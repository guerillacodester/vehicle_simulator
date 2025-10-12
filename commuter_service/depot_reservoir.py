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
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import uuid

from commuter_service.socketio_client import (
    SocketIOClient,
    EventTypes,
    ServiceType,
    create_depot_client,
    CommuterDirection,
)
from commuter_service.location_aware_commuter import LocationAwareCommuter
from commuter_service.commuter_config import CommuterBehaviorConfig, CommuterConfigLoader
from commuter_service.passenger_db import PassengerDatabase


@dataclass
class DepotQueue:
    """Queue of commuters waiting at a specific depot"""
    depot_id: str
    depot_location: tuple[float, float]  # (lat, lon)
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
        vehicle_location: tuple[float, float],
        max_distance: float,
        max_count: int
    ) -> List[LocationAwareCommuter]:
        """Get available commuters within distance threshold"""
        available = []
        
        for commuter in self.commuters:
            # Calculate distance between commuter and vehicle
            from math import radians, sin, cos, sqrt, atan2
            lat1, lon1 = commuter.current_position
            lat2, lon2 = vehicle_location
            
            # Haversine distance
            R = 6371000  # Earth radius in meters
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
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


class DepotReservoir:
    """
    Depot Reservoir manages outbound commuters waiting at depot locations.
    
    Architecture:
    - One queue per depot-route combination
    - FIFO queue ordering
    - Proximity-based vehicle queries
    - Socket.IO event integration
    - Automatic commuter expiration
    
    Usage:
        reservoir = DepotReservoir(socketio_url="http://localhost:1337")
        await reservoir.start()
        
        # Spawn commuter at depot
        commuter = await reservoir.spawn_commuter(
            depot_id="DEPOT_001",
            route_id="ROUTE_A",
            destination=(40.7589, -73.9851)
        )
        
        # Vehicle queries for commuters
        commuters = await reservoir.query_commuters(
            depot_id="DEPOT_001",
            route_id="ROUTE_A",
            vehicle_location=(40.7128, -74.0060),
            max_distance=500,
            max_count=30
        )
    """
    
    def __init__(
        self,
        socketio_url: str = "http://localhost:1337",
        config: Optional[CommuterBehaviorConfig] = None,
        logger: Optional[logging.Logger] = None,
        strapi_url: Optional[str] = None
    ):
        self.socketio_url = socketio_url
        self.config = config or CommuterConfigLoader.get_default_config()
        self.logger = logger or logging.getLogger(__name__)
        
        # Depot queues: {(depot_id, route_id): DepotQueue}
        self.queues: Dict[tuple[str, str], DepotQueue] = {}
        
        # Socket.IO client
        self.client: Optional[SocketIOClient] = None
        
        # Database client for passenger persistence
        self.db = PassengerDatabase(strapi_url)
        
        # Active commuters for quick lookup
        self.active_commuters: Dict[str, LocationAwareCommuter] = {}
        
        # Background tasks
        self.running = False
        self.expiration_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "total_spawned": 0,
            "total_picked_up": 0,
            "total_expired": 0,
            "start_time": None,
        }
    
    async def start(self):
        """Start the depot reservoir service"""
        if self.running:
            self.logger.warning("Depot reservoir already running")
            return
        
        self.logger.info("Starting depot reservoir service...")
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # Connect to database
        await self.db.connect()
        
        # Connect to Socket.IO
        self.client = create_depot_client(
            url=self.socketio_url,
            service_type=ServiceType.COMMUTER_SERVICE
        )
        
        # Register event handlers
        self._register_handlers()
        
        # Connect to Socket.IO hub
        await self.client.connect()
        
        # Log startup statistics
        self.logger.info("=" * 80)
        self.logger.info("📊 DEPOT RESERVOIR - INITIALIZATION COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"🏢 Active Depots: {len(self.queues)}")
        for (depot_id, route_id), queue in self.queues.items():
            self.logger.info(
                f"   • {depot_id} @ ({queue.depot_location[0]:.4f}, {queue.depot_location[1]:.4f}) - Route: {route_id}"
            )
        self.logger.info("=" * 80)
        
        # Start background tasks
        self.expiration_task = asyncio.create_task(self._expiration_loop())
        
        self.logger.info("Depot reservoir service started successfully")
    
    async def stop(self):
        """Stop the depot reservoir service"""
        if not self.running:
            return
        
        self.logger.info("Stopping depot reservoir service...")
        self.running = False
        
        # Stop background tasks
        if self.expiration_task:
            self.expiration_task.cancel()
            try:
                await self.expiration_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect from database
        await self.db.disconnect()
        
        # Disconnect from Socket.IO
        if self.client:
            await self.client.disconnect()
        
        self.logger.info("Depot reservoir service stopped")
    
    def _register_handlers(self):
        """Register Socket.IO event handlers"""
        
        async def handle_vehicle_query(message: Dict):
            """Handle vehicle query for commuters"""
            data = message.get("data", {})
            
            depot_id = data.get("depot_id")
            route_id = data.get("route_id")
            vehicle_location = data.get("vehicle_location", {})
            vehicle_lat = vehicle_location.get("lat")
            vehicle_lon = vehicle_location.get("lon")
            max_distance = data.get("search_radius", 1000)
            max_count = data.get("available_seats", 30)
            
            if not all([depot_id, route_id, vehicle_lat, vehicle_lon]):
                self.logger.warning(f"Invalid vehicle query: {data}")
                return
            
            # Query commuters
            commuters = self.query_commuters_sync(
                depot_id=depot_id,
                route_id=route_id,
                vehicle_location=(vehicle_lat, vehicle_lon),
                max_distance=max_distance,
                max_count=max_count
            )
            
            # Send response
            await self._send_query_response(
                commuters,
                message.get("correlationId"),
                message.get("source")
            )
        
        async def handle_pickup_notification(message: Dict):
            """Handle commuter pickup notification"""
            data = message.get("data", {})
            commuter_id = data.get("commuter_id")
            
            if commuter_id:
                await self.mark_picked_up(commuter_id)
        
        self.client.on(EventTypes.QUERY_COMMUTERS, handle_vehicle_query)
        self.client.on(EventTypes.COMMUTER_PICKED_UP, handle_pickup_notification)
    
    def _get_or_create_queue(
        self,
        depot_id: str,
        route_id: str,
        depot_location: tuple[float, float]
    ) -> DepotQueue:
        """Get existing queue or create new one"""
        key = (depot_id, route_id)
        
        if key not in self.queues:
            self.queues[key] = DepotQueue(
                depot_id=depot_id,
                depot_location=depot_location,
                route_id=route_id
            )
            self.logger.info(f"Created new depot queue: {depot_id} -> {route_id}")
        
        return self.queues[key]
    
    async def spawn_commuter(
        self,
        depot_id: str,
        route_id: str,
        depot_location: tuple[float, float],
        destination: tuple[float, float],
        priority: int = 3,
        max_wait_time: Optional[timedelta] = None
    ) -> LocationAwareCommuter:
        """
        Spawn a new commuter at the depot
        
        Args:
            depot_id: Depot identifier
            route_id: Route identifier
            depot_location: (lat, lon) of depot
            destination: (lat, lon) of destination
            priority: Priority level (1=highest, 5=lowest)
            max_wait_time: Maximum wait time before expiration
        
        Returns:
            LocationAwareCommuter instance
        """
        # Get or create queue
        queue = self._get_or_create_queue(depot_id, route_id, depot_location)
        
        # Create commuter
        person_id = f"COM_{uuid.uuid4().hex[:8].upper()}"
        commuter = LocationAwareCommuter(
            person_id=person_id,
            person_name=None,
            spawn_location=depot_location,
            destination_location=destination,
            trip_purpose="commute",
            priority=priority,
            config=self.config
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
        if self.client:
            await self.client.emit_message(
                EventTypes.COMMUTER_SPAWNED,
                {
                    "commuter_id": commuter.commuter_id,
                    "depot_id": depot_id,
                    "route_id": route_id,
                    "current_location": {
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
        
        # Persist to database
        await self.db.insert_passenger(
            passenger_id=commuter.commuter_id,
            route_id=route_id,
            latitude=depot_location[0],
            longitude=depot_location[1],
            destination_lat=destination[0],
            destination_lon=destination[1],
            destination_name="Destination",
            depot_id=depot_id,
            direction="OUTBOUND",
            priority=priority,
            expires_minutes=max_wait_time.total_seconds() / 60 if max_wait_time else 30
        )
        
        # Log spawn details
        self.logger.info(
            f"✅ DEPOT SPAWN #{self.stats['total_spawned']} | "
            f"ID: {commuter.commuter_id} | "
            f"Depot: {depot_id} @ ({depot_location[0]:.4f}, {depot_location[1]:.4f}) | "
            f"Route: {route_id} | "
            f"Dest: ({destination[0]:.4f}, {destination[1]:.4f}) | "
            f"Priority: {priority} | "
            f"Queue: {len(queue.commuters)} waiting"
        )
        
        return commuter
    
    def query_commuters_sync(
        self,
        depot_id: str,
        route_id: str,
        vehicle_location: tuple[float, float],
        max_distance: float = 1000,
        max_count: int = 30
    ) -> List[LocationAwareCommuter]:
        """
        Query commuters available for pickup (synchronous version)
        
        Args:
            depot_id: Depot identifier
            route_id: Route identifier
            vehicle_location: (lat, lon) of vehicle
            max_distance: Maximum distance in meters
            max_count: Maximum number of commuters
        
        Returns:
            List of available commuters
        """
        key = (depot_id, route_id)
        
        if key not in self.queues:
            return []
        
        queue = self.queues[key]
        return queue.get_available_commuters(vehicle_location, max_distance, max_count)
    
    async def mark_picked_up(self, commuter_id: str) -> bool:
        """
        Mark commuter as picked up and remove from queue
        
        Args:
            commuter_id: Commuter identifier
        
        Returns:
            True if commuter was found and removed
        """
        if commuter_id not in self.active_commuters:
            return False
        
        commuter = self.active_commuters.pop(commuter_id)
        
        # Find and remove from queue
        for queue in self.queues.values():
            removed = queue.remove_commuter(commuter_id)
            if removed:
                queue.total_picked_up += 1
                self.stats["total_picked_up"] += 1
                
                # Update database status
                await self.db.mark_boarded(commuter_id)
                
                # Emit pickup event
                if self.client:
                    await self.client.emit_message(
                        EventTypes.COMMUTER_PICKED_UP,
                        {"commuter_id": commuter_id}
                    )
                
                self.logger.debug(f"Marked commuter {commuter_id} as picked up")
                return True
        
        return False
    
    async def _send_query_response(
        self,
        commuters: List[LocationAwareCommuter],
        correlation_id: Optional[str],
        target: Optional[str]
    ):
        """Send query response via Socket.IO"""
        if not self.client:
            return
        
        commuter_data = [
            {
                "commuter_id": c.commuter_id,
                "current_location": {
                    "lat": c.current_location[0],
                    "lon": c.current_location[1]
                },
                "destination": {
                    "lat": c.destination_position[0],
                    "lon": c.destination_position[1]
                },
                "direction": c.direction.value,
                "priority": c.priority,
                "max_walking_distance": c.max_walking_distance_m,
                "spawn_time": c.spawn_time.isoformat(),
            }
            for c in commuters
        ]
        
        await self.client.emit_message(
            EventTypes.COMMUTERS_FOUND,
            {
                "commuters": commuter_data,
                "total_count": len(commuters),
            },
            target=target,
            correlation_id=correlation_id
        )
    
    async def _expiration_loop(self):
        """Background task to expire old commuters"""
        while self.running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                now = datetime.now()
                expired_ids = []
                
                # Find expired commuters (default 30 minutes)
                max_age = timedelta(minutes=30)
                
                for commuter_id, commuter in self.active_commuters.items():
                    age = now - commuter.spawn_time
                    if age > max_age:
                        expired_ids.append(commuter_id)
                
                # Remove expired commuters
                for commuter_id in expired_ids:
                    commuter = self.active_commuters.pop(commuter_id)
                    
                    # Remove from queue
                    for queue in self.queues.values():
                        removed = queue.remove_commuter(commuter_id)
                        if removed:
                            queue.total_expired += 1
                            self.stats["total_expired"] += 1
                    
                    # Emit expiration event
                    if self.client:
                        await self.client.emit_message(
                            EventTypes.COMMUTER_EXPIRED,
                            {"commuter_id": commuter_id}
                        )
                    
                    self.logger.debug(f"Expired commuter {commuter_id}")
                
                if expired_ids:
                    self.logger.info(f"Expired {len(expired_ids)} commuters")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in expiration loop: {e}")
    
    def get_stats(self) -> Dict:
        """Get depot reservoir statistics"""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        queue_stats = [q.get_stats() for q in self.queues.values()]
        
        return {
            "service": "depot-reservoir",
            "running": self.running,
            "uptime_seconds": uptime,
            "total_queues": len(self.queues),
            "total_active_commuters": len(self.active_commuters),
            "total_spawned": self.stats["total_spawned"],
            "total_picked_up": self.stats["total_picked_up"],
            "total_expired": self.stats["total_expired"],
            "queues": queue_stats,
        }
