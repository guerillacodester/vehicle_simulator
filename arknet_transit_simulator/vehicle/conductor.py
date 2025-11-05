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
    from common.config_provider import get_config
    _config_available = True
except ImportError:
    _config_available = False

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
    """
    Enhanced conductor configuration - Loaded dynamically from ConfigurationService.
    
    CRITICAL: pickup_radius_km has NO default - must be loaded from database.
    This ensures proximity settings are always database-driven, not hardcoded.
    """
    # Proximity settings - Database-driven (operational-configurations table)
    pickup_radius_km: Optional[float] = None  # MUST load from DB - no hardcoded default
    boarding_time_window_minutes: float = 5.0
    
    # Stop duration settings
    min_stop_duration_seconds: float = 15.0
    max_stop_duration_seconds: float = 180.0
    per_passenger_boarding_time: float = 8.0
    per_passenger_disembarking_time: float = 5.0
    
    # Operational settings
    monitoring_interval_seconds: float = 2.0
    gps_precision_meters: float = 10.0
    
    # Depot operations - NEW
    depot_wait_time_minutes: float = 40.0
    depot_proximity_threshold_km: float = 0.1
    
    # Route operations - NEW
    end_loiter_minutes: float = 2.0
    
    # Communication timeouts
    driver_response_timeout_seconds: float = 30.0
    passenger_boarding_timeout_seconds: float = 120.0
    
    def validate(self) -> None:
        """
        Validate configuration parameters are within acceptable ranges.
        
        Raises:
            ValueError: If any parameter is out of bounds or missing
        """
        if self.pickup_radius_km is None:
            raise ValueError(
                "pickup_radius_km is not configured. "
                "Must load from database (operational-configurations table). "
                "Run: python arknet_fleet_manager/seed_operational_config.py"
            )
        
        if not (0.05 <= self.pickup_radius_km <= 5.0):
            raise ValueError(
                f"pickup_radius_km={self.pickup_radius_km} out of bounds. "
                f"Must be between 0.05 and 5.0 kilometers"
            )
        
        if not (1.0 <= self.boarding_time_window_minutes <= 30.0):
            raise ValueError(
                f"boarding_time_window_minutes={self.boarding_time_window_minutes} out of bounds"
            )
    
    @classmethod
    async def from_config_service(cls, config_service=None):
        """
        Load configuration from ConfigurationService.
        
        Args:
            config_service: ConfigurationService instance (optional)
        
        Returns:
            ConductorConfig instance with values from Strapi or defaults
        """
        if config_service is None:
            # Try to get config service, fallback to defaults if not available
            try:
                from ..services.config_service import get_config_service
                config_service = await get_config_service()
            except Exception as e:
                logger.warning(f"Could not load ConfigurationService, using defaults: {e}")
                return cls()
        
        # Load all conductor configuration parameters
        # CRITICAL: No hardcoded defaults - must come from database
        pickup_radius_km = await config_service.get(
            "conductor.proximity.pickup_radius_km",
            default=None  # Force fail-fast if not configured in Strapi
        )
        boarding_time_window_minutes = await config_service.get(
            "conductor.proximity.boarding_time_window_minutes",
            default=5.0
        )
        min_stop_duration_seconds = await config_service.get(
            "conductor.stop_duration.min_seconds",
            default=15.0
        )
        max_stop_duration_seconds = await config_service.get(
            "conductor.stop_duration.max_seconds",
            default=180.0
        )
        per_passenger_boarding_time = await config_service.get(
            "conductor.stop_duration.per_passenger_boarding_time",
            default=8.0
        )
        per_passenger_disembarking_time = await config_service.get(
            "conductor.stop_duration.per_passenger_disembarking_time",
            default=5.0
        )
        monitoring_interval_seconds = await config_service.get(
            "conductor.operational.monitoring_interval_seconds",
            default=2.0
        )
        gps_precision_meters = await config_service.get(
            "conductor.operational.gps_precision_meters",
            default=10.0
        )
        depot_wait_time_minutes = await config_service.get(
            "conductor.depot.wait_time_minutes",
            default=40.0
        )
        depot_proximity_threshold_km = await config_service.get(
            "conductor.depot.proximity_threshold_km",
            default=0.1
        )
        end_loiter_minutes = await config_service.get(
            "conductor.route.end_loiter_minutes",
            default=2.0
        )
        
        logger.info(f"[ConductorConfig] Loaded from ConfigurationService:")
        logger.info(f"  • pickup_radius_km: {pickup_radius_km}")
        logger.info(f"  • boarding_time_window_minutes: {boarding_time_window_minutes}")
        logger.info(f"  • min_stop_duration_seconds: {min_stop_duration_seconds}")
        logger.info(f"  • monitoring_interval_seconds: {monitoring_interval_seconds}")
        logger.info(f"  • depot_wait_time_minutes: {depot_wait_time_minutes}")
        logger.info(f"  • depot_proximity_threshold_km: {depot_proximity_threshold_km}")
        logger.info(f"  • end_loiter_minutes: {end_loiter_minutes}")
        
        config = cls(
            pickup_radius_km=pickup_radius_km,
            boarding_time_window_minutes=boarding_time_window_minutes,
            min_stop_duration_seconds=min_stop_duration_seconds,
            max_stop_duration_seconds=max_stop_duration_seconds,
            per_passenger_boarding_time=per_passenger_boarding_time,
            per_passenger_disembarking_time=per_passenger_disembarking_time,
            monitoring_interval_seconds=monitoring_interval_seconds,
            gps_precision_meters=gps_precision_meters,
            depot_wait_time_minutes=depot_wait_time_minutes,
            depot_proximity_threshold_km=depot_proximity_threshold_km,
            end_loiter_minutes=end_loiter_minutes
        )
        
        # Validate configuration before returning
        config.validate()
        
        return config


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
        capacity: int,  # REQUIRED: Must come from database
        assigned_route_id: str = None,
        tick_time: float = 1.0,
        config: ConductorConfig = None,
        sio_url: Optional[str] = None,
        use_socketio: bool = True,
        passenger_db = None,  # DEPRECATED: Use commuter_service_url instead
        commuter_service_url: Optional[str] = None,  # NEW: URL for commuter_service HTTP API
        hardware_client = None  # Optional: HardwareEventClient for event reporting
    ):
        """
        Initialize conductor.
        
        Args:
            sio_url: Socket.IO URL. If None, loads from config.ini via ConfigProvider.
            commuter_service_url: URL for commuter_service API (default: http://localhost:4000)
            passenger_db: DEPRECATED - kept for backward compatibility
        """
        # Initialize BasePerson with PersonState
        super().__init__(conductor_id, "Conductor", conductor_name)
        
        # Load sio_url from config if not provided
        if sio_url is None:
            if _config_available:
                try:
                    config_provider = get_config()
                    sio_url = config_provider.infrastructure.strapi_url
                except Exception:
                    sio_url = "http://localhost:1337"  # Fallback default
            else:
                sio_url = "http://localhost:1337"  # Fallback if config not available
        
        self.vehicle_id = vehicle_id
        self.assigned_route_id = assigned_route_id or "UNKNOWN"
        self.capacity = capacity
        self.tick_time = tick_time
        self.config = config or ConductorConfig()
        
        # Commuter Service HTTP Client (uses reservoir pattern)
        self.commuter_service_url = commuter_service_url or "http://localhost:4000"
        self.commuter_client = None  # Initialized in start()
        
        # DEPRECATED: Keep passenger_db for backward compatibility only
        self.passenger_db = passenger_db
        self.boarded_passengers: List[str] = []  # Track individual passenger IDs
        
        # Track passenger destinations for alighting logic
        self.passenger_destinations: Dict[str, Tuple[float, float]] = {}  # passenger_id -> (dest_lat, dest_lon)
        
        # Depot detection and boarding state
        self.depot_coordinates: Optional[Dict[str, float]] = None  # Cached depot lat/lon for route
        self.is_at_depot_flag: bool = False  # Current depot proximity state
        self.depot_boarding_active: bool = False  # Whether in depot boarding mode
        
        # Hardware event client (for both simulation and real hardware)
        self.hardware_client = hardware_client
        
        # Current vehicle position (needed for hardware events)
        self.current_latitude: float = 0.0
        self.current_longitude: float = 0.0
        
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
        
        # Auto-wire on_full_callback to signal driver
        self.enable_auto_depart_on_full()
        
        # Threading and async tasks
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.stop_operation_task: Optional[asyncio.Task] = None
        
        self.logger.info(
            f"Enhanced Conductor {conductor_name} initialized for vehicle {vehicle_id} "
            f"on route {self.assigned_route_id} (capacity: {capacity})"
        )
    
    async def initialize_config(self, config_service=None):
        """
        Initialize dynamic configuration from ConfigurationService.
        Call this method after constructing the Conductor to load configuration from Strapi.
        
        Args:
            config_service: Optional ConfigurationService instance. If None, will get global instance.
        
        Example:
            conductor = Conductor(...)
            await conductor.initialize_config()
        """
        try:
            self.config = await ConductorConfig.from_config_service(config_service)
            self.logger.info(
                f"[{self.component_name}] Configuration loaded from ConfigurationService:\n"
                f"  • pickup_radius_km: {self.config.pickup_radius_km}\n"
                f"  • boarding_time_window_minutes: {self.config.boarding_time_window_minutes}\n"
                f"  • min_stop_duration_seconds: {self.config.min_stop_duration_seconds}\n"
                f"  • max_stop_duration_seconds: {self.config.max_stop_duration_seconds}\n"
                f"  • per_passenger_boarding_time: {self.config.per_passenger_boarding_time}\n"
                f"  • per_passenger_disembarking_time: {self.config.per_passenger_disembarking_time}\n"
                f"  • monitoring_interval_seconds: {self.config.monitoring_interval_seconds}\n"
                f"  • gps_precision_meters: {self.config.gps_precision_meters}"
            )
        except Exception as e:
            self.logger.warning(
                f"[{self.component_name}] Could not load config from ConfigurationService, "
                f"using existing config: {e}"
            )
    
    @classmethod
    def from_config(
        cls,
        conductor_id: str,
        conductor_name: str,
        vehicle_id: str,
        capacity: int,  # REQUIRED: Must be provided from database
        route_id: str, 
        config_path: str = None
    ) -> 'Conductor':
        """
        Create enhanced conductor from configuration file.
        
        Args:
            conductor_id: Unique conductor identifier
            conductor_name: Human-readable name
            vehicle_id: Assigned vehicle ID
            capacity: Vehicle passenger capacity (from database)
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
                # No hardcoded defaults - INI file must have all required values
                conductor_config.pickup_radius_km = float(conductor_section['pickup_radius_km'])  # Required
                conductor_config.boarding_time_window_minutes = float(conductor_section.get('boarding_time_window_minutes', 5.0))
                conductor_config.min_stop_duration_seconds = float(conductor_section.get('min_stop_duration_seconds', 15.0))
                conductor_config.max_stop_duration_seconds = float(conductor_section.get('max_stop_duration_seconds', 180.0))
                conductor_config.per_passenger_boarding_time = float(conductor_section.get('per_passenger_boarding_time', 8.0))
                conductor_config.per_passenger_disembarking_time = float(conductor_section.get('per_passenger_disembarking_time', 5.0))
                conductor_config.monitoring_interval_seconds = float(conductor_section.get('monitoring_interval_seconds', 2.0))
                conductor_config.driver_response_timeout_seconds = float(conductor_section.get('driver_response_timeout_seconds', 30.0))
                conductor_config.passenger_boarding_timeout_seconds = float(conductor_section.get('passenger_boarding_timeout_seconds', 120.0))
                
            return cls(
                conductor_id=conductor_id,
                conductor_name=conductor_name,
                vehicle_id=vehicle_id,
                capacity=capacity,  # Use provided capacity (from database)
                assigned_route_id=route_id,
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
        
        @self.sio.on('driver:arrived:waypoint')
        async def on_waypoint_arrival(data):
            """
            Handle waypoint arrival event from driver (Phase 3.2).
            Triggers passenger check at the waypoint location.
            """
            self.logger.info(f"[{self.component_id}] Driver arrived at waypoint: {data}")
            
            # Extract waypoint data
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            route_id = data.get('route_id')
            waypoint_index = data.get('waypoint_index')
            
            # Check if we have passenger database integration
            if self.passenger_db and latitude and longitude:
                try:
                    # Update conductor position for hardware events
                    self.update_position(latitude, longitude)
                    
                    # Check for passengers at this waypoint
                    self.logger.info(
                        f"[{self.component_id}] Checking for passengers at waypoint {waypoint_index} "
                        f"({latitude:.4f}, {longitude:.4f})"
                    )
                    
                    await self.check_for_passengers(
                        latitude=latitude,
                        longitude=longitude,
                        route_id=route_id or self.assigned_route_id,
                        radius_km=0.2  # 200 meters pickup radius
                    )
                    
                except Exception as e:
                    self.logger.error(f"Error checking for passengers at waypoint: {e}")
            else:
                self.logger.debug(
                    f"[{self.component_id}] Skipping passenger check "
                    "(no passenger_db or missing coordinates)"
                )
    
    def enable_auto_depart_on_full(self):
        """
        Enable automatic driver signal when vehicle becomes full.
        Wires on_full_callback to signal driver via Socket.IO.
        """
        def trigger_depart_signal():
            """Sync wrapper for async signal method"""
            # Schedule the async signal in the event loop
            if self._running:
                try:
                    # Try to get running loop (works if called from async context)
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(self._signal_driver_continue())
                except RuntimeError:
                    # Not in async context, try to schedule it
                    try:
                        loop = asyncio.get_event_loop()
                        asyncio.run_coroutine_threadsafe(
                            self._signal_driver_continue(),
                            loop
                        )
                    except Exception as e:
                        logger.error(
                            f"Conductor {self.vehicle_id}: Failed to signal driver - {e}"
                        )
            else:
                logger.warning(
                    f"Conductor {self.vehicle_id}: Vehicle full but cannot signal driver "
                    "(conductor not running)"
                )
        
        self.on_full_callback = trigger_depart_signal
        logger.info(f"Conductor {self.vehicle_id}: Auto-depart on full ENABLED")
    
    def disable_auto_depart_on_full(self):
        """Disable automatic driver signal when vehicle becomes full."""
        self.on_full_callback = None
        logger.info(f"Conductor {self.vehicle_id}: Auto-depart on full DISABLED")
            
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
            
            # Initialize commuter service HTTP client
            if self.commuter_client is None:
                from arknet_transit_simulator.services.commuter_http_client import CommuterServiceClient
                self.commuter_client = CommuterServiceClient(
                    base_url=self.commuter_service_url,
                    logger=self.logger
                )
                # Test connection
                connected = await self.commuter_client.connect()
                if connected:
                    self.logger.info(
                        f"[{self.component_id}] ✅ Connected to commuter_service at {self.commuter_service_url}"
                    )
                    
                    # Load depot coordinates for this route
                    if self.assigned_route_id and self.assigned_route_id != "UNKNOWN":
                        depot_loaded = await self.load_depot_coordinates(
                            route_id=self.assigned_route_id
                        )
                        if depot_loaded:
                            self.logger.info(
                                f"[{self.component_id}] 🏢 Depot coordinates loaded for route {self.assigned_route_id}"
                            )
                        else:
                            self.logger.warning(
                                f"[{self.component_id}] ⚠️ No depot found for route {self.assigned_route_id} - "
                                f"depot boarding mode will be unavailable"
                            )
                else:
                    self.logger.warning(
                        f"[{self.component_id}] ⚠️ Failed to connect to commuter_service - "
                        f"passenger visibility may be limited"
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
            
            # Disconnect commuter service HTTP client
            if self.commuter_client:
                try:
                    await self.commuter_client.disconnect()
                    self.logger.info(f"[{self.component_id}] Disconnected from commuter_service")
                except Exception as e:
                    self.logger.warning(f"[{self.component_id}] Error disconnecting commuter_client: {e}")
            
            # DEPRECATED: Disconnect PassengerDatabase (legacy)
            if self.passenger_db:
                try:
                    await self.passenger_db.disconnect()
                    self.logger.info(f"[{self.component_id}] Disconnected from PassengerDatabase")
                except Exception as e:
                    self.logger.warning(f"[{self.component_id}] Error disconnecting PassengerDatabase: {e}")
            
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
        """
        Update current vehicle GPS position for proximity calculations.
        
        Also checks if vehicle is at depot and triggers depot boarding mode if needed.
        """
        self.current_vehicle_position = (latitude, longitude)
        self.current_latitude = latitude
        self.current_longitude = longitude
        
        # If we have an active stop operation, preserve this position
        if self.current_stop_operation and not self.current_stop_operation.gps_position:
            self.current_stop_operation.gps_position = (latitude, longitude)
        
        # Check if at depot and auto-trigger depot boarding mode
        if self.depot_coordinates and not self.depot_boarding_active:
            at_depot = self.is_at_depot(latitude, longitude)
            
            if at_depot and self.assigned_route_id:
                # Vehicle just arrived at depot - enter depot boarding mode
                logger.info(
                    f"🔵 Conductor {self.vehicle_id}: 🏢 AUTO-TRIGGERING DEPOT BOARDING MODE\n"
                    f"   📍 Position: ({latitude:.6f}, {longitude:.6f})\n"
                    f"   🏢 Depot: {self.depot_coordinates.get('depot_name', 'Unknown')}"
                )
                
                # Create async task to run depot boarding (don't block position update)
                asyncio.create_task(
                    self.depot_boarding_mode(
                        vehicle_lat=latitude,
                        vehicle_lon=longitude,
                        route_id=self.assigned_route_id
                    )
                )

            
    async def _monitor_passengers(self) -> None:
        """Background task to monitor passengers and manage operations."""
        try:
            while self._running and self.conductor_state != ConductorState.WAITING_FOR_DEPARTURE:
                # Only check for passengers when boarding is explicitly active.
                # This prevents the conductor from immediately boarding all nearby
                # passengers as soon as the simulator starts and the driver/GPS
                # reports an initial position.
                if self.passenger_db and self.current_vehicle_position and self.boarding_active:
                    try:
                        lat, lon = self.current_vehicle_position
                        self.logger.info(
                            f"[{self.component_id}] Checking for passengers at position "
                            f"({lat:.6f}, {lon:.6f})"
                        )
                        await self.check_for_passengers(
                            vehicle_lat=lat,
                            vehicle_lon=lon,
                            route_id=self.assigned_route_id
                        )
                    except Exception as e:
                        self.logger.warning(f"[{self.component_id}] Error checking for passengers: {e}")
                elif self.passenger_db and not self.current_vehicle_position:
                    # Log why we're not checking
                    self.logger.warning(f"[{self.component_id}] No vehicle position available yet")
                elif self.passenger_db and self.current_vehicle_position and not self.boarding_active:
                    # Boarding not yet enabled - skip automatic boarding until explicitly enabled
                    self.logger.debug(f"[{self.component_id}] Boarding not active yet; skipping passenger checks")
                
                # Legacy: Query depot callback if configured
                elif self.depot_callback:
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
            f"🔵 Conductor {self.component_id} 🛑 SIGNALING DRIVER TO STOP:\n"
            f"   🚏 Stop ID: {self.current_stop_operation.stop_id}\n"
            f"   🚪 Boarding: {len(self.current_stop_operation.passengers_boarding)} passengers\n"
            f"   🚪 Disembarking: {len(self.current_stop_operation.passengers_disembarking)} passengers\n"
            f"   ⏱️  Duration: {self.current_stop_operation.requested_duration:.0f} seconds\n"
            f"   📍 Position: ({self.current_stop_operation.latitude:.6f}, {self.current_stop_operation.longitude:.6f})"
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
        
        try:
            # Prepare signal data (Socket.IO format)
            signal_data = {
                'vehicle_id': self.vehicle_id,
                'conductor_id': self.component_id,
                'passenger_count': self.passengers_on_board,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(
                f"🔵 Conductor {self.component_id} 🚀 SIGNALING DRIVER TO CONTINUE:\n"
                f"   💺 Passengers on board: {self.passengers_on_board}\n"
                f"   ⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # DEPOT MODE: Skip Socket.IO, use direct driver call
            # Socket.IO doesn't work reliably in depot mode - driver may not have handlers registered
            
            # Final fallback: Direct driver method call (Priority 1 in depot mode)
            self.logger.info(f"[{self.component_id}] Using direct driver.start_engine() call...")
            if hasattr(self, 'driver') and self.driver:
                self.logger.info(f"[{self.component_id}] ✅ Found driver reference")
                try:
                    result = await self.driver.start_engine()
                    self.logger.info(f"[{self.component_id}] ✅ Driver engine started via direct call (result={result})")
                    return  # Success
                except Exception as e:
                    self.logger.error(f"[{self.component_id}] Failed to start engine: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                self.logger.warning(f"[{self.component_id}] No driver reference found (hasattr={hasattr(self, 'driver')})")
            
            # No communication method available
            self.logger.error(f"[{self.component_id}] ⚠️⚠️⚠️ NO COMMUNICATION METHOD AVAILABLE TO SIGNAL DRIVER!")
        
        except Exception as e:
            self.logger.error(f"[{self.component_id}] CRITICAL ERROR in _signal_driver_continue: {e}")
            import traceback
            traceback.print_exc()
        
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
    
    async def board_passengers_by_id(self, passenger_ids: List[str]) -> int:
        """
        Board specific passengers onto vehicle (async with database updates + hardware events).
        
        This method:
        1. Updates passenger status in database (via PassengerDatabase)
        2. Emits hardware events (for real hardware or simulation logging)
        3. Tracks individual passenger IDs
        4. Signals driver when vehicle is full
        
        Args:
            passenger_ids: List of passenger IDs to board
            
        Returns:
            Number of passengers successfully boarded
        """
        if not passenger_ids:
            logger.debug(f"Conductor {self.vehicle_id}: No passenger IDs provided")
            return 0
        
        # Check capacity
        available_seats = self.capacity - self.passengers_on_board
        if len(passenger_ids) > available_seats:
            logger.warning(
                f"Conductor {self.vehicle_id}: Not enough seats - "
                f"{len(passenger_ids)} passengers, {available_seats} seats available"
            )
            # Take only what we can fit
            passenger_ids = passenger_ids[:available_seats]
        
        if not passenger_ids:
            return 0
        
        # Open doors (hardware event)
        if self.hardware_client:
            try:
                await self.hardware_client.door_event(
                    door_id="front",
                    action="opened",
                    latitude=self.current_latitude,
                    longitude=self.current_longitude
                )
            except Exception as e:
                logger.warning(f"Conductor {self.vehicle_id}: Door event failed: {e}")
        
        # Board each passenger
        boarded_count = 0
        for passenger_id in passenger_ids:
            try:
                # Update via CommuterServiceClient (HTTP API → Reservoir → Repository)
                if self.commuter_client:
                    success = await self.commuter_client.board_passenger(
                        passenger_id=passenger_id,
                        vehicle_id=self.vehicle_id
                    )
                    if not success:
                        logger.warning(f"Conductor {self.vehicle_id}: API boarding failed for {passenger_id}")
                        continue
                
                # FALLBACK: Direct database update (deprecated, for backward compatibility)
                elif self.passenger_db:
                    success = await self.passenger_db.mark_boarded(passenger_id, self.vehicle_id)
                    if not success:
                        logger.warning(f"Conductor {self.vehicle_id}: DB update failed for {passenger_id}")
                        continue
                
                # Emit hardware event (simulates RFID tap or manual confirmation)
                if self.hardware_client:
                    await self.hardware_client.rfid_tap(
                        card_id=passenger_id,
                        tap_type="board",
                        latitude=self.current_latitude,
                        longitude=self.current_longitude
                    )
                
                # Track locally
                self.boarded_passengers.append(passenger_id)
                boarded_count += 1
                
            except Exception as e:
                logger.error(f"Conductor {self.vehicle_id}: Error boarding {passenger_id}: {e}")
        
        # Update passenger count (hardware event for IR sensors)
        if self.hardware_client and boarded_count > 0:
            try:
                await self.hardware_client.update_passenger_count(
                    count_in=boarded_count,
                    count_out=0,
                    total_onboard=self.passengers_on_board + boarded_count
                )
            except Exception as e:
                logger.warning(f"Conductor {self.vehicle_id}: Count update event failed: {e}")
        
        # Update counts
        self.passengers_on_board += boarded_count
        self.seats_available = self.capacity - self.passengers_on_board
        
        logger.info(
            f"Conductor {self.vehicle_id}: Boarded {boarded_count} passengers "
            f"({self.passengers_on_board}/{self.capacity})"
        )
        
        # Close doors (hardware event)
        if self.hardware_client:
            try:
                await self.hardware_client.door_event(
                    door_id="front",
                    action="closed",
                    latitude=self.current_latitude,
                    longitude=self.current_longitude
                )
            except Exception as e:
                logger.warning(f"Conductor {self.vehicle_id}: Door event failed: {e}")
        
        # Check if full
        if self.is_full():
            logger.info(f"Conductor {self.vehicle_id}: VEHICLE FULL! Signaling driver to depart")
            if self.on_full_callback:
                self.on_full_callback()
        
        return boarded_count
    
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
    
    def update_position(self, latitude: float, longitude: float):
        """
        Update conductor's current position (called by driver/GPS).
        Needed for hardware event reporting.
        
        Args:
            latitude: Current vehicle latitude
            longitude: Current vehicle longitude
        """
        self.current_latitude = latitude
        self.current_longitude = longitude
    
    async def check_for_passengers(
        self,
        vehicle_lat: float,
        vehicle_lon: float,
        route_id: str = None
    ) -> int:
        """
        Check for eligible passengers at current location and board them.
        
        Uses CommuterServiceClient (HTTP API) → RouteReservoir → PassengerRepository:
        Conductor → HTTP API → RouteReservoir (with Redis cache) → Repository → Strapi
        
        Args:
            vehicle_lat: Current vehicle latitude
            vehicle_lon: Current vehicle longitude
            route_id: Route being served (defaults to assigned_route_id)
            
        Returns:
            Number of passengers boarded
        """
        if not self.commuter_client:
            logger.warning(f"Conductor {self.vehicle_id}: No commuter_service client configured")
            return 0
        
        if self.is_full():
            logger.debug(f"Conductor {self.vehicle_id}: Vehicle full, not checking for passengers")
            return 0
        
        route = route_id or self.assigned_route_id
        
        try:
            logger.info(
                f"🔵 Conductor {self.vehicle_id} 👁️  LOOKING FOR PASSENGERS (via CommuterService API):\n"
                f"   📍 Position: ({vehicle_lat:.6f}, {vehicle_lon:.6f})\n"
                f"   🚏 Route: {route}\n"
                f"   🔍 Pickup radius: {self.config.pickup_radius_km} km\n"
                f"   💺 Seats available: {self.seats_available}/{self.capacity}"
            )
            
            # Query passengers via HTTP API (goes through RouteReservoir)
            # Pass current time for spawn_time filtering (only "arrived" passengers)
            from datetime import datetime, timezone
            current_time_iso = datetime.now(timezone.utc).isoformat()
            
            eligible = await self.commuter_client.get_eligible_passengers(
                vehicle_lat=vehicle_lat,
                vehicle_lon=vehicle_lon,
                route_id=route,
                pickup_radius_km=self.config.pickup_radius_km,
                max_results=self.seats_available,
                status="WAITING",
                current_time=current_time_iso  # Filter by spawn_time
            )
            
            if not eligible:
                logger.info(f"🔵 Conductor {self.vehicle_id}: ❌ No passengers found at this location")
                return 0
            
            # Extract passenger IDs and log details
            passenger_ids = []
            logger.info(f"🔵 Conductor {self.vehicle_id}: ✅ Found {len(eligible)} eligible passengers:")
            
            for idx, p in enumerate(eligible, 1):
                # CommuterService API returns flat structure
                pid = p.get('passenger_id') or p.get('documentId')
                p_lat = p.get('latitude')
                p_lon = p.get('longitude')
                dest_lat = p.get('destination_lat')
                dest_lon = p.get('destination_lon')
                dist = p.get('distance_meters', 0)
                spawned_at = p.get('spawned_at')
                
                if pid:
                    passenger_ids.append(pid)
                    # Store destination for alighting logic
                    if dest_lat is not None and dest_lon is not None:
                        self.passenger_destinations[pid] = (dest_lat, dest_lon)
                    
                    logger.info(
                        f"   {idx}. 🟢 Passenger {pid}\n"
                        f"      📍 Position: ({p_lat:.6f}, {p_lon:.6f})\n"
                        f"      📏 Distance: {dist:.1f} meters\n"
                        f"      🎯 Destination: ({dest_lat:.6f}, {dest_lon:.6f})\n"
                        f"      ⏰ Spawned at: {spawned_at}"
                    )
            
            if not passenger_ids:
                logger.warning(f"🔵 Conductor {self.vehicle_id}: ⚠️  Found passengers but couldn't extract IDs")
                return 0
            
            # Limit to available seats
            if len(passenger_ids) > self.seats_available:
                logger.info(f"🔵 Conductor {self.vehicle_id}: ⚠️  More passengers ({len(passenger_ids)}) than seats ({self.seats_available}), taking first {self.seats_available}")
                passenger_ids = passenger_ids[:self.seats_available]
            
            logger.info(
                f"🔵 Conductor {self.vehicle_id}: 🚪 BOARDING {len(passenger_ids)} passengers..."
            )
            
            # Board them
            boarded = await self.board_passengers_by_id(passenger_ids)
            
            if boarded > 0:
                logger.info(
                    f"🔵 Conductor {self.vehicle_id}: ✅ Successfully boarded {boarded} passengers\n"
                    f"   💺 Current occupancy: {self.passengers_on_board}/{self.capacity}\n"
                    f"   💺 Seats remaining: {self.seats_available}"
                )
            
            return boarded
            
        except Exception as e:
            logger.error(f"Conductor {self.vehicle_id}: Error checking for passengers: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    async def load_depot_coordinates(self, route_id: str, strapi_url: str = "http://localhost:1337") -> bool:
        """
        Load and cache depot coordinates for the given route.
        
        Queries route-depots junction table for start terminus depot.
        This only needs to be called once per route assignment.
        
        Args:
            route_id: Route ID (short_name)
            strapi_url: Strapi base URL
        
        Returns:
            True if depot coordinates loaded successfully
        """
        if not self.commuter_client:
            logger.warning(f"Conductor {self.vehicle_id}: Cannot load depot - commuter client not initialized")
            return False
        
        try:
            self.depot_coordinates = await self.commuter_client.get_route_depot_coordinates(
                route_id=route_id,
                strapi_url=strapi_url
            )
            
            if self.depot_coordinates:
                logger.info(
                    f"🔵 Conductor {self.vehicle_id}: 📍 Loaded depot for route {route_id}:\n"
                    f"   🏢 Depot: {self.depot_coordinates.get('depot_name', 'Unknown')}\n"
                    f"   📍 Location: ({self.depot_coordinates['latitude']:.6f}, {self.depot_coordinates['longitude']:.6f})"
                )
                return True
            else:
                logger.warning(f"Conductor {self.vehicle_id}: No depot found for route {route_id}")
                return False
                
        except Exception as e:
            logger.error(f"Conductor {self.vehicle_id}: Error loading depot coordinates: {e}")
            return False
    
    def is_at_depot(self, vehicle_lat: float, vehicle_lon: float) -> bool:
        """
        Check if vehicle is currently at depot (within proximity threshold).
        
        Uses haversine distance and depot_proximity_threshold_km from config.
        Caches result in self.is_at_depot_flag for state tracking.
        
        Args:
            vehicle_lat: Current vehicle latitude
            vehicle_lon: Current vehicle longitude
        
        Returns:
            True if within depot proximity threshold
        """
        if not self.depot_coordinates:
            return False
        
        from arknet_transit_simulator.utils.geospatial import haversine
        
        depot_lat = self.depot_coordinates['latitude']
        depot_lon = self.depot_coordinates['longitude']
        
        distance_km = haversine(vehicle_lat, vehicle_lon, depot_lat, depot_lon)
        
        is_at_depot = distance_km <= self.config.depot_proximity_threshold_km
        
        # Log state changes
        if is_at_depot != self.is_at_depot_flag:
            if is_at_depot:
                logger.info(
                    f"🔵 Conductor {self.vehicle_id}: 🏢 ARRIVED AT DEPOT\n"
                    f"   📍 Depot: {self.depot_coordinates.get('depot_name', 'Unknown')}\n"
                    f"   📏 Distance: {distance_km*1000:.1f} meters (threshold: {self.config.depot_proximity_threshold_km*1000:.0f}m)"
                )
            else:
                logger.info(
                    f"🔵 Conductor {self.vehicle_id}: 🚦 DEPARTED DEPOT\n"
                    f"   📏 Distance: {distance_km*1000:.1f} meters from depot"
                )
            
            self.is_at_depot_flag = is_at_depot
        
        return is_at_depot
    
    async def depot_boarding_mode(
        self,
        vehicle_lat: float,
        vehicle_lon: float,
        route_id: str
    ) -> int:
        """
        Enter depot boarding wait mode.
        
        Waits at depot for passengers to board, with timeout and capacity limits:
        - Query passengers every monitoring_interval_seconds
        - Filter by spawned_at <= current_time (only "arrived" passengers)
        - Depart when: (seats full) OR (timeout = depot_wait_time_minutes)
        
        Args:
            vehicle_lat: Depot latitude
            vehicle_lon: Depot longitude
            route_id: Current route ID
        
        Returns:
            Total passengers boarded during depot wait
        """
        import asyncio
        from datetime import datetime, timezone, timedelta
        
        logger.info(
            f"🔵 Conductor {self.vehicle_id}: 🏢 ENTERING DEPOT BOARDING MODE\n"
            f"   ⏱️  Wait timeout: {self.config.depot_wait_time_minutes} minutes\n"
            f"   💺 Capacity: {self.capacity} seats\n"
            f"   🔄 Check interval: {self.config.monitoring_interval_seconds} seconds"
        )
        
        self.depot_boarding_active = True
        start_time = datetime.now(timezone.utc)
        timeout_minutes = self.config.depot_wait_time_minutes
        total_boarded = 0
        
        try:
            while self.depot_boarding_active:
                # Check timeout
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() / 60.0
                
                if elapsed >= timeout_minutes:
                    logger.info(
                        f"🔵 Conductor {self.vehicle_id}: ⏰ DEPOT WAIT TIMEOUT\n"
                        f"   ⏱️  Elapsed: {elapsed:.1f} minutes (limit: {timeout_minutes} min)\n"
                        f"   👥 Boarded: {total_boarded} passengers\n"
                        f"   💺 Occupancy: {self.passengers_on_board}/{self.capacity}"
                    )
                    break
                
                # Check if full
                if self.seats_available == 0:
                    logger.info(
                        f"🔵 Conductor {self.vehicle_id}: ✅ VEHICLE FULL AT DEPOT\n"
                        f"   👥 Boarded: {total_boarded} passengers\n"
                        f"   💺 Occupancy: {self.passengers_on_board}/{self.capacity}\n"
                        f"   ⏱️  Time at depot: {elapsed:.1f} minutes"
                    )
                    break
                
                # Check for passengers (with spawn_time filtering)
                boarded_this_round = await self.check_for_passengers(
                    vehicle_lat=vehicle_lat,
                    vehicle_lon=vehicle_lon,
                    route_id=route_id
                )
                
                if boarded_this_round > 0:
                    total_boarded += boarded_this_round
                    logger.info(
                        f"🔵 Conductor {self.vehicle_id}: ➕ Boarded {boarded_this_round} more passengers\n"
                        f"   👥 Total at depot: {total_boarded}\n"
                        f"   💺 Seats remaining: {self.seats_available}/{self.capacity}\n"
                        f"   ⏱️  Elapsed: {elapsed:.1f}/{timeout_minutes} min"
                    )
                
                # Wait before next check
                await asyncio.sleep(self.config.monitoring_interval_seconds)
            
            logger.info(
                f"🔵 Conductor {self.vehicle_id}: 🚦 EXITING DEPOT BOARDING MODE\n"
                f"   👥 Total boarded: {total_boarded} passengers\n"
                f"   💺 Final occupancy: {self.passengers_on_board}/{self.capacity}\n"
                f"   ⏱️  Total time: {((datetime.now(timezone.utc) - start_time).total_seconds() / 60.0):.1f} min"
            )
            
            return total_boarded
            
        except Exception as e:
            logger.error(f"Conductor {self.vehicle_id}: Error in depot boarding mode: {e}")
            import traceback
            traceback.print_exc()
            return total_boarded
        
        finally:
            self.depot_boarding_active = False
        
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
        logger.info(
            f"🔵 Conductor {self.vehicle_id}: 🚪 BOARDING ENABLED\n"
            f"   💺 Seats available: {self.seats_available}/{self.capacity}\n"
            f"   🔍 Will check for passengers at waypoints"
        )
        
    def stop_boarding(self):
        """Stop accepting passengers"""
        self.boarding_active = False
        logger.info(f"🔵 Conductor {self.vehicle_id}: 🚫 BOARDING DISABLED")
        
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