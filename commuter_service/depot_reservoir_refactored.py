"""
Depot Reservoir - Outbound Commuter Management

This module manages outbound commuters waiting at depot locations.
Commuters spawn at depots and wait in a queue for vehicles to arrive.

Features:
- FIFO queue management for outbound commuters
- Proximity-based commuter queries for vehicles
- Real-time commuter spawning and expiration
- Socket.IO integration for event notifications
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

from commuter_service.socketio_client import (
    SocketIOClient,
    EventTypes,
    ServiceType,
    create_depot_client,
    CommuterDirection,
)
from commuter_service.location_aware_commuter import LocationAwareCommuter
from commuter_service.commuter_config import CommuterBehaviorConfig
from commuter_service.reservoir_config import ReservoirConfig
from commuter_service.base_reservoir import BaseCommuterReservoir


@dataclass
class DepotQueue:
    """Queue of commuters waiting at a specific depot"""
    depot_id: str
    depot_location: Tuple[float, float]  # (lat, lon)
    route_id: str
    commuters: deque = field(default_factory=deque)
    total_spawned: int = 0
    total_picked_up: int = 0
    total_expired: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __len__(self) -> int:
        return len(self.commuters)
    
    def add_commuter(self, commuter: LocationAwareCommuter):
        """Add commuter to end of queue (FIFO)"""
        self.commuters.append(commuter)
        self.total_spawned += 1
    
    def remove_commuter(self, commuter_id: str) -> Optional[LocationAwareCommuter]:
        """Remove specific commuter from queue"""
        for i, commuter in enumerate(self.commuters):
            if commuter.commuter_id == commuter_id:
                removed = self.commuters[i]
                del self.commuters[i]
                return removed
        return None
    
    def get_available_commuters(
        self,
        vehicle_location: Tuple[float, float],
        max_distance: float,
        max_count: int,
        distance_calculator
    ) -> List[LocationAwareCommuter]:
        """Get available commuters within distance threshold"""
        available = []
        
        for commuter in self.commuters:
            distance = distance_calculator(commuter.current_position, vehicle_location)
            
            if distance <= max_distance:
                available.append(commuter)
                if len(available) >= max_count:
                    break
        
        return available
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            "depot_id": self.depot_id,
            "route_id": self.route_id,
            "waiting_count": len(self.commuters),
            "total_spawned": self.total_spawned,
            "total_picked_up": self.total_picked_up,
            "total_expired": self.total_expired,
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
        }


class DepotReservoir(BaseCommuterReservoir):
    """
    Depot Reservoir manages outbound commuters waiting at depot locations.
    
    Architecture:
    - One queue per depot-route combination
    - FIFO queue ordering
    - Proximity-based vehicle queries
    - Socket.IO event integration
    - Automatic commuter expiration
    
    Usage:
        reservoir = DepotReservoir()
        await reservoir.start()
        
        # Spawn commuter at depot
        commuter = await reservoir.spawn_commuter(
            depot_id="DEPOT_001",
            route_id="ROUTE_A",
            depot_location=(40.7128, -74.0060),
            destination=(40.7589, -73.9851)
        )
        
        # Vehicle queries for commuters
        commuters = reservoir.query_commuters_sync(
            depot_id="DEPOT_001",
            route_id="ROUTE_A",
            vehicle_location=(40.7128, -74.0060),
            max_distance=500,
            max_count=30
        )
    """
    
    def __init__(
        self,
        socketio_url: Optional[str] = None,
        commuter_config: Optional[CommuterBehaviorConfig] = None,
        reservoir_config: Optional[ReservoirConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        super().__init__(socketio_url, commuter_config, reservoir_config, logger)
        
        # Depot queues: {(depot_id, route_id): DepotQueue}
        self.queues: Dict[Tuple[str, str], DepotQueue] = {}
        
        # Setup Socket.IO event handlers
        self._setup_event_handlers()
    
    async def _initialize_socketio_client(self) -> SocketIOClient:
        """Initialize Socket.IO client for depot reservoir"""
        return create_depot_client(self.reservoir_config.socketio_url)
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers (deferred until client is created)"""
        pass  # Handlers will be registered after connection
    
    def _get_or_create_queue(
        self,
        depot_id: str,
        route_id: str,
        depot_location: Tuple[float, float]
    ) -> DepotQueue:
        """Get existing queue or create new one"""
        key = (depot_id, route_id)
        
        if key not in self.queues:
            self.queues[key] = DepotQueue(
                depot_id=depot_id,
                route_id=route_id,
                depot_location=depot_location
            )
            self.logger.info(f"Created new depot queue: {depot_id} -> {route_id}")
        
        return self.queues[key]
    
    async def spawn_commuter(
        self,
        depot_id: str,
        route_id: str,
        depot_location: Tuple[float, float],
        destination: Tuple[float, float],
        priority: float = 0.5
    ) -> LocationAwareCommuter:
        """
        Spawn a new commuter at depot location
        
        Args:
            depot_id: Depot identifier
            route_id: Route the commuter wants to board
            depot_location: Depot GPS coordinates (lat, lon)
            destination: Destination GPS coordinates (lat, lon)
            priority: Priority level (0.0-1.0)
        
        Returns:
            LocationAwareCommuter instance
        """
        # Get or create queue
        queue = self._get_or_create_queue(depot_id, route_id, depot_location)
        
        # Create commuter
        person_id = self._generate_commuter_id()
        commuter = LocationAwareCommuter(
            person_id=person_id,
            person_name=None,
            spawn_location=depot_location,
            destination_location=destination,
            trip_purpose="commute",
            priority=priority,
            config=self.commuter_config
        )
        
        # Store additional metadata
        commuter.commuter_id = person_id
        commuter.direction = CommuterDirection.OUTBOUND
        commuter.spawn_time = datetime.now()
        
        # Add to queue
        queue.add_commuter(commuter)
        self.active_commuters[commuter.commuter_id] = commuter
        self.stats["total_spawned"] += 1
        
        # Emit spawn event
        if self.reservoir_config.enable_socketio_events and self.socketio_client:
            await self.socketio_client.emit_message(
                EventTypes.COMMUTER_SPAWNED,
                {
                    "commuter_id": commuter.commuter_id,
                    "depot_id": depot_id,
                    "route_id": route_id,
                    "location": {
                        "lat": depot_location[0],
                        "lon": depot_location[1]
                    },
                    "destination": {
                        "lat": destination[0],
                        "lon": destination[1]
                    },
                    "direction": CommuterDirection.OUTBOUND.value,
                    "priority": priority,
                    "max_walking_distance": commuter.max_walking_distance_m,
                    "spawn_time": commuter.spawn_time.isoformat(),
                }
            )
        
        self.logger.debug(
            f"Spawned commuter {commuter.commuter_id} at depot {depot_id}"
        )
        
        return commuter
    
    def query_commuters_sync(
        self,
        depot_id: str,
        route_id: str,
        vehicle_location: Tuple[float, float],
        max_distance: Optional[float] = None,
        max_count: Optional[int] = None
    ) -> List[LocationAwareCommuter]:
        """
        Synchronously query available commuters at depot
        
        Args:
            depot_id: Depot identifier
            route_id: Route identifier
            vehicle_location: Vehicle GPS coordinates (lat, lon)
            max_distance: Maximum pickup distance in meters
            max_count: Maximum number of commuters to return
        
        Returns:
            List of available LocationAwareCommuter instances
        """
        # Use config defaults if not specified
        if max_distance is None:
            max_distance = self.reservoir_config.default_pickup_distance_meters
        if max_count is None:
            max_count = self.reservoir_config.max_commuters_per_query
        
        key = (depot_id, route_id)
        
        if key not in self.queues:
            return []
        
        queue = self.queues[key]
        return queue.get_available_commuters(
            vehicle_location,
            max_distance,
            max_count,
            self.calculate_distance
        )
    
    def _remove_commuter_internal(self, commuter_id: str) -> bool:
        """Remove commuter from queue structures"""
        for queue in self.queues.values():
            removed = queue.remove_commuter(commuter_id)
            if removed:
                return True
        return False
    
    def _find_expired_commuters(self) -> List[str]:
        """Find commuters that have waited too long"""
        expired = []
        max_wait = timedelta(minutes=self.reservoir_config.commuter_max_wait_time_minutes)
        now = datetime.now()
        
        for commuter_id, commuter in self.active_commuters.items():
            if (now - commuter.spawn_time) > max_wait:
                expired.append(commuter_id)
        
        return expired
    
    def get_stats(self) -> Dict:
        """Get depot reservoir statistics"""
        base_stats = super().get_stats()
        
        # Add depot-specific stats
        base_stats.update({
            "total_queues": len(self.queues),
            "queues": [queue.get_stats() for queue in self.queues.values()]
        })
        
        return base_stats
