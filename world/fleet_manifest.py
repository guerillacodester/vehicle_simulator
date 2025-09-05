# fleet_manifest.py
from __future__ import annotations
import json, os, threading
from typing import Dict, Any, Optional

class FleetManifest:
    """
    Thread-safe data layer for vehicles.json
    - Load/save manifest
    - CRUD entries (data only)
    - Choose one vehicle (default → active → first)
    """

    def __init__(self, manifest_path: str) -> None:
        self._path = manifest_path
        self._lock = threading.RLock()
        self._data: Dict[str, Dict[str, Any]] = {}
        self.load()

    # ---------- core I/O ----------
    def load(self) -> None:
        with self._lock:
            if not os.path.exists(self._path):
                self._data = {}
                return
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def save(self) -> None:
        with self._lock:
            tmp = self._path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, sort_keys=True)
            os.replace(tmp, self._path)

    # ---------- queries ----------
    def all(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._data)

    def get(self, vid: str) -> Dict[str, Any]:
        with self._lock:
            if vid not in self._data:
                raise KeyError(vid)
            return dict(self._data[vid])

    def choose_one(self) -> Optional[Dict[str, Any]]:
        """Choose one vehicle: prefer 'default', else 'active', else first in dict."""
        with self._lock:
            if not self._data:
                return None
            if "default" in self._data:
                return {"id": "default", **self._data["default"]}
            active = [ (vid,cfg) for vid,cfg in self._data.items() if cfg.get("active") ]
            if active:
                vid, cfg = active[0]
                return {"id": vid, **cfg}
            vid, cfg = next(iter(self._data.items()))
            return {"id": vid, **cfg}

    # ---------- CRUD ----------
    def create(self, vid: str, cfg: Dict[str, Any]) -> None:
        with self._lock:
            if vid in self._data:
                raise ValueError(f"{vid} already exists")
            self._data[vid] = dict(cfg)
            self.save()

    def update(self, vid: str, updates: Dict[str, Any]) -> None:
        with self._lock:
            if vid not in self._data:
                raise KeyError(vid)
            self._data[vid].update(updates)
            self.save()

    def delete(self, vid: str) -> None:
        with self._lock:
            if vid not in self._data:
                raise KeyError(vid)
            self._data.pop(vid)
            self.save()
