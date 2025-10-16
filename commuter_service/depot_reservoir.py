"""
Depot Reservoir - Outbound Commuter Management

This module manages outbound commuters waiting at depot locations.
Commuters spawn at depots and wait in a queue for vehicles to arrive.

Features:
- FIFO queue management for outbound commuters
- Proximity-based commuter queries for vehicles
- Real-time commuter spawning and expiration
- Socket.IO integration for event notifications

Refactored Architecture (SRP compliance):
- Uses DepotQueue for queue management
- Uses LocationNormalizer for location format conversion
- Uses ReservoirStatistics for thread-safe statistics tracking
- Uses ExpirationManager for background expiration tasks
- Uses SpawningCoordinator for automatic passenger spawning
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
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

# Extracted modules (SRP compliance)
from commuter_service.depot_queue import DepotQueue
from commuter_service.location_normalizer import LocationNormalizer
from commuter_service.reservoir_statistics import ReservoirStatistics
from commuter_service.expiration_manager import ReservoirExpirationManager
from commuter_service.spawning_coordinator import SpawningCoordinator


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
        
        # Extracted module instances (SRP compliance)
        self.statistics = ReservoirStatistics(name="DepotReservoir")
        self.expiration_manager: Optional[ReservoirExpirationManager] = None
        self.spawning_coordinator: Optional[SpawningCoordinator] = None
    
    async def start(self):
        """Start the depot reservoir service"""
        if self.running:
            self.logger.warning("Depot reservoir already running")
            return
        
        self.logger.info("Starting depot reservoir service...")
        self.running = True
        # Note: start_time is tracked in ReservoirStatistics.created_at
        
        # Connect to database
        await self.db.connect()
        
        # Initialize Strapi API client and load depot/route data
        # Strip /api suffix if present (StrapiApiClient adds it internally)
        api_base_url = self.strapi_url.rstrip('/api').rstrip('/')
        self.api_client = StrapiApiClient(api_base_url)
        await self.api_client.connect()
        
        self.logger.info("[API] Loading depots and routes from Strapi API...")
        self.depots = await self.api_client.get_all_depots()
        self.routes = await self.api_client.get_all_routes()
        
        self.logger.info(f"[OK] Loaded {len(self.depots)} depots and {len(self.routes)} routes")
        
        # Initialize Poisson spawner with GeoJSON population data
        self.logger.info("[INIT] Initializing Poisson GeoJSON spawner with population data...")
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
        self.logger.info("[STATS] DEPOT RESERVOIR - INITIALIZATION COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"[DEPOT] Active Depots: {len(self.depots)}")
        for depot in self.depots:
            depot_lat = depot.latitude or (depot.location.get('lat') if depot.location else None)
            depot_lon = depot.longitude or (depot.location.get('lon') if depot.location else None)
            if depot_lat and depot_lon:
                self.logger.info(f"   • {depot.depot_id} ({depot.name}) @ ({depot_lat:.4f}, {depot_lon:.4f})")
        self.logger.info(f"[ROUTE] Active Routes: {len(self.routes)}")
        for route in self.routes[:5]:  # Show first 5
            self.logger.info(f"   • {route.short_name}: {route.long_name}")
        if len(self.routes) > 5:
            self.logger.info(f"   ... and {len(self.routes) - 5} more")
        self.logger.info("=" * 80)
        
        # Initialize ExpirationManager for background expiration task
        self.expiration_manager = ReservoirExpirationManager(
            get_commuters=lambda: self.active_commuters,
            on_expire=self._expire_commuter,
            check_interval=10.0,
            expiration_timeout=1800.0,  # 30 minutes
            logger=self.logger
        )
        
        # Initialize SpawningCoordinator for automatic passenger spawning
        self.spawning_coordinator = SpawningCoordinator(
            spawner=self.poisson_spawner,
            spawn_interval=30.0,  # 30-second intervals for spawning
            time_window_minutes=5.0,
            on_spawn_callback=self._process_spawn_request,
            logger=self.logger
        )
        
        # Start background managers
        await self.expiration_manager.start()
        await self.spawning_coordinator.start()
        
        self.logger.info("Depot reservoir service started successfully with automatic spawning")
    
    async def stop(self):
        """Stop the depot reservoir service"""
        if not self.running:
            return
        
        self.logger.info("Stopping depot reservoir service...")
        self.running = False
        
        # Stop background managers
        if self.expiration_manager:
            await self.expiration_manager.stop()
        
        if self.spawning_coordinator:
            await self.spawning_coordinator.stop()
        
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
        # Normalize locations using LocationNormalizer
        depot_location = LocationNormalizer.normalize(depot_location)
        destination = LocationNormalizer.normalize(destination)
        
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
        
        # Update statistics using ReservoirStatistics
        await self.statistics.increment_spawned()
        
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
        
        # Get total spawned count from statistics
        stats = await self.statistics.get_stats()
        total_spawned = stats['total_spawned']
        
        # Log spawn details
        self.logger.info(
            f"[SPAWN] DEPOT SPAWN #{total_spawned} | "
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
                
                # Update statistics using ReservoirStatistics
                await self.statistics.increment_picked_up()
                
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
    
    # ========================================================================
    # Callback Methods for Extracted Managers (SRP compliance)
    # ========================================================================
    # Callback Methods for Extracted Managers (SRP compliance)
    # ========================================================================
    
    async def _get_active_commuters_for_expiration(self) -> List[tuple[str, LocationAwareCommuter]]:
        """
        Callback for ExpirationManager to get active commuters.
        
        Returns:
            List of (commuter_id, commuter) tuples
        """
        return list(self.active_commuters.items())
    
    async def _expire_commuter(self, commuter_id: str, commuter: LocationAwareCommuter):
        """
        Callback for ExpirationManager to expire a commuter.
        
        Args:
            commuter_id: Commuter identifier
            commuter: LocationAwareCommuter instance
        """
        # Remove from active commuters
        self.active_commuters.pop(commuter_id, None)
        
        # Remove from queue
        for queue in self.queues.values():
            removed = queue.remove_commuter(commuter_id)
            if removed:
                queue.total_expired += 1
        
        # Update statistics
        await self.statistics.increment_expired()
        
        # Delete from database
        try:
            deleted_count = await self.db.delete_expired()
            if deleted_count > 0:
                self.logger.debug(f"Deleted {deleted_count} expired passengers from database")
        except Exception as e:
            self.logger.error(f"Error deleting expired passengers: {e}")
        
        # Emit expiration event
        if self.client:
            await self.client.emit_message(
                EventTypes.COMMUTER_EXPIRED,
                {"commuter_id": commuter_id}
            )
    
    async def _generate_spawn_requests(self) -> List[Dict]:
        """
        Callback for SpawningCoordinator to generate spawn requests.
        
        Returns:
            List of spawn request dicts from Poisson spawner
        """
        current_time = datetime.now()
        spawn_requests = await self.poisson_spawner.generate_poisson_spawn_requests(
            current_time=current_time,
            time_window_minutes=5,
            spawn_context="depot"  # Depot spawning pattern
        )
        return spawn_requests
    
    async def _process_spawn_request(self, spawn_request: Dict):
        """
        Callback for SpawningCoordinator to process a spawn request.
        
        Args:
            spawn_request: Spawn request dict with location/destination/route info
        """
        spawn_location = spawn_request.get('spawn_location')  # (lat, lon)
        destination = spawn_request.get('destination_location')  # (lat, lon)
        route_id = spawn_request.get('assigned_route')
        priority = spawn_request.get('priority', 3)
        
        if not all([spawn_location, destination, route_id]):
            self.logger.debug(f"Skipping incomplete spawn request")
            return
        
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
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _find_nearest_depot(self, location: tuple[float, float]) -> Optional[DepotData]:
        """Find the nearest depot to a given location using Haversine distance"""
        from math import radians, sin, cos, sqrt, atan2
        
        if not self.depots:
            return None
        
        # Normalize location using LocationNormalizer
        lat1, lon1 = LocationNormalizer.normalize(location)
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
        
        # Normalize location using LocationNormalizer
        lat, lon = LocationNormalizer.normalize(location)
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
    
    async def get_stats(self) -> Dict:
        """Get depot reservoir statistics"""
        # Get statistics from ReservoirStatistics
        stats = await self.statistics.get_stats()
        
        queue_stats = [q.get_stats() for q in self.queues.values()]
        
        return {
            "service": "depot-reservoir",
            "running": self.running,
            "uptime_seconds": stats['uptime_seconds'],
            "total_queues": len(self.queues),
            "total_active_commuters": len(self.active_commuters),
            "total_spawned": stats['total_spawned'],
            "total_picked_up": stats['total_picked_up'],
            "total_expired": stats['total_expired'],
            "queues": queue_stats,
        }
