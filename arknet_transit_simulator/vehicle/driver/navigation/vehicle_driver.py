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
import asyncio
import socketio
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime

from . import math
from .telemetry_buffer import TelemetryBuffer
from ...base_person import BasePerson
from ....core.states import DriverState

logger = logging.getLogger(__name__)


@dataclass
class DriverConfig:
    """
    Enhanced driver configuration - Now loaded dynamically from ConfigurationService.
    Default values are used as fallbacks if configuration service is unavailable.
    """
    waypoint_proximity_threshold_km: float = 0.05  # 50 meters - proximity to consider waypoint "reached"
    broadcast_interval_seconds: float = 5.0  # How often to broadcast location via Socket.IO
    
    @classmethod
    async def from_config_service(cls, config_service=None):
        """
        Load driver configuration from ConfigurationService with fallback to defaults.
        
        Args:
            config_service: Optional ConfigurationService instance
            
        Returns:
            DriverConfig instance with values from Strapi or defaults
        """
        if config_service is None:
            try:
                from ....services.config_service import get_config_service
                config_service = await get_config_service()
            except Exception as e:
                logger.warning(f"Could not load ConfigurationService, using defaults: {e}")
                return cls()
        
        # Load waypoint settings
        waypoint_proximity_threshold_km = await config_service.get(
            "driver.waypoints.proximity_threshold_km",
            default=0.05
        )
        
        broadcast_interval_seconds = await config_service.get(
            "driver.waypoints.broadcast_interval_seconds",
            default=5.0
        )
        
        logger.info(f"[DriverConfig] Loaded from ConfigurationService:")
        logger.info(f"  • waypoint_proximity_threshold_km: {waypoint_proximity_threshold_km}")
        logger.info(f"  • broadcast_interval_seconds: {broadcast_interval_seconds}")
        
        return cls(
            waypoint_proximity_threshold_km=waypoint_proximity_threshold_km,
            broadcast_interval_seconds=broadcast_interval_seconds
        )


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
        direction: str = "outbound",
        sio_url: str = "http://localhost:1337",
        use_socketio: bool = True,
        config: DriverConfig = None
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
        :param sio_url: Socket.IO server URL (Priority 2)
        :param use_socketio: Enable/disable Socket.IO (Priority 2)
        :param config: DriverConfig instance (optional, uses defaults if not provided)
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
        self.config = config or DriverConfig()  # Use provided config or defaults
        
        # References to vehicle components (to be set when boarding)
        self.vehicle_engine = None
        self.vehicle_gps = None
        
        # Socket.IO configuration (NEW for Priority 2)
        self.use_socketio = use_socketio
        self.sio_url = sio_url
        self.sio_connected = False
        self.location_broadcast_task = None
        if self.use_socketio:
            self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)
            self._setup_socketio_handlers()
        else:
            self.sio = None

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
        
        # Waypoint tracking for passenger checks (Phase 3.2)
        self.visited_waypoints = set()  # Track which route points we've visited
        # Proximity threshold now loaded from config (dynamically from Strapi)
        # self.waypoint_proximity_threshold_km is accessed via self.config.waypoint_proximity_threshold_km

        # Worker
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    async def initialize_config(self, config_service=None):
        """
        Initialize dynamic configuration from ConfigurationService.
        Call this method after constructing the VehicleDriver to load configuration from Strapi.
        
        Args:
            config_service: Optional ConfigurationService instance. If None, will get global instance.
        
        Example:
            driver = VehicleDriver(...)
            await driver.initialize_config()
        """
        try:
            self.config = await DriverConfig.from_config_service(config_service)
            self.logger.info(
                f"[{self.component_name}] Configuration loaded from ConfigurationService:\n"
                f"  • waypoint_proximity_threshold_km: {self.config.waypoint_proximity_threshold_km}\n"
                f"  • broadcast_interval_seconds: {self.config.broadcast_interval_seconds}"
            )
        except Exception as e:
            self.logger.warning(
                f"[{self.component_name}] Could not load config from ConfigurationService, "
                f"using existing config: {e}"
            )
    
    def _setup_socketio_handlers(self) -> None:
        """Set up Socket.IO event handlers (Priority 2)."""
        
        @self.sio.event
        async def connect():
            self.sio_connected = True
            self.logger.info(f"[{self.person_name}] Socket.IO connected to {self.sio_url}")
        
        @self.sio.event
        async def disconnect():
            self.sio_connected = False
            self.logger.warning(f"[{self.person_name}] Socket.IO disconnected")
            
        @self.sio.event
        async def connect_error(data):
            self.logger.error(f"[{self.person_name}] Socket.IO connection error: {data}")
        
        @self.sio.on('conductor:request:stop')
        async def on_stop_request(data):
            """Handle stop request from conductor (Priority 2)."""
            self.logger.info(f"[{self.person_name}] Received stop request: {data}")
            
            # Stop engine if currently driving
            if self.current_state == DriverState.ONBOARD:
                await self.stop_engine()
                
                # Wait for specified duration
                duration = data.get('duration_seconds', 30)
                self.logger.info(f"[{self.person_name}] Stopping for {duration}s for passenger operations")
                await asyncio.sleep(duration)
                
                self.logger.info(f"[{self.person_name}] Stop duration complete, waiting for conductor signal")
        
        @self.sio.on('conductor:ready:depart')
        async def on_ready_to_depart(data):
            """Handle ready-to-depart signal from conductor (Priority 2)."""
            self.logger.info(f"[{self.person_name}] Conductor ready to depart: {data}")
            
            # Restart engine if in WAITING state
            if self.current_state == DriverState.WAITING:
                await self.start_engine()
                self.logger.info(f"[{self.person_name}] Engine restarted, resuming journey")
            
    async def _connect_socketio(self) -> None:
        """Connect to Socket.IO server (Priority 2)."""
        if not self.use_socketio or self.sio_connected:
            return
        
        try:
            await self.sio.connect(self.sio_url)
            self.logger.info(f"[{self.person_name}] Connected to Socket.IO server: {self.sio_url}")
        except Exception as e:
            self.logger.error(f"[{self.person_name}] Socket.IO connection failed: {e}")
            self.logger.info(f"[{self.person_name}] Continuing without Socket.IO")
            self.use_socketio = False
            
    async def _disconnect_socketio(self) -> None:
        """Disconnect from Socket.IO server (Priority 2)."""
        if self.use_socketio and self.sio_connected:
            try:
                await self.sio.disconnect()
                self.logger.info(f"[{self.person_name}] Disconnected from Socket.IO server")
            except Exception as e:
                self.logger.error(f"[{self.person_name}] Error disconnecting Socket.IO: {e}")
    
    async def _broadcast_location_loop(self) -> None:
        """Background task to broadcast location via Socket.IO (Priority 2)."""
        
        while self._running and self.use_socketio:
            try:
                if self.sio_connected and self.current_state == DriverState.ONBOARD:
                    # Get current telemetry
                    telemetry = self.step()
                    
                    if telemetry:
                        lat = telemetry.get('lat', 0)
                        lon = telemetry.get('lon', 0)
                        
                        # Update conductor position if available
                        if hasattr(self, 'conductor') and self.conductor:
                            await self.conductor.update_vehicle_position(lat, lon)
                        
                        location_data = {
                            'vehicle_id': self.vehicle_id,
                            'driver_id': self.component_id,
                            'latitude': lat,
                            'longitude': lon,
                            'speed': telemetry.get('speed', 0),
                            'heading': telemetry.get('bearing', 0),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        await self.sio.emit('driver:location:update', location_data)
                        
                        # Check if we've arrived at a waypoint (Phase 3.2)
                        await self._check_waypoint_arrival(lat, lon)
                
                # Broadcast every 5 seconds
                await asyncio.sleep(5.0)
            
            except Exception as e:
                self.logger.error(f"Location broadcast error: {e}")
                await asyncio.sleep(5.0)  # Continue trying

    async def _start_implementation(self) -> bool:
        """Driver boards vehicle and starts GPS device, but NOT the engine (real operations workflow)."""
        try:
            # Connect to Socket.IO (Priority 2)
            if self.use_socketio:
                await self._connect_socketio()
            
            # Set state to BOARDING while starting components
            self.current_state = DriverState.BOARDING
            self.logger.info(f"Driver {self.person_name} boarding vehicle {self.vehicle_id}")
            
            # Start the navigation worker
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._worker, daemon=True)
                self._thread.start()
            
            # NOTE: In real operations, driver does NOT automatically start engine when boarding
            # Engine will be started later via start_engine() when triggered
            
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
            
            # Set state to WAITING after successful boarding (engine off, waiting for start trigger)
            self.current_state = DriverState.WAITING
            
            # Start location broadcasting (Priority 2)
            if self.use_socketio:
                self.location_broadcast_task = asyncio.create_task(self._broadcast_location_loop())
                self.logger.info(f"[{self.person_name}] Location broadcasting task started")
            
            self.logger.info(
                f"Driver {self.person_name} successfully boarded {self.vehicle_id} - WAITING for engine start "
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
            
            # Stop conductor first (if present)
            if hasattr(self, 'conductor') and self.conductor:
                self.logger.info(f"Driver {self.person_name} dismissing conductor for {self.vehicle_id}")
                try:
                    await self.conductor.stop()
                except Exception as e:
                    self.logger.warning(f"Error stopping conductor: {e}")
            
            # Cancel location broadcasting (Priority 2)
            if self.location_broadcast_task:
                self.location_broadcast_task.cancel()
                try:
                    await self.location_broadcast_task
                except asyncio.CancelledError:
                    pass
                self.logger.info(f"[{self.person_name}] Location broadcasting task stopped")
            
            # Disconnect Socket.IO (Priority 2)
            if self.use_socketio:
                await self._disconnect_socketio()
            
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
    
    async def start_engine(self) -> bool:
        """Start the vehicle engine - transitions driver from WAITING to ONBOARD state."""
        try:
            if self.current_state != DriverState.WAITING:
                self.logger.warning(
                    f"Driver {self.person_name} cannot start engine - not in WAITING state "
                    f"(current state: {self.current_state.value})"
                )
                return False
            
            if self.vehicle_engine:
                self.logger.info(f"Driver {self.person_name} starting engine for {self.vehicle_id}")
                engine_started = await self.vehicle_engine.start()
                if engine_started:
                    # Transition from WAITING to ONBOARD
                    self.current_state = DriverState.ONBOARD
                    self.logger.info(
                        f"✅ Driver {self.person_name} started engine - now ONBOARD and ready to drive"
                    )
                    return True
                else:
                    self.logger.error(f"Failed to start engine for {self.vehicle_id}")
                    return False
            else:
                self.logger.warning(f"No engine available for vehicle {self.vehicle_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Engine start failed for driver {self.person_name}: {e}")
            return False
    
    async def stop_engine(self) -> bool:
        """Stop the vehicle engine - transitions driver from ONBOARD to WAITING state."""
        try:
            if self.current_state != DriverState.ONBOARD:
                self.logger.warning(
                    f"Driver {self.person_name} cannot stop engine - not ONBOARD "
                    f"(current state: {self.current_state.value})"
                )
                return False
            
            if self.vehicle_engine:
                self.logger.info(f"Driver {self.person_name} stopping engine for {self.vehicle_id}")
                engine_stopped = await self.vehicle_engine.stop()
                if engine_stopped:
                    # Transition from ONBOARD to WAITING
                    self.current_state = DriverState.WAITING
                    self.logger.info(
                        f"🛑 Driver {self.person_name} stopped engine - now WAITING"
                    )
                    return True
                else:
                    self.logger.error(f"Failed to stop engine for {self.vehicle_id}")
                    return False
            else:
                self.logger.warning(f"No engine available for vehicle {self.vehicle_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Engine stop failed for driver {self.person_name}: {e}")
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
    
    async def _check_waypoint_arrival(self, current_lat: float, current_lon: float) -> None:
        """
        Check if vehicle has arrived at a route waypoint and emit event for conductor.
        
        This enables Phase 3.2: Driver triggers conductor to check for passengers at stops.
        
        Args:
            current_lat: Current vehicle latitude
            current_lon: Current vehicle longitude
        """
        if not self.use_socketio or not self.sio_connected:
            return
        
        # Check each waypoint in the route
        for waypoint_index, (wp_lon, wp_lat) in enumerate(self.route):
            # Skip if already visited
            if waypoint_index in self.visited_waypoints:
                continue
            
            # Calculate distance to waypoint
            distance_km = math.haversine(current_lat, current_lon, wp_lat, wp_lon)
            
            # If within proximity threshold (from dynamic config), mark as arrived
            if distance_km <= self.config.waypoint_proximity_threshold_km:
                self.visited_waypoints.add(waypoint_index)
                
                # Emit arrival event for conductor
                arrival_data = {
                    'vehicle_id': self.vehicle_id,
                    'driver_id': self.component_id,
                    'waypoint_index': waypoint_index,
                    'latitude': wp_lat,
                    'longitude': wp_lon,
                    'route_id': self.route_name,
                    'timestamp': datetime.now().isoformat()
                }
                
                try:
                    await self.sio.emit('driver:arrived:waypoint', arrival_data)
                    self.logger.info(
                        f"[{self.person_name}] Arrived at waypoint {waypoint_index} "
                        f"({wp_lat:.4f}, {wp_lon:.4f})"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to emit waypoint arrival: {e}")

    def _worker(self):
        while self._running:
            telemetry = self.step()
            if telemetry:
                # Write to internal telemetry buffer
                self.telemetry_buffer.write(telemetry)

                # Propagate to GPS plugin's VehicleState so outbound packets move
                if self.vehicle_gps and hasattr(self.vehicle_gps, 'plugin_manager'):
                    plugin = getattr(self.vehicle_gps.plugin_manager, 'active_plugin', None)
                    # Only update if simulation plugin with vehicle_state object exists
                    if plugin and hasattr(plugin, 'vehicle_state') and plugin.vehicle_state:
                        vs = plugin.vehicle_state
                        try:
                            lat = telemetry.get('lat')
                            lon = telemetry.get('lon')
                            speed = telemetry.get('speed', 0.0)
                            heading = telemetry.get('bearing', 0.0)
                            # VehicleState uses update_position(lat, lon, speed, heading)
                            vs.update_position(lat, lon, speed, heading)
                            # Propagate physics diagnostics if present
                            physics = telemetry.get('physics')
                            if physics:
                                vs.update_physics(
                                    accel=physics.get('accel'),
                                    phase=physics.get('phase'),
                                    progress=physics.get('progress'),
                                    segment_index=physics.get('segment_index')
                                )
                        except Exception as e:
                            self.logger.debug(f"VehicleState update failed: {e}")

                # (Diagnostics removed after validation of movement)
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

        speed_mps = entry.get("cruise_speed_mps", entry.get("cruise_speed", 0.0))
        telemetry = {
            "deviceId": self.component_id,  # Use driver's license as device ID
            "timestamp": entry.get("timestamp", time.time()),
            "lon": lon,
            "lat": lat,
            "bearing": bearing,
            "speed": speed_mps * 3.6,  # Emit km/h externally
            "speed_mps": speed_mps,     # Internal diagnostic (not packetized yet)
            "time": entry.get("time", 0.0),
            "distance": entry.get("distance", 0.0) * 1000.0,  # ✅ km → m
        }

        # If physics diagnostics present, attach for downstream consumers
        if "physics" in entry:
            telemetry["physics"] = entry["physics"]

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

        speed_mps = entry.get("cruise_speed_mps", entry.get("cruise_speed", 0.0))
        telemetry = {
            "deviceId": self.component_id,  # Use driver's license as device ID
            "timestamp": entry.get("timestamp", time.time()),
            "lon": lon,
            "lat": lat,
            "bearing": bearing,
            "speed": speed_mps * 3.6,  # km/h
            "speed_mps": speed_mps,
            "time": entry.get("time", 0.0),
            "distance": entry.get("distance", 0.0) * 1000.0,  # ✅ km → m
        }

        if "physics" in entry:
            telemetry["physics"] = entry["physics"]

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
