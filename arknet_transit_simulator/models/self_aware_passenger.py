#!/usr/bin/env python3
"""
Enhanced Passenger Model
========================

Self-aware passenger with GPS tracking, stop monitoring, and conductor communication.

This enhanced passenger model provides:
- GPS position tracking and stop proximity monitoring
- Conductor communication for stop requests
- Multi-route journey support with connections
- Timeout handling for waiting and missed connections
- Integration with DynamicPassengerService event system
"""

import logging
import asyncio
import math
from typing import List, Dict, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

try:
    # Try relative imports first (when used as module)
    from .people import Passenger, JourneyDetails
    from ..passenger_modeler.passenger_events import PassengerEvent, EventType, EventPriority
except ImportError:
    # Fall back to direct imports (when run directly)
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from people import Passenger, JourneyDetails
    from passenger_modeler.passenger_events import PassengerEvent, EventType, EventPriority


class PassengerState(Enum):
    """Enhanced passenger states for journey lifecycle."""
    WAITING_FOR_PICKUP = "waiting_for_pickup"
    ONBOARD = "onboard" 
    APPROACHING_DESTINATION = "approaching_destination"
    REQUESTING_STOP = "requesting_stop"
    WAITING_FOR_CONNECTION = "waiting_for_connection"
    JOURNEY_COMPLETE = "journey_complete"
    TIMEOUT_EXCEEDED = "timeout_exceeded"


@dataclass
class StopLocation:
    """Represents a bus/transit stop with GPS coordinates."""
    stop_id: str
    stop_name: str
    latitude: float
    longitude: float
    route_ids: List[str] = field(default_factory=list)
    
    def distance_to(self, lat: float, lon: float) -> float:
        """Calculate distance to this stop from given coordinates."""
        return self._haversine_distance(self.latitude, self.longitude, lat, lon)
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 6371 * 2 * math.asin(math.sqrt(a))  # Earth radius in km


@dataclass
class ConnectionPlan:
    """Represents a connection between routes for multi-route journeys."""
    from_route_id: str
    to_route_id: str
    transfer_stop: StopLocation
    max_wait_time: timedelta = field(default_factory=lambda: timedelta(minutes=15))
    connection_buffer: timedelta = field(default_factory=lambda: timedelta(minutes=2))


@dataclass
class EnhancedJourneyDetails(JourneyDetails):
    """Enhanced journey details with multi-route support and GPS tracking."""
    connections: List[ConnectionPlan] = field(default_factory=list)
    current_route_index: int = 0
    current_gps_lat: Optional[float] = None
    current_gps_lon: Optional[float] = None
    pickup_stop: Optional[StopLocation] = None
    destination_stop: Optional[StopLocation] = None
    
    @property
    def current_route_id(self) -> str:
        """Get the current route being traveled."""
        if self.connections and self.current_route_index < len(self.connections):
            return self.connections[self.current_route_index].from_route_id
        return self.route_id
    
    @property
    def has_connections(self) -> bool:
        """Check if this is a multi-route journey."""
        return len(self.connections) > 0
    
    @property
    def is_final_route(self) -> bool:
        """Check if currently on the final route of the journey."""
        return self.current_route_index >= len(self.connections)


