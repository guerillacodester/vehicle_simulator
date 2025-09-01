from __future__ import annotations
import threading
from typing import Dict, Any

from .gps_device.device import GPSDevice


def _install_gpsdevice() -> type[GPSDevice]:
    """Hook to swap/validate the GPSDevice class if needed later."""
    return GPSDevice


class Vehicle:
    """
    Thread-safe wrapper around a GPSDevice with simple lifecycle + config.
    """
    def __init__(
        self,
        vehicle_id: str,
        server_url: str,
        token: str,
        config: Dict[str, Any],
        default_interval: float = 1.0,
    ) -> None:
        self.id = vehicle_id
        self._server_url = server_url
        self._token = token
        self._cfg = dict(config)  # shallow copy
        self._lock = threading.RLock()
        self._on = False

        interval = float(self._cfg.get("interval", default_interval))
        method = self._cfg.get("method", "ws")

        GPS = _install_gpsdevice()
        self._gps = GPS(
            self.id,
            self._server_url,
            self._token,
            method=method,
            interval=interval,
        )

    # ---- lifecycle (vehicle-level) ----
    def on(self) -> None:
        with self._lock:
            if not self._on:
                self._gps.on()
                self._on = True

    def off(self) -> None:
        with self._lock:
            if self._on:
                self._gps.off()
                self._on = False

    # ---- lifecycle (explicit GPS control) ----
    def gps_on(self) -> None:
        """Explicitly power on the embedded GPSDevice."""
        with self._lock:
            self._gps.on()
            self._on = True

    def gps_off(self) -> None:
        """Explicitly power off the embedded GPSDevice."""
        with self._lock:
            self._gps.off()
            self._on = False

    def is_on(self) -> bool:
        with self._lock:
            return self._on

    # ---- config ----
    def update_config(self, updates: Dict[str, Any]) -> None:
        with self._lock:
            self._cfg.update(updates)

    def config(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._cfg)

    # ---- cleanup ----
    def cleanup(self) -> None:
        """Ensure GPSDevice is stopped and release references."""
        self.off()
