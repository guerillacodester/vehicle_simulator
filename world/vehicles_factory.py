from __future__ import annotations
import threading, concurrent.futures
from typing import Dict, Any, List, Optional

# your existing Vehicle wrapper
from .fleet_manifest import FleetManifest
from .vehicle.vahicle_object import Vehicle


class VehiclesFactory:
    """
    Runtime orchestration layer.
    Uses FleetManifest as the source of truth for vehicle configs.
    """

    def __init__(
        self,
        manifest: FleetManifest,
        server_url: str,
        token: str,
        default_interval: float = 1.0,
        start_active: bool = True,
        max_workers: int = 8,
    ) -> None:
        self._manifest = manifest
        self._server_url = server_url
        self._token = token
        self._default_interval = default_interval
        self._start_active = start_active
        self._max_workers = max_workers

        self._lock = threading.RLock()
        self._registry: Dict[str, Vehicle] = {}
        self._opened = False

    # ---------- lifecycle ----------
    def open(self) -> None:
        with self._lock:
            if self._opened:
                return
            items = list(self._manifest.all().items())

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

            # ✅ Step 1: only start if manifest says active
            if self._start_active and cfg.get("active", False):
                v.on()
            else:
                # optional: log inactive skip
                print(f"[INFO] Vehicle {vid} inactive.")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as ex:
            futs = [ex.submit(_spawn, vid, dict(cfg)) for vid, cfg in items]
            for f in futs:
                f.result()

        with self._lock:
            self._opened = True

    # AFTER (deterministic shutdown)
    def close(self) -> None:
        with self._lock:
            vehicles = list(self._registry.values())
            self._opened = False
            self._registry.clear()

        for v in vehicles:
            try:
                v.cleanup()  # cleanup() should call off()
            except Exception:
                pass

    # ---------- runtime CRUD ----------
    def start(self, vid: str) -> None:
        with self._lock:
            v = self._registry.get(vid)
            if not v:
                raise KeyError(vid)
        v.on()

    def stop(self, vid: str) -> None:
        with self._lock:
            v = self._registry.get(vid)
            if not v:
                raise KeyError(vid)
        v.off()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                vid: {
                    "active": self._manifest.get(vid).get("active", False),
                    "running": v.is_on() if v else False,
                }
                for vid, v in self._registry.items()
            }
