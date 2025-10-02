"""
Base Commuter Reservoir

Abstract base class for commuter reservoir implementations.
Provides shared functionality for depot and route reservoirs.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import uuid
from math import radians, sin, cos, sqrt, atan2

from commuter_service.socketio_client import (
    SocketIOClient,
    EventTypes,
    ServiceType,
    CommuterDirection,
)
from commuter_service.location_aware_commuter import LocationAwareCommuter
from commuter_service.commuter_config import CommuterBehaviorConfig, CommuterConfigLoader
from commuter_service.reservoir_config import ReservoirConfig, get_reservoir_config


class BaseCommuterReservoir(ABC):
    """
    Abstract base class for commuter reservoirs.
    
    Provides:
    - Socket.IO client management
    - Distance calculations
    - Commuter lifecycle tracking
    - Statistics gathering
    - Expiration checking
    - Event emission
    """
    
    def __init__(
        self,
        socketio_url: Optional[str] = None,
        commuter_config: Optional[CommuterBehaviorConfig] = None,
        reservoir_config: Optional[ReservoirConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize base reservoir
        
        Args:
            socketio_url: Socket.IO server URL (overrides config)
            commuter_config: Commuter behavior configuration
            reservoir_config: Reservoir operational configuration
            logger: Logger instance
        """
        # Configurations
        self.reservoir_config = reservoir_config or get_reservoir_config()
        self.commuter_config = commuter_config or CommuterConfigLoader.get_default_config()
        
        # Override socketio_url if provided
        if socketio_url:
            self.reservoir_config.socketio_url = socketio_url
        
        # Logging
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # Socket.IO client (to be initialized by subclass)
        self.socketio_client: Optional[SocketIOClient] = None
        
        # Active commuters tracking
        self.active_commuters: Dict[str, LocationAwareCommuter] = {}
        
        # Statistics
        self.stats = {
            "total_spawned": 0,
            "total_picked_up": 0,
            "total_expired": 0,
            "start_time": None,
        }
        
        # Background tasks
        self._expiration_task: Optional[asyncio.Task] = None
        self._running = False
    
    @abstractmethod
    async def _initialize_socketio_client(self) -> SocketIOClient:
        """Initialize Socket.IO client (implemented by subclass)"""
        pass
    
    @abstractmethod
    async def spawn_commuter(self, **kwargs) -> LocationAwareCommuter:
        """Spawn a new commuter (implemented by subclass)"""
        pass
    
    @abstractmethod
    def _find_expired_commuters(self) -> List[str]:
        """Find expired commuter IDs (implemented by subclass)"""
        pass
    
    @abstractmethod
    def _remove_commuter_internal(self, commuter_id: str) -> bool:
        """Remove commuter from internal structures (implemented by subclass)"""
        pass
    
    async def start(self):
        """Start the reservoir service"""
        self.logger.info(f"Starting {self.__class__.__name__} service...")
        
        # Initialize Socket.IO client
        self.socketio_client = await self._initialize_socketio_client()
        await self.socketio_client.connect()
        
        # Start expiration loop
        self._running = True
        self._expiration_task = asyncio.create_task(self._expiration_loop())
        
        # Record start time
        self.stats["start_time"] = datetime.now()
        
        self.logger.info(f"{self.__class__.__name__} service started successfully")
    
    async def stop(self):
        """Stop the reservoir service"""
        self.logger.info(f"Stopping {self.__class__.__name__} service...")
        
        # Stop expiration loop
        self._running = False
        if self._expiration_task:
            self._expiration_task.cancel()
            try:
                await self._expiration_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect Socket.IO
        if self.socketio_client:
            await self.socketio_client.disconnect()
        
        self.logger.info(f"{self.__class__.__name__} service stopped")
    
    def calculate_distance(
        self,
        loc1: tuple[float, float],
        loc2: tuple[float, float]
    ) -> float:
        """
        Calculate Haversine distance between two points
        
        Args:
            loc1: (lat, lon) tuple
            loc2: (lat, lon) tuple
        
        Returns:
            Distance in meters
        """
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        
        R = self.reservoir_config.earth_radius_meters
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def is_commuter_within_range(
        self,
        commuter: LocationAwareCommuter,
        vehicle_location: tuple[float, float],
        max_distance: float
    ) -> bool:
        """
        Check if commuter is within pickup range of vehicle
        
        Args:
            commuter: Commuter to check
            vehicle_location: Vehicle GPS coordinates
            max_distance: Maximum distance in meters
        
        Returns:
            True if within range
        """
        distance = self.calculate_distance(
            commuter.current_position,
            vehicle_location
        )
        return distance <= max_distance
    
    async def mark_picked_up(self, commuter_id: str) -> bool:
        """
        Mark commuter as picked up and remove from reservoir
        
        Args:
            commuter_id: ID of commuter being picked up
        
        Returns:
            True if successfully removed
        """
        if commuter_id not in self.active_commuters:
            self.logger.warning(f"Commuter {commuter_id} not found for pickup")
            return False
        
        # Remove from active tracking
        commuter = self.active_commuters.pop(commuter_id)
        
        # Remove from internal structures
        if not self._remove_commuter_internal(commuter_id):
            self.logger.error(f"Failed to remove {commuter_id} from internal structures")
            return False
        
        # Update stats
        self.stats["total_picked_up"] += 1
        
        # Emit event
        if self.reservoir_config.enable_socketio_events and self.socketio_client:
            await self.socketio_client.emit_message(
                EventTypes.COMMUTER_PICKED_UP,
                {
                    "commuter_id": commuter_id,
                    "pickup_time": datetime.now().isoformat(),
                    "wait_time_seconds": (datetime.now() - commuter.spawn_time).total_seconds()
                }
            )
        
        self.logger.debug(f"Marked commuter {commuter_id} as picked up")
        return True
    
    async def _expiration_loop(self):
        """Background task to expire old commuters"""
        self.logger.info("Starting expiration loop...")
        
        max_wait = timedelta(minutes=self.reservoir_config.commuter_max_wait_time_minutes)
        check_interval = self.reservoir_config.expiration_check_interval_seconds
        
        while self._running:
            try:
                await asyncio.sleep(check_interval)
                
                # Find expired commuters
                expired_ids = self._find_expired_commuters()
                
                # Remove each expired commuter
                for commuter_id in expired_ids:
                    if commuter_id in self.active_commuters:
                        commuter = self.active_commuters.pop(commuter_id)
                        self._remove_commuter_internal(commuter_id)
                        self.stats["total_expired"] += 1
                        
                        self.logger.debug(f"Expired commuter {commuter_id}")
                        
                        # Emit expiration event
                        if self.reservoir_config.enable_socketio_events and self.socketio_client:
                            await self.socketio_client.emit_message(
                                EventTypes.COMMUTER_EXPIRED,
                                {
                                    "commuter_id": commuter_id,
                                    "spawn_time": commuter.spawn_time.isoformat(),
                                    "expiration_time": datetime.now().isoformat(),
                                }
                            )
                
                if expired_ids:
                    self.logger.info(f"Expired {len(expired_ids)} commuters")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in expiration loop: {e}")
        
        self.logger.info("Expiration loop stopped")
    
    def get_stats(self) -> Dict:
        """
        Get reservoir statistics
        
        Returns:
            Dictionary of statistics
        """
        uptime = 0
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        base_stats = {
            "total_active_commuters": len(self.active_commuters),
            "total_spawned": self.stats["total_spawned"],
            "total_picked_up": self.stats["total_picked_up"],
            "total_expired": self.stats["total_expired"],
            "uptime_seconds": uptime,
            "service_type": self.__class__.__name__,
        }
        
        return base_stats
    
    def _generate_commuter_id(self) -> str:
        """Generate unique commuter ID"""
        return f"COM_{uuid.uuid4().hex[:8].upper()}"
