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
from commuter_service.strapi_api_client import StrapiApiClient, DepotData, RouteData
from commuter_service.poisson_geojson_spawner import PoissonGeoJSONSpawner


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
        self.strapi_url = strapi_url or "http://localhost:1337"
        self.config = config or CommuterConfigLoader.get_default_config()
        self.logger = logger or logging.getLogger(__name__)
        
        # Depot queues: {(depot_id, route_id): DepotQueue}
        self.queues: Dict[tuple[str, str], DepotQueue] = {}
        
        # Socket.IO client
        self.client: Optional[SocketIOClient] = None
        
        # Database client for passenger persistence
        self.db = PassengerDatabase(strapi_url)
        
        # Strapi API client for depot/route data
        self.api_client: Optional[StrapiApiClient] = None
        
        # Poisson spawner for statistical passenger generation
        self.poisson_spawner: Optional[PoissonGeoJSONSpawner] = None
        
        # Depot and route data from API
        self.depots: List[DepotData] = []
        self.routes: List[RouteData] = []
        
        # Active commuters for quick lookup
        self.active_commuters: Dict[str, LocationAwareCommuter] = {}
        
        # Background tasks
        self.running = False
        self.expiration_task: Optional[asyncio.Task] = None
        self.spawning_task: Optional[asyncio.Task] = None
        
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
        
        # Initialize Strapi API client and load depot/route data
        # Strip /api suffix if present (StrapiApiClient adds it internally)
        api_base_url = self.strapi_url.rstrip('/api').rstrip('/')
        self.api_client = StrapiApiClient(api_base_url)
        await self.api_client.connect()
        
        self.logger.info("📡 Loading depots and routes from Strapi API...")
        self.depots = await self.api_client.get_all_depots()
        self.routes = await self.api_client.get_all_routes()
        
        self.logger.info(f"✅ Loaded {len(self.depots)} depots and {len(self.routes)} routes")
        
        # Initialize Poisson spawner with GeoJSON population data
        self.logger.info("🌍 Initializing Poisson GeoJSON spawner with population data...")
        self.poisson_spawner = PoissonGeoJSONSpawner(self.api_client)
        await self.poisson_spawner.initialize(country_code="BB")  # Barbados ISO code
        
        # Create depot queues for all depot-route combinations
        for depot in self.depots:
            depot_lat = depot.latitude or (depot.location.get('lat') if depot.location else None)
            depot_lon = depot.longitude or (depot.location.get('lon') if depot.location else None)
            
            if not depot_lat or not depot_lon:
                self.logger.warning(f"Depot {depot.depot_id} has no GPS coordinates, skipping")
                continue
            
            for route in self.routes:
                queue_key = (depot.depot_id, route.short_name)
                self.queues[queue_key] = DepotQueue(
                    depot_id=depot.depot_id,
                    depot_location=(depot_lat, depot_lon),
                    route_id=route.short_name
                )
        
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
        self.logger.info(f"🏢 Active Depots: {len(self.depots)}")
        for depot in self.depots:
            depot_lat = depot.latitude or (depot.location.get('lat') if depot.location else None)
            depot_lon = depot.longitude or (depot.location.get('lon') if depot.location else None)
            if depot_lat and depot_lon:
                self.logger.info(f"   • {depot.depot_id} ({depot.name}) @ ({depot_lat:.4f}, {depot_lon:.4f})")
        self.logger.info(f"🚌 Active Routes: {len(self.routes)}")
        for route in self.routes[:5]:  # Show first 5
            self.logger.info(f"   • {route.short_name}: {route.long_name}")
        if len(self.routes) > 5:
            self.logger.info(f"   ... and {len(self.routes) - 5} more")
        self.logger.info("=" * 80)
        
        # Start background tasks
        self.expiration_task = asyncio.create_task(self._expiration_loop())
        self.spawning_task = asyncio.create_task(self._spawning_loop())
        
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
        
        if self.spawning_task:
            self.spawning_task.cancel()
            try:
                await self.spawning_task
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
        # Normalize locations to (float, float) tuples
        depot_location = self._normalize_location(depot_location)
        destination = self._normalize_location(destination)
        
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
            priority=max(1, min(5, int(priority * 5) + 1)),  # Convert float (0.0-1.0) to int (1-5)
            expires_minutes=max_wait_time.total_seconds() / 60 if max_wait_time else 30
        )
        
        # Get location names
        spawn_location_name = self._get_location_name(depot_location)
        dest_location_name = self._get_location_name(destination)
        
        # Get depot name
        depot_name = next((d.name for d in self.depots if d.depot_id == depot_id), depot_id)
        
        # Log spawn details
        self.logger.info(
            f"✅ DEPOT SPAWN #{self.stats['total_spawned']} | "
            f"ID: {commuter.commuter_id[:8]}... | "
            f"Depot: {depot_name} @ ({depot_location[0]:.4f}, {depot_location[1]:.4f}) | "
            f"Near: {spawn_location_name} | "
            f"Route: {route_id} | "
            f"Dest: ({destination[0]:.4f}, {destination[1]:.4f}) → {dest_location_name} | "
            f"Priority: {priority} | "
            f"Queue: {len(queue.commuters)} waiting"
        )
        
        # Emit spawn event via Socket.IO
        await self.client.emit_message(
            "commuter:spawned",
            {
                "passenger_id": commuter.commuter_id,
                "depot_id": depot_id,
                "depot_name": depot_name,
                "route_id": route_id,
                "spawn_location": {
                    "lat": depot_location[0],
                    "lon": depot_location[1],
                    "name": spawn_location_name
                },
                "destination": {
                    "lat": destination[0],
                    "lon": destination[1],
                    "name": dest_location_name
                },
                "priority": priority,
                "queue_size": len(queue.commuters),
                "spawn_time": commuter.spawn_time.isoformat(),
                "type": "depot"
            }
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
    
    async def _spawning_loop(self):
        """Background task for automatic Poisson-based passenger spawning using GeoJSON population data"""
        self.logger.info("🚀 Starting automatic passenger spawning loop (using real GeoJSON population data)")
        
        while self.running:
            try:
                # Wait before next spawn cycle (30 seconds for demo)
                await asyncio.sleep(30)  # 30-second intervals for testing
                
                current_time = datetime.now()
                
                # Generate spawn requests from Poisson spawner using GeoJSON population zones
                spawn_requests = await self.poisson_spawner.generate_poisson_spawn_requests(
                    current_time=current_time,
                    time_window_minutes=5
                )
                
                self.logger.info(f"🎲 Poisson spawner generated {len(spawn_requests)} spawn requests for hour {current_time.hour}")
                
                # Process spawn requests
                for request in spawn_requests:
                    try:
                        spawn_location = request.get('spawn_location')  # (lat, lon)
                        destination = request.get('destination_location')  # (lat, lon)
                        route_id = request.get('assigned_route')
                        priority = request.get('priority', 3)
                        
                        if not all([spawn_location, destination, route_id]):
                            self.logger.debug(f"Skipping incomplete spawn request: spawn={spawn_location}, dest={destination}, route={route_id}")
                            continue
                        
                        # Find nearest depot to spawn location
                        nearest_depot = self._find_nearest_depot(spawn_location)
                        
                        if nearest_depot:
                            # Get depot coordinates
                            depot_lat = nearest_depot.latitude if nearest_depot.latitude is not None else nearest_depot.location.get('lat')
                            depot_lon = nearest_depot.longitude if nearest_depot.longitude is not None else nearest_depot.location.get('lon')
                            
                            # Ensure coordinates are floats
                            if isinstance(depot_lat, str):
                                depot_lat = float(depot_lat)
                            if isinstance(depot_lon, str):
                                depot_lon = float(depot_lon)
                            
                            # Spawn commuter at depot
                            await self.spawn_commuter(
                                depot_id=nearest_depot.depot_id,
                                route_id=route_id,
                                depot_location=(depot_lat, depot_lon),
                                destination=destination,
                                priority=priority
                            )
                        
                    except Exception as e:
                        self.logger.error(f"Failed to process spawn request: {e}", exc_info=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in spawning loop: {e}")
    
    def _normalize_location(self, location) -> tuple[float, float]:
        """
        Convert location to (lat, lon) tuple of floats.
        Handles dict {'lat': x, 'lon': y}, tuple/list (x, y), with string or numeric values.
        """
        if isinstance(location, dict):
            lat = location.get('lat') or location.get('latitude')
            lon = location.get('lon') or location.get('longitude')
            if lat is None or lon is None:
                raise ValueError(f"Invalid dict location format: {location}")
            return (float(lat), float(lon))
        elif isinstance(location, (tuple, list)) and len(location) == 2:
            return (float(location[0]), float(location[1]))
        else:
            raise ValueError(f"Unexpected location format: {location} (type: {type(location)})")
    
    def _find_nearest_depot(self, location: tuple[float, float]) -> Optional[DepotData]:
        """Find the nearest depot to a given location using Haversine distance"""
        from math import radians, sin, cos, sqrt, atan2
        
        if not self.depots:
            return None
        
        # Normalize location to (float, float) tuple
        lat1, lon1 = self._normalize_location(location)
        min_distance = float('inf')
        nearest_depot = None
        
        for depot in self.depots:
            depot_lat = depot.latitude or (depot.location.get('lat') if depot.location else None)
            depot_lon = depot.longitude or (depot.location.get('lon') if depot.location else None)
            
            if not depot_lat or not depot_lon:
                continue
            
            # Ensure coordinates are floats (might be strings from API)
            lat2 = float(depot_lat) if isinstance(depot_lat, str) else depot_lat
            lon2 = float(depot_lon) if isinstance(depot_lon, str) else depot_lon
            
            # Haversine distance
            R = 6371000  # Earth radius in meters
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            if distance < min_distance:
                min_distance = distance
                nearest_depot = depot
        
        return nearest_depot
    
    def _get_location_name(self, location: tuple[float, float]) -> str:
        """Get location name from coordinates using GeoJSON data"""
        from math import radians, sin, cos, sqrt, atan2
        
        if not hasattr(self, 'poisson_spawner') or not self.poisson_spawner:
            return "Unknown Location"
        
        # Normalize location to (float, float) tuple
        lat, lon = self._normalize_location(location)
        min_distance = float('inf')
        nearest_name = "Unknown Location"
        
        # Check amenity zones (POIs and Places)
        for zone in self.poisson_spawner.geojson_loader.amenity_zones:
            zone_lat, zone_lon = zone.center_point
            
            # Simple distance calculation
            R = 6371000  # Earth radius in meters
            dlat = radians(zone_lat - lat)
            dlon = radians(zone_lon - lon)
            a = sin(dlat/2)**2 + cos(radians(lat)) * cos(radians(zone_lat)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            if distance < min_distance and distance < 100:  # Within 100m
                min_distance = distance
                nearest_name = f"{zone.zone_type.title()} ({zone.zone_id.replace('poi_', '').replace('_', ' ')})"
        
        return nearest_name
    
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
                    self.logger.info(f"Expired {len(expired_ids)} commuters from memory")
                    
                    # 🆕 FIX: Delete expired passengers from database
                    try:
                        deleted_count = await self.db.delete_expired()
                        if deleted_count > 0:
                            self.logger.info(f"🗑️  Deleted {deleted_count} expired passengers from database")
                    except Exception as e:
                        self.logger.error(f"Error deleting expired passengers from database: {e}")
                    
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
