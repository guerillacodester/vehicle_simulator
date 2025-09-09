#!/usr/bin/env python3
"""
Navigator
---------
Maps engine-produced cumulative distance onto a route polyline and produces
interpolated GPS positions that lie on that polyline. Results are written to
a TelemetryBuffer (separate from RxTx/GPS buffers).
"""

import time
import threading
from typing import List, Tuple, Optional

from world.vehicle_simulator.utils.routes.route_loader import load_route_coordinates
from . import math
from .telemetry_buffer import TelemetryBuffer
from .route_topology import build_ordered_path

# Decoupled route provider imports
from world.vehicle_simulator.interfaces.route_provider import IRouteProvider
try:
    from world.vehicle_simulator.providers.database_route_provider import DatabaseRouteProvider
except ImportError:
    DatabaseRouteProvider = None
from world.vehicle_simulator.providers.file_route_provider import FileRouteProvider


class Navigator:
    def __init__(
        self,
        vehicle_id: str,
        route_file: Optional[str] = None,
        route: Optional[str] = None,   # route short_name from DB
        engine_buffer=None,
        tick_time: float = 0.1,
        mode: str = "geodesic",
        direction: str = "outbound",   # "outbound" = default, "inbound" = reversed
        route_provider: Optional[IRouteProvider] = None,  # Injectable route provider
    ):
        """
        :param vehicle_id: vehicle ID string
        :param route_file: path to GeoJSON route file (legacy mode)
        :param route: route short_name in DB (preferred mode)
        :param engine_buffer: EngineBuffer instance for this vehicle
        :param tick_time: worker loop sleep time (s)
        :param mode: "linear" (legacy) or "geodesic" (default)
        :param direction: "outbound" (default) or "inbound" (reverse route)
        :param route_provider: Injectable route provider (auto-detected if None)
        """
        self.vehicle_id = vehicle_id
        self.route_file = route_file
        self.engine_buffer = engine_buffer
        self.telemetry_buffer = TelemetryBuffer()
        self.tick_time = tick_time
        self.mode = mode
        self.direction = direction

        # Auto-detect or use provided route provider
        if route_provider is None:
            route_provider = self._get_default_route_provider(route, route_file)

        if route:  # DB-backed route
            self.route: List[Tuple[float, float]] = route_provider.get_route_coordinates(route)
        elif route_file:  # fallback to file
            self.route: List[Tuple[float, float]] = build_ordered_path(
                route_file, direction=direction
            )
        else:
            raise ValueError("Navigator requires either a route short_name (DB) or a route_file")

        # Precompute segment lengths (km)
        self.segment_lengths: List[float] = []
        self.total_route_length = 0.0
        for i in range(len(self.route) - 1):
            lon1, lat1 = self.route[i]
            lon2, lat2 = self.route[i + 1]
            seg_len = math.haversine(lat1, lon1, lat2, lon2)  # km
            self.segment_lengths.append(seg_len)
            self.total_route_length += seg_len

        # State
        self.current_segment = 0
        self.distance_into_segment = 0.0
        self.last_position: Optional[Tuple[float, float]] = None

        # Worker
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _get_default_route_provider(self, route: Optional[str], route_file: Optional[str]) -> object:
        """
        Returns the default route provider based on whether a database route or file route is requested.
        """
        if route:  # Database route requested
            if DatabaseRouteProvider is not None:
                try:
                    return DatabaseRouteProvider()
                except (RuntimeError, Exception):
                    # Fleet manager not available, fall back to file provider
                    import logging
                    logging.warning("Fleet manager not available, falling back to file-based routes")
                    return FileRouteProvider()
            else:
                import logging
                logging.warning("DatabaseRouteProvider not available, falling back to file-based routes")
                return FileRouteProvider()
        else:  # File route requested or fallback
            return FileRouteProvider()

    def on(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
            print(
                f"[INFO] Navigator for {self.vehicle_id} turned ON "
                f"(mode={self.mode}, direction={self.direction})"
            )

    def off(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print(f"[INFO] Navigator for {self.vehicle_id} turned OFF")

    def _worker(self):
        while self._running:
            telemetry = self.step()
            if telemetry:
                self.telemetry_buffer.write(telemetry)
            time.sleep(self.tick_time)

    # Linear interpolation
    def _step_linear(self) -> Optional[dict]:
        entry = self.engine_buffer.read()
        if not entry:
            return None

        distance = entry.get("distance", 0.0)
        remaining = distance
        seg_index = 0
        for i, seg_len in enumerate(self.segment_lengths):
            if remaining <= seg_len:
                seg_index = i
                self.current_segment = i
                self.distance_into_segment = remaining
                break
            remaining -= seg_len
        else:
            seg_index = len(self.segment_lengths) - 1
            self.current_segment = seg_index
            self.distance_into_segment = self.segment_lengths[seg_index]

        lon1, lat1 = self.route[seg_index]
        lon2, lat2 = self.route[seg_index + 1]
        seg_len = self.segment_lengths[seg_index]
        fraction = (self.distance_into_segment / seg_len) if seg_len > 0 else 0.0

        lon = lon1 + (lon2 - lon1) * fraction
        lat = lat1 + (lat2 - lat1) * fraction
        bearing = math.bearing(lat1, lon1, lat2, lon2)

        telemetry = {
            "deviceId": self.vehicle_id,
            "timestamp": entry.get("timestamp", time.time()),
            "lon": lon,
            "lat": lat,
            "bearing": bearing,
            "speed": entry.get("cruise_speed", 0.0),
            "time": entry.get("time", 0.0),
            "distance": entry.get("distance", 0.0) * 1000.0,  # ✅ km → m
        }

        self.last_position = (lon, lat)
        return telemetry

    # Geodesic interpolation
    def _step_geodesic(self) -> Optional[dict]:
        entry = self.engine_buffer.read()
        if not entry:
            return None

        distance_km = entry.get("distance", 0.0)
        route_latlon = [(lat, lon) for lon, lat in self.route]
        lat, lon, bearing = math.interpolate_along_route_geodesic(
            route_latlon, distance_km
        )

        telemetry = {
            "deviceId": self.vehicle_id,
            "timestamp": entry.get("timestamp", time.time()),
            "lon": lon,
            "lat": lat,
            "bearing": bearing,
            "speed": entry.get("cruise_speed", 0.0),
            "time": entry.get("time", 0.0),
            "distance": entry.get("distance", 0.0) * 1000.0,  # ✅ km → m
        }

        self.last_position = (lon, lat)
        return telemetry

    def step(self) -> Optional[dict]:
        if self.mode == "geodesic":
            # DEBUG: Show which interpolation method is being used
            # print(f"[DEBUG] {self.vehicle_id}: Using GEODESIC interpolation")
            return self._step_geodesic()
        else:
            # DEBUG: Show which interpolation method is being used  
            # print(f"[DEBUG] {self.vehicle_id}: Using LINEAR interpolation")
            return self._step_linear()
