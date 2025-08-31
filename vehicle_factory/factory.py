# /vehicle_factory/factory.py
from __future__ import annotations
import json
import os
import threading
import concurrent.futures
from typing import Dict, Any, Optional, List, Tuple

from vehicle import Vehicle


class VehicleFactory:
    """
    Thread-safe factory managing a registry of Vehicle instances and their manifest.
    Responsibilities:
      - Load/save vehicles.json (manifest)
      - CRUD by vehicle_id
      - open(): instantiate all, optionally start those with active==True
      - close(): stop and destroy all
      - start()/stop() individual vehicles

    Concurrency:
      - Internal RLock guards manifest/registry.
      - Spawns/starts executed via ThreadPoolExecutor to avoid blocking.
    """

    def __init__(
        self,
        manifest_path: str = "vehicles.json",
        server_url: str = "",
        token: str = "",
        default_interval: float = 1.0,
        autosave: bool = True,
        start_active: bool = True,
        max_workers: int = 8,
    ) -> None:
        self._manifest_path = manifest_path
        self._server_url = server_url
        self._token = token
        self._default_interval = float(default_interval)
        self._autosave = bool(autosave)
        self._start_active = bool(start_active)
        self._max_workers = max_workers

        self._lock = threading.RLock()
        self._manifest: Dict[str, Dict[str, Any]] = {}
        self._registry: Dict[str, Vehicle] = {}
        self._opened = False

    # ---------- manifest I/O ----------
    def _load_manifest(self) -> None:
        with self._lock:
            if not os.path.exists(self._manifest_path):
                self._manifest = {}
                return
            with open(self._manifest_path, "r", encoding="utf-8") as f:
                self._manifest = json.load(f)

    def _save_manifest(self) -> None:
        if not self._autosave:
            return
        with self._lock:
            tmp = self._manifest_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._manifest, f, indent=2, sort_keys=True)
            os.replace(tmp, self._manifest_path)

    # ---------- lifecycle ----------
    def open(self) -> None:
        """
        Create Vehicle instances for all entries in manifest.
        If start_active=True, start those with config['active'] == True.
        Spawns concurrently.
        """
        with self._lock:
            if self._opened:
                return
            self._load_manifest()
            items: List[Tuple[str, Dict[str, Any]]] = list(self._manifest.items())

        if not items:
            with self._lock:
                self._opened = True
            return

        def _spawn(vid: str, cfg: Dict[str, Any]) -> None:
            v = Vehicle(
                vehicle_id=vid,
                server_url=self._server_url,
                token=self._token,
                config=cfg,
                default_interval=self._default_interval,
            )
            with self._lock:
                self._registry[vid] = v
            if self._start_active and cfg.get("active", False):
                v.on()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as ex:
            futs = [ex.submit(_spawn, vid, dict(cfg)) for vid, cfg in items]
            for f in futs:
                f.result()  # surface exceptions

        with self._lock:
            self._opened = True

    def close(self) -> None:
        """Stop and destroy all vehicle instances."""
        with self._lock:
            pairs = list(self._registry.items())
            self._registry.clear()
            self._opened = False
        for _, v in pairs:
            try:
                v.cleanup()
            except Exception:
                pass

    # ---------- CRUD ----------
    def create(self, vehicle_id: str, config: Dict[str, Any]) -> Vehicle:
        with self._lock:
            if vehicle_id in self._manifest:
                raise ValueError(f"Vehicle '{vehicle_id}' already exists")
            cfg = dict(config)
            cfg.setdefault("active", False)
            self._manifest[vehicle_id] = cfg
            self._save_manifest()

        v = Vehicle(
            vehicle_id=vehicle_id,
            server_url=self._server_url,
            token=self._token,
            config=cfg,
            default_interval=self._default_interval,
        )
        with self._lock:
            self._registry[vehicle_id] = v
        return v

    def read(self, vehicle_id: str) -> Dict[str, Any]:
        with self._lock:
            cfg = self._manifest.get(vehicle_id)
            if cfg is None:
                raise KeyError(vehicle_id)
            return dict(cfg)

    def update(self, vehicle_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if vehicle_id not in self._manifest:
                raise KeyError(vehicle_id)
            self._manifest[vehicle_id].update(updates)
            new_cfg = dict(self._manifest[vehicle_id])
            v = self._registry.get(vehicle_id)

        if v:
            v.update_config(updates)
            if "active" in updates:
                if bool(updates["active"]):
                    self.start(vehicle_id)
                else:
                    self.stop(vehicle_id)

        self._save_manifest()
        return new_cfg

    def delete(self, vehicle_id: str) -> None:
        v: Optional[Vehicle] = None
        with self._lock:
            if vehicle_id not in self._manifest:
                raise KeyError(vehicle_id)
            self._manifest.pop(vehicle_id, None)
            v = self._registry.pop(vehicle_id, None)
            self._save_manifest()
        if v:
            v.cleanup()

    # ---------- control & info ----------
    def start(self, vehicle_id: str) -> None:
        with self._lock:
            v = self._registry.get(vehicle_id)
            if not v:
                raise KeyError(vehicle_id)
        v.on()

    def stop(self, vehicle_id: str) -> None:
        with self._lock:
            v = self._registry.get(vehicle_id)
            if not v:
                raise KeyError(vehicle_id)
        v.off()

    def list_ids(self) -> List[str]:
        with self._lock:
            return list(self._manifest.keys())

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                vid: {
                    "active": bool(cfg.get("active", False)),
                    "running": bool(self._registry.get(vid).is_on() if vid in self._registry else False),
                }
                for vid, cfg in self._manifest.items()
            }
