#!/usr/bin/env python3
"""
Enhanced Vehicle Conductor - Intelligent Passenger Management Component
----------------------------------------------------------------------
The Enhanced Conductor manages passenger boarding, route monitoring, and driver communication.
Part of the 4-layer hierarchy: DepotManager → Dispatcher → VehicleDriver → Conductor

Enhanced Key Responsibilities:
- Monitor depot and route for passengers matching assigned route
- Evaluate passenger-vehicle proximity and timing intersections
- Manage passenger boarding/disembarking based on configuration rules
- Signal driver to start/stop vehicle with duration control
- Preserve GPS state during engine on/off cycles
- Handle passenger capacity and safety protocols
- Communicate with self-aware passengers for stop requests

The Conductor is a person component that uses PersonState management.
"""

import logging
import threading
import time
import asyncio
import math
import socketio
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

try:
    # Try relative imports first (when used as module)
    from .base_person import BasePerson
    from ..config.config_loader import ConfigLoader
except ImportError:
    # Fall back to direct imports (when run directly)
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from base_person import BasePerson
    from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class ConductorState(Enum):
    """Enhanced conductor operational states."""
    MONITORING = "monitoring"           # Watching for passengers
    EVALUATING = "evaluating"          # Checking passenger eligibility  
    BOARDING_PASSENGERS = "boarding"    # Managing passenger boarding
    SIGNALING_DRIVER = "signaling"     # Communicating with driver
    WAITING_FOR_DEPARTURE = "waiting"  # Ready to signal departure


@dataclass
class StopOperation:
    """Represents a stop operation with timing and passenger details."""
    stop_id: str
    stop_name: str = "Dynamic Stop"
    latitude: float = 0.0
    longitude: float = 0.0
    passengers_boarding: List[str] = field(default_factory=list)
    passengers_disembarking: List[str] = field(default_factory=list)
    requested_duration: float = 0.0  # seconds
    start_time: Optional[datetime] = None
    gps_position: Optional[Tuple[float, float]] = None
    
    @property
    def total_passengers(self) -> int:
        """Total passengers involved in this stop."""
        return len(self.passengers_boarding) + len(self.passengers_disembarking)


@dataclass
class ConductorConfig:
    """Enhanced conductor configuration from config.ini."""
    # Proximity settings
    pickup_radius_km: float = 0.2
    boarding_time_window_minutes: float = 5.0
    
    # Stop duration settings
    min_stop_duration_seconds: float = 15.0
    max_stop_duration_seconds: float = 180.0
    per_passenger_boarding_time: float = 8.0
    per_passenger_disembarking_time: float = 5.0
    
    # Operational settings
    monitoring_interval_seconds: float = 2.0
    gps_precision_meters: float = 10.0
    
    # Communication timeouts
    driver_response_timeout_seconds: float = 30.0
    passenger_boarding_timeout_seconds: float = 120.0


