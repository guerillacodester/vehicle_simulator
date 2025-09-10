"""
Enhanced Navigator with Operational Cycle Support
-------------------------------------------------
Extended Navigator that supports complete ZR van operational cycle:
- Engine control (on/off states)
- Route execution with passenger stops
- Destination loitering
- Return journey management
- Depot return and cycle completion
"""

import time
import threading
import logging
from typing import List, Tuple, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum

from . import math
from .telemetry_buffer import TelemetryBuffer

logger = logging.getLogger(__name__)


class NavigationState(Enum):
    """Navigation states during operational cycle"""
    IDLE = "idle"                    # Engine off, at depot
    ENGINE_STARTING = "engine_starting"  # Engine turning on
    DEPARTING = "departing"          # Leaving depot
    EN_ROUTE = "en_route"           # Following route to destination
    AT_STOP = "at_stop"             # At passenger stop
    AT_DESTINATION = "at_destination"  # At final destination
    LOITERING = "loitering"         # Waiting at destination
    RETURNING = "returning"         # Return journey
    APPROACHING_DEPOT = "approaching_depot"  # Near depot
    ENGINE_STOPPING = "engine_stopping"  # Engine turning off


class EnhancedNavigator:
    """
    Enhanced Navigator supporting complete ZR van operational cycle.
    Manages route execution, passenger stops, engine control, and journey tracking.
    """
    
    def __init__(
        self,
        vehicle_id: str,
        engine_buffer=None,
        tick_time: float = 0.1,
        mode: str = "geodesic"
    ):
        """
        Initialize Enhanced Navigator.
        
        Args:
            vehicle_id: Vehicle identifier
            engine_buffer: Engine buffer for distance data
            tick_time: Navigation update interval
            mode: Navigation mode (geodesic or linear)
        """
        self.vehicle_id = vehicle_id
        self.engine_buffer = engine_buffer
        self.telemetry_buffer = TelemetryBuffer()
        self.tick_time = tick_time
        self.mode = mode
        
        # Route and journey data
        self.route_data: Optional[Dict[str, Any]] = None
        self.outbound_route: List[Tuple[float, float]] = []
        self.return_route: List[Tuple[float, float]] = []
        self.current_route: List[Tuple[float, float]] = []
        self.passenger_stops: List[Dict[str, Any]] = []
        
        # Navigation state
        self.state = NavigationState.IDLE
        self.engine_on = False
        self.current_segment = 0
        self.distance_into_segment = 0.0
        self.last_position: Optional[Tuple[float, float]] = None
        
        # Journey tracking
        self.journey_start_time: Optional[datetime] = None
        self.destination_arrival_time: Optional[datetime] = None
        self.loiter_duration = timedelta(minutes=5)  # 5 minutes at destination
        self.passengers_on_board = 0
        
        # Route calculations
        self.segment_lengths: List[float] = []
        self.total_route_length = 0.0
        
        # Worker thread
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.state_change_callbacks: List[Callable] = []
        self.journey_complete_callback: Optional[Callable] = None
        
    def register_state_change_callback(self, callback: Callable):
        """Register callback for navigation state changes"""
        self.state_change_callbacks.append(callback)
        
    def register_journey_complete_callback(self, callback: Callable):
        """Register callback for journey completion"""
        self.journey_complete_callback = callback
    
    def load_route(self, route_data: Dict[str, Any]) -> bool:
        """
        Load route data and prepare for journey.
        
        Args:
            route_data: Complete route information from fleet manager
            
        Returns:
            bool: Success of route loading
        """
        try:
            self.route_data = route_data
            
            # Extract route coordinates
            coordinates = route_data.get('coordinates', [])
            if not coordinates:
                logger.error(f"🗺️ No coordinates in route data for {self.vehicle_id}")
                return False
                
            # Set outbound and return routes
            self.outbound_route = [(lon, lat) for lon, lat in coordinates]
            self.return_route = list(reversed(self.outbound_route))
            
            # Extract passenger stops
            self.passenger_stops = route_data.get('stops', [])
            
            logger.info(f"🗺️ Route loaded for {self.vehicle_id}: {route_data.get('route_name', 'Unknown Route')}")
            logger.info(f"🗺️ Route length: {len(self.outbound_route)} points, {len(self.passenger_stops)} stops")
            
            return True
            
        except Exception as e:
            logger.error(f"🗺️ Failed to load route for {self.vehicle_id}: {e}")
            return False
    
    def start_engine(self) -> bool:
        """Start vehicle engine and begin journey"""
        if self.state != NavigationState.IDLE:
            logger.warning(f"🚗 Cannot start engine - vehicle {self.vehicle_id} not in IDLE state")
            return False
            
        if not self.route_data:
            logger.error(f"🚗 Cannot start engine - no route loaded for {self.vehicle_id}")
            return False
            
        self.engine_on = True
        self.journey_start_time = datetime.now()
        self._change_state(NavigationState.ENGINE_STARTING)
        
        # Prepare outbound route
        self._prepare_route(self.outbound_route)
        
        # Start navigation worker
        self.on()
        
        logger.info(f"🚗 ✅ Engine started for {self.vehicle_id} - beginning journey")
        return True
    
    def stop_engine(self) -> bool:
        """Stop vehicle engine and complete journey"""
        if not self.engine_on:
            return True
            
        self.engine_on = False
        self._change_state(NavigationState.ENGINE_STOPPING)
        
        # Stop navigation worker
        self.off()
        
        # Complete journey
        if self.journey_complete_callback:
            journey_data = {
                'route_id': self.route_data.get('route_id') if self.route_data else None,
                'journey_start_time': self.journey_start_time.isoformat() if self.journey_start_time else None,
                'journey_end_time': datetime.now().isoformat(),
                'total_passengers_transported': self.passengers_on_board
            }
            self.journey_complete_callback(self.vehicle_id, journey_data)
        
        # Reset state
        self._reset_journey_state()
        
        logger.info(f"🚗 ⏹️ Engine stopped for {self.vehicle_id} - journey completed")
        return True
    
    def _prepare_route(self, route_coordinates: List[Tuple[float, float]]):
        """Prepare route for navigation"""
        self.current_route = route_coordinates
        self.current_segment = 0
        self.distance_into_segment = 0.0
        
        # Calculate segment lengths
        self.segment_lengths = []
        self.total_route_length = 0.0
        
        for i in range(len(self.current_route) - 1):
            lon1, lat1 = self.current_route[i]
            lon2, lat2 = self.current_route[i + 1]
            seg_len = math.haversine(lat1, lon1, lat2, lon2)  # km
            self.segment_lengths.append(seg_len)
            self.total_route_length += seg_len
    
    def _change_state(self, new_state: NavigationState):
        """Change navigation state and notify callbacks"""
        old_state = self.state
        self.state = new_state
        
        logger.info(f"🔄 {self.vehicle_id} navigation: {old_state.value} → {new_state.value}")
        
        # Notify callbacks
        for callback in self.state_change_callbacks:
            try:
                callback(self.vehicle_id, old_state, new_state)
            except Exception as e:
                logger.error(f"🔄 State change callback error: {e}")
    
    def _reset_journey_state(self):
        """Reset journey state after completion"""
        self.state = NavigationState.IDLE
        self.route_data = None
        self.outbound_route = []
        self.return_route = []
        self.current_route = []
        self.passenger_stops = []
        self.current_segment = 0
        self.distance_into_segment = 0.0
        self.last_position = None
        self.journey_start_time = None
        self.destination_arrival_time = None
        self.passengers_on_board = 0
    
    def on(self):
        """Start navigation worker thread"""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
            logger.info(f"🗺️ Navigation started for {self.vehicle_id}")

    def off(self):
        """Stop navigation worker thread"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info(f"🗺️ Navigation stopped for {self.vehicle_id}")

    def _worker(self):
        """Main navigation worker loop"""
        while self._running and self.engine_on:
            try:
                self._update_navigation()
                time.sleep(self.tick_time)
            except Exception as e:
                logger.error(f"🗺️ Navigation worker error for {self.vehicle_id}: {e}")
                break
    
    def _update_navigation(self):
        """Update navigation based on current state"""
        if self.state == NavigationState.ENGINE_STARTING:
            # Transition to departing after brief delay
            time.sleep(1)
            self._change_state(NavigationState.DEPARTING)
            
        elif self.state == NavigationState.DEPARTING:
            # Begin route following
            self._change_state(NavigationState.EN_ROUTE)
            
        elif self.state == NavigationState.EN_ROUTE:
            # Follow current route
            telemetry = self._step_navigation()
            if telemetry:
                self.telemetry_buffer.write(telemetry)
                
            # Check if reached destination
            if self._is_route_complete():
                if self.current_route == self.outbound_route:
                    # Reached destination
                    self.destination_arrival_time = datetime.now()
                    self._change_state(NavigationState.AT_DESTINATION)
                else:
                    # Returned to depot
                    self._change_state(NavigationState.APPROACHING_DEPOT)
                    
        elif self.state == NavigationState.AT_DESTINATION:
            # Start loitering period
            self._change_state(NavigationState.LOITERING)
            
        elif self.state == NavigationState.LOITERING:
            # Wait at destination
            if self.destination_arrival_time:
                elapsed = datetime.now() - self.destination_arrival_time
                if elapsed >= self.loiter_duration:
                    # Start return journey
                    self._prepare_route(self.return_route)
                    self._change_state(NavigationState.RETURNING)
                    
        elif self.state == NavigationState.RETURNING:
            # Follow return route
            telemetry = self._step_navigation()
            if telemetry:
                self.telemetry_buffer.write(telemetry)
                
            # Check if back at depot
            if self._is_route_complete():
                self._change_state(NavigationState.APPROACHING_DEPOT)
                
        elif self.state == NavigationState.APPROACHING_DEPOT:
            # Stop engine and complete journey
            self.stop_engine()
    
    def _step_navigation(self) -> Optional[Dict[str, Any]]:
        """Perform navigation step and return telemetry"""
        if not self.engine_buffer or not self.current_route:
            return None
            
        try:
            # Get latest engine data
            entry = self.engine_buffer.read_latest()
            if not entry:
                return None
                
            # Calculate position using geodesic interpolation
            distance_km = entry.get("distance", 0.0)
            
            # Convert route for math functions
            route_latlon = [(lat, lon) for lon, lat in self.current_route]
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
                "distance": entry.get("distance", 0.0) * 1000.0,  # km → m
                "state": self.state.value,
                "passengers": self.passengers_on_board
            }

            self.last_position = (lon, lat)
            return telemetry
            
        except Exception as e:
            logger.error(f"🗺️ Navigation step error for {self.vehicle_id}: {e}")
            return None
    
    def _is_route_complete(self) -> bool:
        """Check if current route is complete"""
        if not self.engine_buffer:
            return False
            
        entry = self.engine_buffer.read_latest()
        if not entry:
            return False
            
        distance_km = entry.get("distance", 0.0)
        return distance_km >= self.total_route_length
    
    def get_navigation_status(self) -> Dict[str, Any]:
        """Get current navigation status"""
        return {
            'vehicle_id': self.vehicle_id,
            'state': self.state.value,
            'engine_on': self.engine_on,
            'route_loaded': self.route_data is not None,
            'route_name': self.route_data.get('route_name') if self.route_data else None,
            'passengers': self.passengers_on_board,
            'journey_start_time': self.journey_start_time.isoformat() if self.journey_start_time else None,
            'last_position': self.last_position,
            'total_route_length_km': self.total_route_length
        }
