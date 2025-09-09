#!/usr/bin/env python3
"""
Navigator
---------
Maps engine-produced cumulative distance onto a route polyline and produces
interpolated GPS positions that lie on that polyline. Results are written to
a TelemetryBuffer (separate from RxTx/GPS buffers).

Navigator is a pure data consumer - it accepts route coordinates directly
and does not load from files or databases on its own.
"""

import time
import threading
from typing import List, Tuple, Optional

from . import math
from .telemetry_buffer import TelemetryBuffer


class Navigator:
    def __init__(
        self,
        vehicle_id: str,
        route_coordinates: List[Tuple[float, float]],
        engine_buffer=None,
        tick_time: float = 0.1,
        mode: str = "geodesic",
        direction: str = "outbound"
    ):
        """
        Navigator that accepts route coordinates directly.
        
        :param vehicle_id: vehicle ID string
        :param route_coordinates: List of (longitude, latitude) coordinate pairs
        :param engine_buffer: EngineBuffer instance for this vehicle
        :param tick_time: worker loop sleep time (s)
        :param mode: "linear" (legacy) or "geodesic" (default)
        :param direction: "outbound" (default) or "inbound" (reverse route)
        """
        if not route_coordinates:
            raise ValueError("Navigator requires route coordinates")
        
        self.vehicle_id = vehicle_id
        self.engine_buffer = engine_buffer
        self.telemetry_buffer = TelemetryBuffer()
        self.tick_time = tick_time
        self.mode = mode
        self.direction = direction

        # Set route coordinates (reverse if inbound direction)
        if direction == "inbound":
            self.route: List[Tuple[float, float]] = list(reversed(route_coordinates))
        else:
            self.route: List[Tuple[float, float]] = route_coordinates

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