class SelfAwarePassenger(Passenger):
    """
    Enhanced passenger with GPS awareness, stop monitoring, and conductor communication.
    
    This passenger can:
    - Track their GPS position relative to their destination
    - Monitor approaching stops and signal intent to disembark
    - Handle multi-route journeys with connections
    - Communicate with conductor/driver for stop requests
    - Manage timeouts for waiting and missed connections
    """
    
    def __init__(
        self,
        passenger_id: str = None,
        journey: EnhancedJourneyDetails = None,
        passenger_type: str = "self_aware",
        stop_request_distance: float = 0.5,  # km
        timeout_threshold: timedelta = None
    ):
        """
        Initialize self-aware passenger.
        
        Args:
            passenger_id: Unique identifier
            journey: Enhanced journey details with GPS and connections
            passenger_type: Type of passenger
            stop_request_distance: Distance threshold for requesting stops (km)
            timeout_threshold: Maximum waiting time before timeout
        """
        # Convert to base JourneyDetails for parent class
        base_journey = JourneyDetails(
            route_id=journey.route_id if journey else "unknown",
            pickup_lat=journey.pickup_lat if journey else 0.0,
            pickup_lon=journey.pickup_lon if journey else 0.0,
            destination_lat=journey.destination_lat if journey else 0.0,
            destination_lon=journey.destination_lon if journey else 0.0,
            pickup_time=journey.pickup_time if journey else datetime.now()
        ) if journey else None
        
        super().__init__(passenger_id, base_journey, passenger_type)
        
        # Enhanced journey details
        self.enhanced_journey = journey or EnhancedJourneyDetails("unknown", 0.0, 0.0, 0.0, 0.0)
        self.passenger_state = PassengerState.WAITING_FOR_PICKUP
        
        # Stop monitoring configuration
        self.stop_request_distance = stop_request_distance
        self.timeout_threshold = timeout_threshold or timedelta(minutes=30)
        
        # Communication callbacks
        self.conductor_callback: Optional[Callable] = None
        self.event_callback: Optional[Callable] = None
        
        # State tracking
        self.stop_requested = False
        self.connection_start_time: Optional[datetime] = None
        self.last_gps_update: Optional[datetime] = None
        
        # Monitoring task
        self.monitoring_task: Optional[asyncio.Task] = None
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{self.component_id}]")
        
    def set_conductor_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for communicating with conductor."""
        self.conductor_callback = callback
        
    def set_event_callback(self, callback: Callable[[PassengerEvent], None]) -> None:
        """Set callback for sending events to passenger service."""
        self.event_callback = callback
        
    async def update_gps_position(self, latitude: float, longitude: float) -> None:
        """Update passenger's current GPS position (when onboard vehicle)."""
        self.enhanced_journey.current_gps_lat = latitude
        self.enhanced_journey.current_gps_lon = longitude
        self.last_gps_update = datetime.now()
        
        # Check if approaching destination
        if self.passenger_state == PassengerState.ONBOARD:
            await self._check_approaching_destination()
            
    async def board_vehicle(self, vehicle_id: str, route_id: str) -> None:
        """Passenger boards vehicle and begins GPS monitoring."""
        self.mark_picked_up()
        self.passenger_state = PassengerState.ONBOARD
        
        # Start monitoring task
        if not self.monitoring_task or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(self._monitor_journey())
            
        # Send event
        if self.event_callback:
            event = PassengerEvent(
                event_type=EventType.PICKUP,
                passenger_id=self.component_id,
                route_id=route_id,
                vehicle_id=vehicle_id,
                location=(self.enhanced_journey.pickup_lat, self.enhanced_journey.pickup_lon),
                priority=EventPriority.HIGH
            )
            self.event_callback(event)
            
        self.logger.info(f"Passenger {self.component_id} boarded vehicle {vehicle_id} on route {route_id}")
        
    async def disembark_vehicle(self, vehicle_id: str) -> None:
        """Passenger disembarks vehicle."""
        # Stop monitoring
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            
        # Check if this is a connection or final destination
        if self.enhanced_journey.has_connections and not self.enhanced_journey.is_final_route:
            await self._handle_connection()
        else:
            await self._complete_journey()
            
        # Send event
        if self.event_callback:
            event = PassengerEvent(
                event_type=EventType.DROPOFF,
                passenger_id=self.component_id,
                vehicle_id=vehicle_id,
                location=(
                    self.enhanced_journey.current_gps_lat or self.enhanced_journey.destination_lat,
                    self.enhanced_journey.current_gps_lon or self.enhanced_journey.destination_lon
                ),
                priority=EventPriority.HIGH
            )
            self.event_callback(event)
            
        self.logger.info(f"Passenger {self.component_id} disembarked vehicle {vehicle_id}")
        
    async def _monitor_journey(self) -> None:
        """Background task to monitor journey progress."""
        try:
            while (self.passenger_state in [PassengerState.ONBOARD, PassengerState.APPROACHING_DESTINATION] 
                   and not self.is_journey_complete):
                
                # Check for timeout
                if self.last_gps_update:
                    time_since_update = datetime.now() - self.last_gps_update
                    if time_since_update > timedelta(minutes=5):
                        self.logger.warning(f"No GPS update for {time_since_update.total_seconds():.0f}s")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except asyncio.CancelledError:
            self.logger.debug(f"Journey monitoring cancelled for passenger {self.component_id}")
        except Exception as e:
            self.logger.error(f"Error in journey monitoring: {e}")
            
    async def _check_approaching_destination(self) -> None:
        """Check if passenger is approaching their destination stop."""
        if not (self.enhanced_journey.current_gps_lat and self.enhanced_journey.current_gps_lon):
            return
            
        # Calculate distance to destination
        current_lat = self.enhanced_journey.current_gps_lat
        current_lon = self.enhanced_journey.current_gps_lon
        
        # Use destination stop if available, otherwise use coordinates
        if self.enhanced_journey.destination_stop:
            distance = self.enhanced_journey.destination_stop.distance_to(current_lat, current_lon)
        else:
            distance = StopLocation._haversine_distance(
                current_lat, current_lon,
                self.enhanced_journey.destination_lat, self.enhanced_journey.destination_lon
            )
            
        # Request stop if within threshold
        if distance <= self.stop_request_distance and not self.stop_requested:
            await self._request_stop()
            
    async def _request_stop(self) -> None:
        """Request stop from conductor/driver."""
        self.stop_requested = True
        self.passenger_state = PassengerState.REQUESTING_STOP
        
        # Communicate with conductor
        if self.conductor_callback:
            self.conductor_callback(
                self.component_id,
                f"Stop request: Passenger {self.component_id} requests stop for destination"
            )
            
        self.logger.info(f"Passenger {self.component_id} requested stop for destination")
        
    async def _handle_connection(self) -> None:
        """Handle connection to next route."""
        self.passenger_state = PassengerState.WAITING_FOR_CONNECTION
        self.connection_start_time = datetime.now()
        self.enhanced_journey.current_route_index += 1
        
        # Start connection timeout monitoring
        asyncio.create_task(self._monitor_connection_timeout())
        
        self.logger.info(
            f"Passenger {self.component_id} waiting for connection to route "
            f"{self.enhanced_journey.connections[self.enhanced_journey.current_route_index-1].to_route_id}"
        )
        
    async def _monitor_connection_timeout(self) -> None:
        """Monitor connection timeout."""
        if not self.connection_start_time:
            return
            
        connection = self.enhanced_journey.connections[self.enhanced_journey.current_route_index - 1]
        max_wait = connection.max_wait_time
        
        await asyncio.sleep(max_wait.total_seconds())
        
        # Check if still waiting
        if self.passenger_state == PassengerState.WAITING_FOR_CONNECTION:
            self.passenger_state = PassengerState.TIMEOUT_EXCEEDED
            self.logger.warning(f"Passenger {self.component_id} connection timeout exceeded")
            
            # Send timeout event
            if self.event_callback:
                event = PassengerEvent(
                    event_type=EventType.TIMEOUT,
                    passenger_id=self.component_id,
                    route_id=connection.to_route_id,
                    metadata={"connection_timeout": max_wait.total_seconds()},
                    priority=EventPriority.HIGH
                )
                self.event_callback(event)
                
    async def _complete_journey(self) -> None:
        """Complete the passenger's journey."""
        self.passenger_state = PassengerState.JOURNEY_COMPLETE
        self.mark_destination_reached()
        
        self.logger.info(f"Passenger {self.component_id} journey completed successfully")
        
    def get_enhanced_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary including enhanced features."""
        base_summary = self.get_journey_summary()
        
        enhanced_summary = {
            **base_summary,
            'passenger_state': self.passenger_state.value,
            'current_route_id': self.enhanced_journey.current_route_id,
            'current_gps': (
                self.enhanced_journey.current_gps_lat,
                self.enhanced_journey.current_gps_lon
            ) if self.enhanced_journey.current_gps_lat else None,
            'has_connections': self.enhanced_journey.has_connections,
            'current_route_index': self.enhanced_journey.current_route_index,
            'stop_requested': self.stop_requested,
            'last_gps_update': self.last_gps_update,
            'connection_start_time': self.connection_start_time,
            'timeout_threshold': self.timeout_threshold.total_seconds()
        }
        
        return enhanced_summary
        
    async def _stop_implementation(self) -> bool:
        """Enhanced stop implementation with cleanup."""
        # Cancel monitoring tasks
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
        return await super()._stop_implementation()


# Convenience function for creating self-aware passengers
def create_self_aware_passenger(
    route_id: str,
    pickup_coords: Tuple[float, float],
    destination_coords: Tuple[float, float],
    connections: List[ConnectionPlan] = None,
    passenger_id: str = None
) -> SelfAwarePassenger:
    """
    Create a self-aware passenger with enhanced journey details.
    
    Args:
        route_id: Initial route ID
        pickup_coords: (latitude, longitude) of pickup point
        destination_coords: (latitude, longitude) of destination
        connections: List of route connections for multi-route journeys
        passenger_id: Optional custom passenger ID
        
    Returns:
        SelfAwarePassenger instance
    """
    journey = EnhancedJourneyDetails(
        route_id=route_id,
        pickup_lat=pickup_coords[0],
        pickup_lon=pickup_coords[1],
        destination_lat=destination_coords[0],
        destination_lon=destination_coords[1],
        connections=connections or []
    )
    
    return SelfAwarePassenger(
        passenger_id=passenger_id,
        journey=journey
    )