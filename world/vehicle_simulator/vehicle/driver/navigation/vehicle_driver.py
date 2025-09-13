#!/usr/bin/env python3
"""
VehicleDriver
-------------
Maps engine-produced cumulative distance onto a route polyline and produces
interpolated GPS positions that lie on that polyline. Results are written to
a TelemetryBuffer (separate from RxTx/GPS buffers).

VehicleDriver manages the boarding process and controls vehicle components:
- Boards vehicle (DriverState: DISEMBARKED → BOARDING → ONBOARD)
- Turns on Engine and GPS Device when boarding
- Turns off components when disembarking

VehicleDriver is a pure data consumer - it accepts route coordinates directly
and does not load from files or databases on its own.
"""

import time
import threading
from typing import List, Tuple, Optional

from . import math
from .telemetry_buffer import TelemetryBuffer
from ...base_person import BasePerson
from ....core.states import DriverState


class VehicleDriver(BasePerson):
    def __init__(
        self,
        driver_id: str,
        driver_name: str,
        vehicle_id: str,
        route_coordinates: List[Tuple[float, float]],
        route_name: str = "",
        engine_buffer=None,
        tick_time: float = 0.1,
        mode: str = "geodesic",
        direction: str = "outbound"
    ):
        """
        VehicleDriver that accepts route coordinates directly.
        
        :param driver_id: Driver ID string (e.g., "DRV001")
        :param driver_name: Driver's human-readable name
        :param vehicle_id: vehicle ID string that driver will operate
        :param route_coordinates: List of (longitude, latitude) coordinate pairs
        :param route_name: Route identifier (e.g., "1A")
        :param engine_buffer: EngineBuffer instance for this vehicle
        :param tick_time: worker loop sleep time (s)
        :param mode: "linear" (legacy) or "geodesic" (default)
        :param direction: "outbound" (default) or "inbound" (reverse route)
        """
        # Initialize BasePerson with PersonState, then override with DriverState
        super().__init__(driver_id, "VehicleDriver", driver_name)
        # Override initial state to use DriverState.DISEMBARKED
        self.current_state = DriverState.DISEMBARKED
        
        if not route_coordinates:
            raise ValueError("VehicleDriver requires route coordinates")
        
        self.vehicle_id = vehicle_id
        self.route_name = route_name
        self.engine_buffer = engine_buffer
        self.telemetry_buffer = TelemetryBuffer()
        self.tick_time = tick_time
        self.mode = mode
        self.direction = direction
        
        # References to vehicle components (to be set when boarding)
        self.vehicle_engine = None
        self.vehicle_gps = None

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

    async def _start_implementation(self) -> bool:
        """Driver boards vehicle and starts vehicle components."""
        try:
            # Set state to BOARDING while starting components
            self.current_state = DriverState.BOARDING
            self.logger.info(f"Driver {self.person_name} boarding vehicle {self.vehicle_id}")
            
            # Start the navigation worker
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._worker, daemon=True)
                self._thread.start()
            
            # Turn on vehicle components if available
            if self.vehicle_engine:
                self.logger.info(f"Driver {self.person_name} starting engine for {self.vehicle_id}")
                await self.vehicle_engine.start()
            
            if self.vehicle_gps:
                self.logger.info(f"Driver {self.person_name} starting GPS device for {self.vehicle_id}")
                await self.vehicle_gps.start()
                
                # Set initial position and transmit first GPS packet
                if self.route:
                    initial_coord = self.route[0]  # [longitude, latitude]
                    lat, lon = initial_coord[1], initial_coord[0]
                    
                    # Create production VehicleState with initial position
                    from ..vehicle_state import VehicleState
                    initial_state = VehicleState(
                        driver_id=self.component_id,
                        driver_name=self.person_name,
                        vehicle_id=self.vehicle_id,
                        route_name=self.route_name
                    )
                    
                    # Set the initial position (first coordinate of route)
                    initial_state.set_position(lat, lon)
                    
                    # Set vehicle state in GPS plugin
                    self.vehicle_gps.set_vehicle_state(initial_state)
                    
                    self.logger.info(f"📍 Initial GPS position set: lat={lat:.6f}, lon={lon:.6f}")
                    self.logger.info("📡 Initial position packet transmitted to GPS server")
            
            # Set state to ONBOARD after successful boarding
            self.current_state = DriverState.ONBOARD
            self.logger.info(
                f"Driver {self.person_name} successfully boarded {self.vehicle_id} "
                f"(mode={self.mode}, direction={self.direction})"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Driver {self.person_name} failed to board vehicle {self.vehicle_id}: {e}")
            return False

    async def _stop_implementation(self) -> bool:
        """Driver disembarks vehicle and stops vehicle components."""
        try:
            # Set state to DISEMBARKING while stopping components
            self.current_state = DriverState.DISEMBARKING
            self.logger.info(f"Driver {self.person_name} disembarking from vehicle {self.vehicle_id}")
            
            # Turn off vehicle components if available
            if self.vehicle_gps:
                self.logger.info(f"Driver {self.person_name} stopping GPS device for {self.vehicle_id}")
                await self.vehicle_gps.stop()
            
            if self.vehicle_engine:
                self.logger.info(f"Driver {self.person_name} stopping engine for {self.vehicle_id}")
                await self.vehicle_engine.stop()
            
            # Stop the navigation worker
            self._running = False
            if self._thread:
                self._thread.join(timeout=2)
                if self._thread.is_alive():
                    self.logger.warning(f"Navigation thread for {self.person_name} did not stop cleanly")
            
            # Set state to DISEMBARKED after successful disembarking
            self.current_state = DriverState.DISEMBARKED
            self.logger.info(f"Driver {self.person_name} successfully disembarked from {self.vehicle_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Driver {self.person_name} failed to disembark from vehicle {self.vehicle_id}: {e}")
            return False
    
    def set_vehicle_components(self, engine=None, gps_device=None):
        """Set references to vehicle components that the driver will control."""
        self.vehicle_engine = engine
        self.vehicle_gps = gps_device
        self.logger.info(f"Driver {self.person_name} assigned to control vehicle {self.vehicle_id} components")
    
    # Legacy compatibility methods
    def on(self):
        """Legacy method - driver boards vehicle (sync version)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = loop.create_task(self.start())
                return True
            else:
                return loop.run_until_complete(self.start())
        except RuntimeError:
            return asyncio.run(self.start())

    def off(self):
        """Legacy method - driver disembarks vehicle (sync version)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = loop.create_task(self.stop())
                return True
            else:
                return loop.run_until_complete(self.stop())
        except RuntimeError:
            return asyncio.run(self.stop())

    def _worker(self):
        while self._running:
            telemetry = self.step()
            if telemetry:
                self.telemetry_buffer.write(telemetry)
            time.sleep(self.tick_time)

    # Linear interpolation
    def _step_linear(self) -> Optional[dict]:
        # Handle case where engine is OFF (no engine buffer)
        if self.engine_buffer is None:
            # Engine is off - return static position at route start with speed=0
            if not self.route:
                return None
            
            # Get first coordinate from route (vehicle parked at route start)
            lon, lat = self.route[0]
            
            return {
                "deviceId": self.component_id,
                "timestamp": time.time(),
                "lon": lon,
                "lat": lat,
                "bearing": 0.0,  # Stationary
                "speed": 0.0,    # Engine off, no movement
                "time": 0.0,     # No engine time
                "distance": 0.0  # No distance traveled
            }
        
        # Engine is running - read from engine buffer
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
            "deviceId": self.component_id,  # Use driver's license as device ID
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
        # Handle case where engine is OFF (no engine buffer)
        if self.engine_buffer is None:
            # Engine is off - return static position at route start with speed=0
            if not self.route:
                return None
            
            # Get first coordinate from route (vehicle parked at route start)
            lon, lat = self.route[0]
            
            return {
                "deviceId": self.component_id,
                "timestamp": time.time(),
                "lon": lon,
                "lat": lat,
                "bearing": 0.0,  # Stationary
                "speed": 0.0,    # Engine off, no movement
                "time": 0.0,     # No engine time
                "distance": 0.0  # No distance traveled
            }
        
        # Engine is running - read from engine buffer
        entry = self.engine_buffer.read()
        if not entry:
            return None

        distance_km = entry.get("distance", 0.0)
        route_latlon = [(lat, lon) for lon, lat in self.route]
        lat, lon, bearing = math.interpolate_along_route_geodesic(
            route_latlon, distance_km
        )

        telemetry = {
            "deviceId": self.component_id,  # Use driver's license as device ID
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