class Conductor(BasePerson):
    """
    Enhanced Vehicle Conductor for intelligent passenger management
    
    The enhanced conductor is responsible for:
    1. Monitoring depot and route for passengers
    2. Evaluating passenger-vehicle proximity and timing
    3. Managing passenger boarding/disembarking
    4. Signaling driver for stop/start operations
    5. Preserving GPS state during engine on/off cycles
    6. Handling passenger capacity and safety protocols
    """
    
    def __init__(
        self, 
        conductor_id: str, 
        conductor_name: str, 
        vehicle_id: str, 
        assigned_route_id: str = None,
        capacity: int = 40, 
        tick_time: float = 1.0,
        config: ConductorConfig = None,
        sio_url: str = "http://localhost:3000",
        use_socketio: bool = True
    ):
        # Initialize BasePerson with PersonState
        super().__init__(conductor_id, "Conductor", conductor_name)
        
        self.vehicle_id = vehicle_id
        self.assigned_route_id = assigned_route_id or "UNKNOWN"
        self.capacity = capacity
        self.tick_time = tick_time
        self.config = config or ConductorConfig()
        
        # Basic passenger state (existing functionality)
        self.passengers_on_board = 0
        self.seats_available = capacity
        self.boarding_active = False
        
        # Socket.IO configuration (NEW for Priority 2)
        self.use_socketio = use_socketio
        self.sio_url = sio_url
        self.sio_connected = False
        if self.use_socketio:
            self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)
            self._setup_socketio_handlers()
        else:
            self.sio = None
        
        # Enhanced operational state
        self.conductor_state = ConductorState.MONITORING
        self.current_stop_operation: Optional[StopOperation] = None
        self.current_vehicle_position: Optional[Tuple[float, float]] = None
        self.preserved_gps_position: Optional[Tuple[float, float]] = None
        
        # Passenger tracking
        self.monitored_passengers: Dict[str, Any] = {}  # passenger_id -> passenger_data
        self.boarding_queue: List[str] = []
        self.disembarking_queue: List[str] = []
        
        # Enhanced callbacks
        self.on_full_callback: Optional[Callable] = None
        self.on_empty_callback: Optional[Callable] = None
        self.driver_callback: Optional[Callable[[str, dict], None]] = None
        self.passenger_service_callback: Optional[Callable] = None
        self.depot_callback: Optional[Callable[[str], List]] = None
        
        # Threading and async tasks
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.stop_operation_task: Optional[asyncio.Task] = None
        
        self.logger.info(
            f"Enhanced Conductor {conductor_name} initialized for vehicle {vehicle_id} "
            f"on route {self.assigned_route_id} (capacity: {capacity})"
        )
    
    @classmethod
    def from_config(
        cls, 
        conductor_id: str, 
        conductor_name: str, 
        vehicle_id: str, 
        route_id: str, 
        config_path: str = None
    ) -> 'Conductor':
        """
        Create enhanced conductor from configuration file.
        
        Args:
            conductor_id: Unique conductor identifier
            conductor_name: Human-readable name
            vehicle_id: Assigned vehicle ID
            route_id: Assigned route ID
            config_path: Path to config.ini file
            
        Returns:
            Configured Conductor instance
        """
        try:
            config_loader = ConfigLoader(config_path)
            config_data = config_loader.get_config()
            
            # Extract conductor-specific configuration
            conductor_config = ConductorConfig()
            
            if 'conductor' in config_data:
                conductor_section = config_data['conductor']
                conductor_config.pickup_radius_km = float(conductor_section.get('pickup_radius_km', 0.2))
                conductor_config.boarding_time_window_minutes = float(conductor_section.get('boarding_time_window_minutes', 5.0))
                conductor_config.min_stop_duration_seconds = float(conductor_section.get('min_stop_duration_seconds', 15.0))
                conductor_config.max_stop_duration_seconds = float(conductor_section.get('max_stop_duration_seconds', 180.0))
                conductor_config.per_passenger_boarding_time = float(conductor_section.get('per_passenger_boarding_time', 8.0))
                conductor_config.per_passenger_disembarking_time = float(conductor_section.get('per_passenger_disembarking_time', 5.0))
                conductor_config.monitoring_interval_seconds = float(conductor_section.get('monitoring_interval_seconds', 2.0))
                conductor_config.driver_response_timeout_seconds = float(conductor_section.get('driver_response_timeout_seconds', 30.0))
                conductor_config.passenger_boarding_timeout_seconds = float(conductor_section.get('passenger_boarding_timeout_seconds', 120.0))
            
            # Get vehicle capacity from config
            capacity = 40
            if 'vehicle_defaults' in config_data:
                capacity = int(config_data['vehicle_defaults'].get('passengers', 40))
                
            return cls(
                conductor_id=conductor_id,
                conductor_name=conductor_name,
                vehicle_id=vehicle_id,
                assigned_route_id=route_id,
                capacity=capacity,
                config=conductor_config
            )
            
        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {e}")
            return cls(conductor_id, conductor_name, vehicle_id, route_id)
    
    def set_driver_callback(self, callback: Callable[[str, dict], None]) -> None:
        """Set callback for communicating with vehicle driver."""
        self.driver_callback = callback
        
    def set_passenger_service_callback(self, callback: Callable) -> None:
        """Set callback for communicating with passenger service."""
        self.passenger_service_callback = callback
        
    def set_depot_callback(self, callback: Callable[[str], List]) -> None:
        """Set callback for querying depot for passengers."""
        self.depot_callback = callback
        
    def _setup_socketio_handlers(self) -> None:
        """Set up Socket.IO event handlers (Priority 2)."""
        
        @self.sio.event
        async def connect():
            self.sio_connected = True
            self.logger.info(f"[{self.component_id}] Socket.IO connected to {self.sio_url}")
        
        @self.sio.event
        async def disconnect():
            self.sio_connected = False
            self.logger.warning(f"[{self.component_id}] Socket.IO disconnected")
            
        @self.sio.event
        async def connect_error(data):
            self.logger.error(f"[{self.component_id}] Socket.IO connection error: {data}")
            
    async def _connect_socketio(self) -> None:
        """Connect to Socket.IO server (Priority 2)."""
        if not self.use_socketio or self.sio_connected:
            return
        
        try:
            await self.sio.connect(self.sio_url)
            self.logger.info(f"[{self.component_id}] Connected to Socket.IO server: {self.sio_url}")
        except Exception as e:
            self.logger.error(f"[{self.component_id}] Socket.IO connection failed: {e}")
            self.logger.info(f"[{self.component_id}] Falling back to callback-based communication")
            self.use_socketio = False  # Disable Socket.IO, fall back to callbacks
            
    async def _disconnect_socketio(self) -> None:
        """Disconnect from Socket.IO server (Priority 2)."""
        if self.use_socketio and self.sio_connected:
            try:
                await self.sio.disconnect()
                self.logger.info(f"[{self.component_id}] Disconnected from Socket.IO server")
            except Exception as e:
                self.logger.error(f"[{self.component_id}] Error disconnecting Socket.IO: {e}")
        
    def assign_to_route(self, route_id: str) -> None:
        """Assign conductor to specific route."""
        self.assigned_route_id = route_id
        self.logger.info(f"Conductor {self.component_id} assigned to route {route_id}")
    
    async def _start_implementation(self) -> bool:
        """Enhanced conductor start with passenger monitoring."""
        try:
            self.logger.info(
                f"Enhanced Conductor {self.person_name} starting duties for vehicle {self.vehicle_id} "
                f"on route {self.assigned_route_id}"
            )
            
            # Connect to Socket.IO (Priority 2)
            if self.use_socketio:
                await self._connect_socketio()
            
            # Start basic conductor operations
            if not self._running:
                self._running = True
                
            # Start enhanced monitoring
            self.conductor_state = ConductorState.MONITORING
            
            # Start passenger monitoring task
            self.monitoring_task = asyncio.create_task(self._monitor_passengers())
                
            self.logger.info(f"Enhanced Conductor {self.person_name} ready for intelligent passenger management")
            return True
            
        except Exception as e:
            self.logger.error(f"Enhanced Conductor {self.person_name} failed to start duties: {e}")
            return False

    async def _stop_implementation(self) -> bool:
        """Enhanced conductor stop with cleanup."""
        try:
            self.logger.info(f"Enhanced Conductor {self.person_name} finishing duties for vehicle {self.vehicle_id}")
            
            # Disconnect Socket.IO (Priority 2)
            if self.use_socketio:
                await self._disconnect_socketio()
            
            # Stop basic operations
            self._running = False
            if self._thread:
                self._thread.join(timeout=2)
                
            # Cancel enhanced monitoring tasks
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
                    
            if self.stop_operation_task and not self.stop_operation_task.done():
                self.stop_operation_task.cancel()
                try:
                    await self.stop_operation_task
                except asyncio.CancelledError:
                    pass
                
            # Reset state
            self.conductor_state = ConductorState.MONITORING
            self.current_stop_operation = None
            self.preserved_gps_position = None
                
            # Check passenger state
            if not self.is_empty():
                self.logger.warning(f"Conductor {self.person_name} leaving with {self.passengers_on_board} passengers still on board")
            
            self.logger.info(f"Enhanced Conductor {self.person_name} duties completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Enhanced Conductor {self.person_name} failed to finish duties: {e}")
            return False
    
    async def update_vehicle_position(self, latitude: float, longitude: float) -> None:
        """Update current vehicle GPS position for proximity calculations."""
        self.current_vehicle_position = (latitude, longitude)
        
        # If we have an active stop operation, preserve this position
        if self.current_stop_operation and not self.current_stop_operation.gps_position:
            self.current_stop_operation.gps_position = (latitude, longitude)
            
    async def _monitor_passengers(self) -> None:
        """Background task to monitor passengers and manage operations."""
        try:
            while self._running and self.conductor_state != ConductorState.WAITING_FOR_DEPARTURE:
                # Query depot for passengers matching our route
                if self.depot_callback:
                    try:
                        route_passengers = self.depot_callback(self.assigned_route_id)
                        await self._evaluate_passengers(route_passengers)
                    except Exception as e:
                        self.logger.warning(f"Error querying depot: {e}")
                        
                # Check for passengers requesting stops
                await self._check_stop_requests()
                
                # Process any pending operations
                if self.conductor_state == ConductorState.EVALUATING:
                    await self._process_passenger_operations()
                    
                await asyncio.sleep(self.config.monitoring_interval_seconds)
                
        except asyncio.CancelledError:
            self.logger.debug(f"Conductor {self.component_id} monitoring cancelled")
        except Exception as e:
            self.logger.error(f"Error in passenger monitoring: {e}")
            
    async def _evaluate_passengers(self, passengers: List[Any]) -> None:
        """Evaluate passengers for boarding/disembarking eligibility."""
        if not self.current_vehicle_position:
            return
            
        eligible_boarding = []
        eligible_disembarking = []
        
        vehicle_lat, vehicle_lon = self.current_vehicle_position
        
        for passenger in passengers:
            try:
                # Check if passenger has route information
                if not hasattr(passenger, 'assigned_route_id') and not hasattr(passenger, 'journey'):
                    continue
                    
                passenger_route = getattr(passenger, 'assigned_route_id', None)
                if hasattr(passenger, 'journey') and hasattr(passenger.journey, 'route_id'):
                    passenger_route = passenger.journey.route_id
                    
                # Skip if not our route
                if passenger_route != self.assigned_route_id:
                    continue
                    
                # Check pickup eligibility
                if (not getattr(passenger, 'is_picked_up', False) and 
                    hasattr(passenger, 'journey')):
                    
                    pickup_distance = self._calculate_distance(
                        vehicle_lat, vehicle_lon,
                        passenger.journey.pickup_lat,
                        passenger.journey.pickup_lon
                    )
                    
                    if pickup_distance <= self.config.pickup_radius_km:
                        # Check timing window
                        if self._is_within_time_window(passenger):
                            eligible_boarding.append(passenger.component_id)
                            
                # Check dropoff eligibility  
                elif (getattr(passenger, 'is_picked_up', False) and 
                      getattr(passenger, 'stop_requested', False)):
                    
                    eligible_disembarking.append(passenger.component_id)
                    
            except Exception as e:
                self.logger.warning(f"Error evaluating passenger {getattr(passenger, 'component_id', 'unknown')}: {e}")
                
        # If we have eligible passengers, prepare stop operation
        if eligible_boarding or eligible_disembarking:
            await self._prepare_stop_operation(eligible_boarding, eligible_disembarking)
            
    def _is_within_time_window(self, passenger: Any) -> bool:
        """Check if passenger is within boarding time window."""
        try:
            if not hasattr(passenger, 'journey') or not hasattr(passenger.journey, 'pickup_time'):
                return True  # No specific pickup time
                
            now = datetime.now()
            pickup_time = passenger.journey.pickup_time
            time_diff = abs((now - pickup_time).total_seconds() / 60)
            
            return time_diff <= self.config.boarding_time_window_minutes
        except:
            return True  # Default to allow if we can't check
            
    async def _check_stop_requests(self) -> None:
        """Check for passengers requesting stops."""
        # Process disembarking queue
        if self.disembarking_queue and self.conductor_state == ConductorState.MONITORING:
            await self._prepare_stop_operation([], self.disembarking_queue.copy())
            self.disembarking_queue.clear()
            
    async def _prepare_stop_operation(self, boarding: List[str], disembarking: List[str]) -> None:
        """Prepare stop operation for passenger boarding/disembarking."""
        if self.conductor_state in [ConductorState.BOARDING_PASSENGERS, ConductorState.SIGNALING_DRIVER]:
            return  # Already handling a stop
            
        # Calculate stop duration
        boarding_time = len(boarding) * self.config.per_passenger_boarding_time
        disembarking_time = len(disembarking) * self.config.per_passenger_disembarking_time
        total_time = max(
            boarding_time + disembarking_time + 10,  # 10 second buffer
            self.config.min_stop_duration_seconds
        )
        total_time = min(total_time, self.config.max_stop_duration_seconds)
        
        # Create stop operation
        self.current_stop_operation = StopOperation(
            stop_id=f"STOP_{datetime.now().strftime('%H%M%S')}",
            stop_name="Dynamic Stop",
            latitude=self.current_vehicle_position[0] if self.current_vehicle_position else 0.0,
            longitude=self.current_vehicle_position[1] if self.current_vehicle_position else 0.0,
            passengers_boarding=boarding,
            passengers_disembarking=disembarking,
            requested_duration=total_time,
            start_time=datetime.now()
        )
        
        self.conductor_state = ConductorState.SIGNALING_DRIVER
        
        # Signal driver to stop
        await self._signal_driver_stop()
        
    async def _signal_driver_stop(self) -> None:
        """Signal driver to stop vehicle (Priority 2: Socket.IO + callback fallback)."""
        if not self.current_stop_operation:
            return
            
        # Preserve current GPS position
        self.preserved_gps_position = self.current_vehicle_position
        
        # Prepare signal data (Socket.IO format)
        signal_data = {
            'vehicle_id': self.vehicle_id,
            'conductor_id': self.component_id,
            'stop_id': self.current_stop_operation.stop_id,
            'passengers_boarding': len(self.current_stop_operation.passengers_boarding),
            'passengers_disembarking': len(self.current_stop_operation.passengers_disembarking),
            'duration_seconds': self.current_stop_operation.requested_duration,
            'gps_position': [
                self.current_stop_operation.latitude,
                self.current_stop_operation.longitude
            ]
        }
        
        self.logger.info(
            f"Conductor {self.component_id} signaling driver to stop for "
            f"{self.current_stop_operation.total_passengers} passengers "
            f"(duration: {self.current_stop_operation.requested_duration:.0f}s)"
        )
        
        # Try Socket.IO first (Priority 2)
        if self.use_socketio and self.sio_connected:
            try:
                await self.sio.emit('conductor:request:stop', signal_data)
                self.logger.info(f"[{self.component_id}] Stop request sent via Socket.IO")
                # Start stop operation management
                self.stop_operation_task = asyncio.create_task(self._manage_stop_operation())
                return
            except Exception as e:
                self.logger.error(f"Socket.IO emit failed: {e}, falling back to callback")
        
        # Fallback to callback (existing mechanism)
        if self.driver_callback:
            # Convert to old callback format for backward compatibility
            callback_data = {
                'action': 'stop_vehicle',
                'conductor_id': self.component_id,
                'duration': self.current_stop_operation.requested_duration,
                'location': {
                    'stop_id': self.current_stop_operation.stop_id,
                    'latitude': self.current_stop_operation.latitude,
                    'longitude': self.current_stop_operation.longitude
                },
                'passengers_boarding': len(self.current_stop_operation.passengers_boarding),
                'passengers_disembarking': len(self.current_stop_operation.passengers_disembarking),
                'preserve_gps': True,
                'gps_position': self.preserved_gps_position
            }
            self.driver_callback(self.component_id, callback_data)
            # Start stop operation management
            self.stop_operation_task = asyncio.create_task(self._manage_stop_operation())
        else:
            self.logger.warning(f"[{self.component_id}] No communication method available for driver!")

        
    async def _manage_stop_operation(self) -> None:
        """Manage the stop operation process."""
        try:
            self.conductor_state = ConductorState.BOARDING_PASSENGERS
            
            # Initialize start time if not already set
            if self.current_stop_operation.start_time is None:
                self.current_stop_operation.start_time = datetime.now()
            
            # Handle disembarking first (faster)
            for passenger_id in self.current_stop_operation.passengers_disembarking:
                success = self.alight_passengers(1)  # Use existing method
                if success:
                    self.logger.info(f"Passenger {passenger_id} disembarked successfully")
                    
            # Then handle boarding
            for passenger_id in self.current_stop_operation.passengers_boarding:
                success = self.board_passengers(1)  # Use existing method
                if success:
                    self.logger.info(f"Passenger {passenger_id} boarded successfully")
                else:
                    self.logger.warning(f"Could not board passenger {passenger_id} - vehicle full")
                    
            # Wait for remaining time or until complete
            elapsed = (datetime.now() - self.current_stop_operation.start_time).total_seconds()
            remaining_time = max(0, self.current_stop_operation.requested_duration - elapsed)
            
            if remaining_time > 0:
                await asyncio.sleep(remaining_time)
                
            # Signal driver to continue
            await self._signal_driver_continue()
            
        except Exception as e:
            self.logger.error(f"Error managing stop operation: {e}")
            # Signal driver to continue anyway
            await self._signal_driver_continue()
            
    async def _signal_driver_continue(self) -> None:
        """Signal driver to continue driving (Priority 2: Socket.IO + callback fallback)."""
        
        # Prepare signal data (Socket.IO format)
        signal_data = {
            'vehicle_id': self.vehicle_id,
            'conductor_id': self.component_id,
            'passenger_count': self.passengers_on_board,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Conductor {self.component_id} signaling driver to continue")
        
        # Try Socket.IO first (Priority 2)
        if self.use_socketio and self.sio_connected:
            try:
                await self.sio.emit('conductor:ready:depart', signal_data)
                self.logger.info(f"[{self.component_id}] Depart signal sent via Socket.IO")
            except Exception as e:
                self.logger.error(f"Socket.IO emit failed: {e}, falling back to callback")
                # Fall through to callback
                if self.driver_callback:
                    callback_data = {
                        'action': 'continue_driving',
                        'conductor_id': self.component_id,
                        'restore_gps': True,
                        'gps_position': self.preserved_gps_position
                    }
                    self.driver_callback(self.component_id, callback_data)
        elif self.driver_callback:
            # Fallback to callback (existing mechanism)
            callback_data = {
                'action': 'continue_driving',
                'conductor_id': self.component_id,
                'restore_gps': True,
                'gps_position': self.preserved_gps_position
            }
            self.driver_callback(self.component_id, callback_data)
        else:
            self.logger.warning(f"[{self.component_id}] No communication method available for driver!")
        
        # Reset state
        self.current_stop_operation = None
        self.preserved_gps_position = None
        self.conductor_state = ConductorState.MONITORING
        
    async def receive_stop_request(self, passenger_id: str, message: str) -> None:
        """Receive stop request from passenger."""
        self.logger.info(f"Stop request from {passenger_id}: {message}")
        
        # Add to disembarking queue
        if passenger_id not in self.disembarking_queue:
            self.disembarking_queue.append(passenger_id)
            
        # If not currently stopping, prepare stop operation
        if self.conductor_state == ConductorState.MONITORING:
            await self._prepare_stop_operation([], [passenger_id])
            
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS points in kilometers."""
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 6371 * 2 * math.asin(math.sqrt(a))  # Earth radius in km
        
    async def _process_passenger_operations(self) -> None:
        """Process pending passenger operations."""
        # This method handles any additional passenger operation logic
        self.conductor_state = ConductorState.MONITORING
    
    def set_departure_callback(self, callback: Callable):
        """Set callback to notify driver when vehicle is full"""
        self.on_full_callback = callback
        
    def set_empty_callback(self, callback: Callable):
        """Set callback to notify when vehicle is empty"""
        self.on_empty_callback = callback
    
    def board_passengers(self, count: int) -> bool:
        """
        Board passengers onto the vehicle
        
        Args:
            count: Number of passengers to board
            
        Returns:
            bool: True if passengers could board, False if not enough seats
        """
        if count <= 0:
            return False
            
        if self.passengers_on_board + count > self.capacity:
            # Can't board - not enough seats
            available = self.capacity - self.passengers_on_board
            logger.info(f"Conductor {self.vehicle_id}: Only {available} seats available, can't board {count}")
            return False
            
        # Board the passengers
        self.passengers_on_board += count
        self.seats_available = self.capacity - self.passengers_on_board
        
        logger.info(f"Conductor {self.vehicle_id}: Boarded {count} passengers ({self.passengers_on_board}/{self.capacity})")
        
        # Check if vehicle is now full
        if self.is_full():
            logger.info(f"Conductor {self.vehicle_id}: VEHICLE FULL! Signaling driver to depart")
            if self.on_full_callback:
                self.on_full_callback()
                
        return True
    
    def alight_passengers(self, count: int = None) -> int:
        """
        Passengers alighting (getting off)
        
        Args:
            count: Number of passengers alighting (None = all passengers)
            
        Returns:
            int: Number of passengers that alighted
        """
        if count is None:
            count = self.passengers_on_board
            
        alighted = min(count, self.passengers_on_board)
        self.passengers_on_board -= alighted
        self.seats_available = self.capacity - self.passengers_on_board
        
        logger.info(f"Conductor {self.vehicle_id}: {alighted} passengers alighted ({self.passengers_on_board}/{self.capacity})")
        
        # Check if vehicle is now empty
        if self.is_empty() and self.on_empty_callback:
            self.on_empty_callback()
            
        return alighted
    
    def is_full(self) -> bool:
        """Check if vehicle is at capacity"""
        return self.passengers_on_board >= self.capacity
        
    def is_empty(self) -> bool:
        """Check if vehicle has no passengers"""
        return self.passengers_on_board == 0
        
    def has_seats_available(self) -> bool:
        """Check if vehicle has available seats"""
        return self.seats_available > 0
        
    def get_passenger_count(self) -> int:
        """Get current passenger count"""
        return self.passengers_on_board
        
    def get_available_seats(self) -> int:
        """Get number of available seats"""
        return self.seats_available
        
    def get_capacity(self) -> int:
        """Get vehicle capacity"""
        return self.capacity
        
    def start_boarding(self):
        """Start accepting passengers"""
        self.boarding_active = True
        logger.info(f"Conductor {self.vehicle_id}: Boarding started - {self.seats_available} seats available")
        
    def stop_boarding(self):
        """Stop accepting passengers"""
        self.boarding_active = False
        logger.info(f"Conductor {self.vehicle_id}: Boarding stopped")
        
    def is_boarding_active(self) -> bool:
        """Check if boarding is active"""
        return self.boarding_active
        
    def get_passenger_status(self) -> Dict[str, Any]:
        """Get conductor's passenger management status"""
        return {
            'vehicle_id': self.vehicle_id,
            'passengers': self.passengers_on_board,
            'capacity': self.capacity,
            'seats_available': self.seats_available,
            'boarding_active': self.boarding_active,
            'is_full': self.is_full(),
            'is_empty': self.is_empty()
        }
        
    def reset(self):
        """Reset conductor state (for new journey)"""
        self.passengers_on_board = 0
        self.seats_available = self.capacity
        self.boarding_active = False
        logger.info(f"Conductor {self.vehicle_id}: Reset for new journey")
        
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get comprehensive enhanced conductor status."""
        base_status = self.get_passenger_status()
        
        enhanced_status = {
            **base_status,
            'conductor_state': self.conductor_state.value,
            'assigned_route_id': self.assigned_route_id,
            'current_position': self.current_vehicle_position,
            'preserved_gps': self.preserved_gps_position,
            'monitored_passengers': len(self.monitored_passengers),
            'boarding_queue': len(self.boarding_queue),
            'disembarking_queue': len(self.disembarking_queue),
            'current_stop_operation': {
                'active': self.current_stop_operation is not None,
                'passengers_boarding': len(self.current_stop_operation.passengers_boarding) if self.current_stop_operation else 0,
                'passengers_disembarking': len(self.current_stop_operation.passengers_disembarking) if self.current_stop_operation else 0,
                'duration': self.current_stop_operation.requested_duration if self.current_stop_operation else 0,
                'stop_id': self.current_stop_operation.stop_id if self.current_stop_operation else None
            },
            'config': {
                'pickup_radius_km': self.config.pickup_radius_km,
                'min_stop_duration': self.config.min_stop_duration_seconds,
                'max_stop_duration': self.config.max_stop_duration_seconds,
                'boarding_time_per_passenger': self.config.per_passenger_boarding_time,
                'disembarking_time_per_passenger': self.config.per_passenger_disembarking_time
            }
        }
        
        return enhanced_status

    def __str__(self):
        """Enhanced string representation"""
        status = "FULL" if self.is_full() else f"{self.seats_available} seats"
        boarding = "BOARDING" if self.boarding_active else "CLOSED"
        enhanced_state = f" [{self.conductor_state.value.upper()}]"
        route_info = f" Route:{self.assigned_route_id}"
        return f"Conductor({self.vehicle_id}): {self.passengers_on_board}/{self.capacity} - {status} - {boarding}{enhanced_state}{route_info}"