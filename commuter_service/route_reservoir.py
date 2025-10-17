"""
Route Reservoir - Bidirectional Commuter Management

This module manages commuters spawning along route paths (not at depots).
Supports both inbound and outbound commuters at various points along routes.

Features:
- Bidirectional commuter spawning (inbound/outbound)
- Proximity-based vehicle queries
- Grid-based spatial indexing for fast lookups
- Real-time commuter management
- Socket.IO integration

Refactored Architecture (SRP compliance):
- Uses RouteSegment for bidirectional segment tracking
- Uses LocationNormalizer for location format conversion
- Uses ReservoirStatistics for thread-safe statistics tracking
- Uses ExpirationManager for background expiration tasks
- Uses SpawningCoordinator for automatic passenger spawning
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import math

from commuter_service.socketio_client import (
    SocketIOClient,
    EventTypes,
    ServiceType,
    create_route_client,
    CommuterDirection,
)
from commuter_service.location_aware_commuter import LocationAwareCommuter
from commuter_service.commuter_config import CommuterBehaviorConfig, CommuterConfigLoader
from commuter_service.passenger_db import PassengerDatabase
from commuter_service.strapi_api_client import StrapiApiClient, DepotData, RouteData
from commuter_service.poisson_geojson_spawner import PoissonGeoJSONSpawner
from commuter_service.spatial_zone_cache import SpatialZoneCache

# Extracted modules (SRP compliance)
from commuter_service.route_segment import RouteSegment
from commuter_service.location_normalizer import LocationNormalizer
from commuter_service.reservoir_statistics import ReservoirStatistics
from commuter_service.expiration_manager import ReservoirExpirationManager
from commuter_service.spawning_coordinator import SpawningCoordinator


def get_grid_cell(lat: float, lon: float, cell_size: float = 0.01) -> Tuple[int, int]:
    """
    Get grid cell coordinates for spatial indexing
    
    Args:
        lat: Latitude
        lon: Longitude
        cell_size: Grid cell size in degrees (~1km at equator)
    
    Returns:
        (grid_x, grid_y) tuple
    """
    return (int(lat / cell_size), int(lon / cell_size))


def get_nearby_cells(
    lat: float,
    lon: float,
    radius_km: float = 2.0,
    cell_size: float = 0.01
) -> List[Tuple[int, int]]:
    """
    Get all grid cells within radius
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Search radius in kilometers
        cell_size: Grid cell size in degrees
    
    Returns:
        List of (grid_x, grid_y) tuples
    """
    # Convert radius to degrees (approximate)
    radius_deg = radius_km / 111.0  # ~111km per degree latitude
    
    center_cell = get_grid_cell(lat, lon, cell_size)
    cell_radius = int(radius_deg / cell_size) + 1
    
    cells = []
    for dx in range(-cell_radius, cell_radius + 1):
        for dy in range(-cell_radius, cell_radius + 1):
            cells.append((center_cell[0] + dx, center_cell[1] + dy))
    
    return cells


class RouteReservoir:
    """
    Route Reservoir manages bidirectional commuters along route paths.
    
    Architecture:
    - Grid-based spatial indexing for fast proximity searches
    - Separate tracking for inbound/outbound commuters
    - Route-based organization
    - Socket.IO event integration
    - Automatic commuter expiration
    
    Usage:
        reservoir = RouteReservoir(socketio_url="http://localhost:1337")
        await reservoir.start()
        
        # Spawn commuter along route
        commuter = await reservoir.spawn_commuter(
            route_id="ROUTE_A",
            current_location=(40.7500, -73.9950),
            destination=(40.7589, -73.9851),
            direction=CommuterDirection.INBOUND
        )
        
        # Vehicle queries for nearby commuters
        commuters = reservoir.query_commuters_sync(
            route_id="ROUTE_A",
            vehicle_location=(40.7520, -73.9970),
            direction=CommuterDirection.INBOUND,
            max_distance=1000,
            max_count=5
        )
    """
    
    def __init__(
        self,
        socketio_url: str = "http://localhost:1337",
        config: Optional[CommuterBehaviorConfig] = None,
        grid_cell_size: float = 0.01,  # ~1km cells
        logger: Optional[logging.Logger] = None,
        strapi_url: Optional[str] = None
    ):
        self.socketio_url = socketio_url
        self.strapi_url = strapi_url or "http://localhost:1337"
        self.config = config or CommuterConfigLoader.get_default_config()
        self.grid_cell_size = grid_cell_size
        self.logger = logger or logging.getLogger(__name__)
        
        # Spatial index: {(grid_x, grid_y): {route_id: RouteSegment}}
        self.grid: Dict[Tuple[int, int], Dict[str, RouteSegment]] = defaultdict(dict)
        
        # Active commuters for quick lookup
        self.active_commuters: Dict[str, LocationAwareCommuter] = {}
        
        # Commuter location index: {commuter_id: grid_cell}
        self.commuter_cells: Dict[str, Tuple[int, int]] = {}
        
        # Socket.IO client
        self.client: Optional[SocketIOClient] = None
        
        # Database client for passenger persistence
        self.db = PassengerDatabase(strapi_url)
        
        # Strapi API client for depot/route data
        self.api_client: Optional[StrapiApiClient] = None
        
        # Poisson spawner for statistical passenger generation
        self.poisson_spawner: Optional[PoissonGeoJSONSpawner] = None
        
        # Spatial zone cache for performance (loads zones in background)
        self.spatial_cache: Optional[SpatialZoneCache] = None
        
        # Route data from API
        self.routes: List[RouteData] = []
        
        # Background tasks
        self.running = False
        
        # Extracted module instances (SRP compliance)
        self.statistics = ReservoirStatistics(name="RouteReservoir")
        self.expiration_manager: Optional[ReservoirExpirationManager] = None
        self.spawning_coordinator: Optional[SpawningCoordinator] = None
    
    async def start(self):
        """Start the route reservoir service"""
        if self.running:
            self.logger.warning("Route reservoir already running")
            return
        
        self.logger.info("Starting route reservoir service...")
        self.running = True
        # Note: start_time is tracked in ReservoirStatistics.created_at
        
        # Connect to database
        await self.db.connect()
        
        # Initialize Strapi API client and load route data
        # Strip /api suffix if present (StrapiApiClient adds it internally)
        api_base_url = self.strapi_url.rstrip('/api').rstrip('/')
        self.api_client = StrapiApiClient(api_base_url)
        await self.api_client.connect()
        
        self.logger.info("[API] Loading routes from Strapi API...")
        self.routes = await self.api_client.get_all_routes()
        
        self.logger.info(f"[OK] Loaded {len(self.routes)} routes from database")
        
        # Extract route coordinates for spatial filtering
        route_coordinates = []
        for route in self.routes:
            if route.geometry_coordinates:
                route_coordinates.extend(route.geometry_coordinates)
        
        # Initialize spatial zone cache (loads zones in background thread)
        self.logger.info(f"[SPATIAL] Initializing spatial zone cache with {len(route_coordinates)} route points...")
        self.spatial_cache = SpatialZoneCache(
            api_client=self.api_client,
            country_id=1,  # Barbados
            buffer_km=5.0,  # Only load zones within 5km of routes
            cache_ttl_minutes=60,
            logger=self.logger
        )
        
        # Start background zone loading (non-blocking)
        await self.spatial_cache.initialize_for_route(
            route_coordinates=route_coordinates,
            depot_locations=[]  # No depots for route reservoir
        )
        
        # Initialize Poisson spawner with GeoJSON population data
        self.logger.info("[INIT] Initializing Poisson GeoJSON spawner with spatial cache...")
        self.poisson_spawner = PoissonGeoJSONSpawner(
            self.api_client,
            spatial_cache=self.spatial_cache  # Pass spatial cache for background loading
        )
        await self.poisson_spawner.initialize(country_code="BB", use_spatial_cache=True)  # Barbados ISO code
        
        # Initialize route segments from loaded routes
        for route in self.routes:
            if route.geometry_coordinates:
                self._create_route_segments(route.short_name, route.geometry_coordinates)
        
        # Connect to Socket.IO
        self.client = create_route_client(
            url=self.socketio_url,
            service_type=ServiceType.COMMUTER_SERVICE
        )
        
        # Register event handlers
        self._register_handlers()
        
        # Connect to Socket.IO hub
        await self.client.connect()
        
        # Log startup statistics
        self.logger.info("=" * 80)
        self.logger.info("[STATS] ROUTE RESERVOIR - INITIALIZATION COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"[ROUTE] Active Routes: {len(self.routes)}")
        for route in self.routes[:5]:  # Show first 5
            self.logger.info(f"   • {route.short_name}: {route.long_name} ({route.coordinate_count} points)")
        if len(self.routes) > 5:
            self.logger.info(f"   ... and {len(self.routes) - 5} more")
        self.logger.info(f"[GRID] Grid Cell Size: {self.grid_cell_size}° (~1km)")
        self.logger.info(f"[GRID] Active Grid Cells: {len(self.grid)}")
        self.logger.info(f"[COMMUTER] Active Commuters: {len(self.active_commuters)}")
        self.logger.info("=" * 80)
        
        # Initialize ExpirationManager for background expiration task
        self.expiration_manager = ReservoirExpirationManager(
            get_commuters=lambda: self.active_commuters,
            on_expire=self._expire_commuter,
            check_interval=10.0,
            expiration_timeout=1800.0,  # 30 minutes
            logger=self.logger
        )
        
        # Load spawn_interval from configuration service (database-driven)
        spawn_interval = 30.0  # Default fallback
        try:
            from arknet_transit_simulator.services.config_service import get_config_service
            config_service = await get_config_service()
            spawn_interval = await config_service.get(
                "commuter_service.spawning.route_spawn_interval_seconds",
                default=30.0
            )
            self.logger.info(
                f"[CONFIG] Loaded spawn_interval from database: {spawn_interval}s "
                "(configure via Strapi: commuter_service.spawning.route_spawn_interval_seconds)"
            )
        except Exception as e:
            self.logger.warning(
                f"[CONFIG] Could not load spawn_interval from config service, using default {spawn_interval}s: {e}"
            )
        
        # Initialize SpawningCoordinator for automatic passenger spawning
        self.spawning_coordinator = SpawningCoordinator(
            spawner=self.poisson_spawner,
            spawn_interval=spawn_interval,  # Database-driven configuration
            time_window_minutes=5.0,
            on_spawn_callback=self._process_spawn_request,
            logger=self.logger
        )
        
        # Start background managers
        await self.expiration_manager.start()
        await self.spawning_coordinator.start()
        
        self.logger.info("Route reservoir service started successfully with automatic spawning")
    
    def _create_route_segments(self, route_id: str, coordinates: List[List[float]]):
        """Create route segments from GPS coordinates and add to spatial grid"""
        if not coordinates or len(coordinates) < 2:
            return
        
        for i in range(len(coordinates) - 1):
            lat1, lon1 = coordinates[i]
            lat2, lon2 = coordinates[i + 1]
            
            # Add segment to grid cell
            cell = get_grid_cell(lat1, lon1, self.grid_cell_size)
            segment_id = f"{route_id}_seg_{i}"
            
            if route_id not in self.grid[cell]:
                self.grid[cell][route_id] = RouteSegment(
                    route_id=route_id,
                    segment_id=segment_id,
                    grid_cell=cell
                )
    
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
    
    async def stop(self):
        """Stop the route reservoir service"""
        if not self.running:
            return
        
        self.logger.info("Stopping route reservoir service...")
        self.running = False
        
        # Stop background managers
        if self.expiration_manager:
            await self.expiration_manager.stop()
        
        if self.spawning_coordinator:
            await self.spawning_coordinator.stop()
        
        if self.spatial_cache:
            await self.spatial_cache.shutdown()
        
        # Disconnect from database
        await self.db.disconnect()
        
        # Disconnect from Socket.IO
        if self.client:
            await self.client.disconnect()
        
        self.logger.info("Route reservoir service stopped")
    
    def _register_handlers(self):
        """Register Socket.IO event handlers"""
        
        async def handle_vehicle_query(message: Dict):
            """Handle vehicle query for commuters"""
            data = message.get("data", {})
            
            route_id = data.get("route_id")
            vehicle_location = data.get("vehicle_location", {})
            vehicle_lat = vehicle_location.get("lat")
            vehicle_lon = vehicle_location.get("lon")
            direction_str = data.get("direction", "OUTBOUND").upper()
            max_distance = data.get("search_radius", 1000)
            max_count = data.get("available_seats", 5)
            
            if not all([route_id, vehicle_lat, vehicle_lon]):
                self.logger.warning(f"Invalid vehicle query: {data}")
                return
            
            # Parse direction
            direction = CommuterDirection.INBOUND if direction_str == "INBOUND" else CommuterDirection.OUTBOUND
            
            # Query commuters
            commuters = self.query_commuters_sync(
                route_id=route_id,
                vehicle_location=(vehicle_lat, vehicle_lon),
                direction=direction,
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
    
    def _get_or_create_segment(
        self,
        route_id: str,
        grid_cell: Tuple[int, int]
    ) -> RouteSegment:
        """Get existing segment or create new one"""
        if route_id not in self.grid[grid_cell]:
            segment_id = f"{route_id}_{grid_cell[0]}_{grid_cell[1]}"
            self.grid[grid_cell][route_id] = RouteSegment(
                route_id=route_id,
                segment_id=segment_id,
                grid_cell=grid_cell
            )
            self.logger.debug(f"Created route segment: {segment_id}")
        
        return self.grid[grid_cell][route_id]
    
    async def spawn_commuter(
        self,
        route_id: str,
        current_location: tuple[float, float],
        destination: tuple[float, float],
        direction: CommuterDirection,
        priority: int = 3,
        nearest_stop: Optional[Dict] = None
    ) -> LocationAwareCommuter:
        """
        Spawn a new commuter along the route
        
        Args:
            route_id: Route identifier
            current_location: (lat, lon) of commuter spawn point
            destination: (lat, lon) of destination
            direction: Travel direction (INBOUND or OUTBOUND)
            priority: Priority level (1=highest, 5=lowest)
            nearest_stop: Optional bus stop data
        
        Returns:
            LocationAwareCommuter instance
        """
        # Normalize locations using LocationNormalizer
        current_location = LocationNormalizer.normalize(current_location)
        destination = LocationNormalizer.normalize(destination)
        
        # Get grid cell for location
        grid_cell = get_grid_cell(
            current_location[0],
            current_location[1],
            self.grid_cell_size
        )
        
        # Get or create segment
        segment = self._get_or_create_segment(route_id, grid_cell)
        
        # Create commuter
        person_id = f"COM_{uuid.uuid4().hex[:8].upper()}"
        commuter = LocationAwareCommuter(
            person_id=person_id,
            person_name=None,
            spawn_location=current_location,
            destination_location=destination,
            trip_purpose="commute",
            priority=priority,
            config=self.config
        )
        # Store additional metadata
        commuter.commuter_id = person_id
        commuter.direction = direction
        commuter.spawn_time = datetime.now()
        
        # Add to segment
        segment.add_commuter(commuter)
        self.active_commuters[commuter.commuter_id] = commuter
        self.commuter_cells[commuter.commuter_id] = grid_cell
        
        # Update statistics using ReservoirStatistics
        await self.statistics.increment_spawned()
        
        # Emit spawn event
        if self.client:
            await self.client.emit_message(
                EventTypes.COMMUTER_SPAWNED,
                {
                    "commuter_id": commuter.commuter_id,
                    "route_id": route_id,
                    "current_location": {
                        "lat": current_location[0],
                        "lon": current_location[1]
                    },
                    "destination": {
                        "lat": destination[0],
                        "lon": destination[1]
                    },
                    "direction": direction.value,
                    "priority": priority,
                    "max_walking_distance": commuter.max_walking_distance_m,
                    "spawn_time": commuter.spawn_time.isoformat(),
                    "nearest_stop": nearest_stop,
                }
            )
        
        # Persist to database
        await self.db.insert_passenger(
            passenger_id=commuter.commuter_id,
            route_id=route_id,
            latitude=current_location[0],
            longitude=current_location[1],
            destination_lat=destination[0],
            destination_lon=destination[1],
            destination_name="Destination",
            depot_id=None,  # Route spawns don't have depot
            direction=direction.value,
            priority=max(1, min(5, int(priority * 5) + 1)),  # Convert float (0.0-1.0) to int (1-5)
            expires_minutes=30  # Default 30 minute expiration for route spawns
        )
        
        
        # Get location names
        spawn_location_name = self._get_location_name(current_location)
        dest_location_name = self._get_location_name(destination)
        
        # Get total spawned count from statistics
        stats = await self.statistics.get_stats()
        total_spawned = stats['total_spawned']
        
        # Log spawn details
        self.logger.info(
            f"[SPAWN] ROUTE SPAWN #{total_spawned} | "
            f"ID: {commuter.commuter_id[:8]}... | "
            f"Route: {route_id} | "
            f"Spawn: ({current_location[0]:.4f}, {current_location[1]:.4f}) → {spawn_location_name} | "
            f"Dest: ({destination[0]:.4f}, {destination[1]:.4f}) → {dest_location_name} | "
            f"Direction: {direction.value} | "
            f"Priority: {priority} | "
            f"Grid: {grid_cell}"
        )
        
        # Emit spawn event via Socket.IO
        await self.client.emit_message(
            "commuter:spawned",
            {
                "passenger_id": commuter.commuter_id,
                "route_id": route_id,
                "spawn_location": {
                    "lat": current_location[0],
                    "lon": current_location[1],
                    "name": spawn_location_name
                },
                "destination": {
                    "lat": destination[0],
                    "lon": destination[1],
                    "name": dest_location_name
                },
                "direction": direction.value,
                "priority": priority,
                "grid_cell": grid_cell,
                "spawn_time": commuter.spawn_time.isoformat(),
                "type": "route"
            }
        )
        
        return commuter
    
    def query_commuters_sync(
        self,
        route_id: str,
        vehicle_location: tuple[float, float],
        direction: CommuterDirection,
        max_distance: float = 1000,
        max_count: int = 5
    ) -> List[LocationAwareCommuter]:
        """
        Query commuters available for pickup (synchronous version)
        
        Args:
            route_id: Route identifier
            vehicle_location: (lat, lon) of vehicle
            direction: Travel direction to match
            max_distance: Maximum distance in meters
            max_count: Maximum number of commuters
        
        Returns:
            List of available commuters sorted by proximity
        """
        # Get nearby grid cells
        radius_km = max_distance / 1000.0
        nearby_cells = get_nearby_cells(
            vehicle_location[0],
            vehicle_location[1],
            radius_km,
            self.grid_cell_size
        )
        
        available = []
        
        # Search through nearby cells
        for cell in nearby_cells:
            if cell not in self.grid:
                continue
            
            if route_id not in self.grid[cell]:
                continue
            
            segment = self.grid[cell][route_id]
            commuters = segment.get_commuters_by_direction(direction)
            
            for commuter in commuters:
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
                        return available[:max_count]
        
        return available[:max_count]
    
    async def mark_picked_up(self, commuter_id: str) -> bool:
        """
        Mark commuter as picked up and remove from reservoir
        
        Args:
            commuter_id: Commuter identifier
        
        Returns:
            True if commuter was found and removed
        """
        if commuter_id not in self.active_commuters:
            return False
        
        commuter = self.active_commuters.pop(commuter_id)
        grid_cell = self.commuter_cells.pop(commuter_id)
        
        # Find and remove from segment
        if grid_cell in self.grid:
            for route_id, segment in self.grid[grid_cell].items():
                removed = segment.remove_commuter(commuter_id)
                if removed:
                    segment.total_picked_up += 1
                    
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
        grid_cell = self.commuter_cells.pop(commuter_id, None)
        
        # Remove from segment
        if grid_cell and grid_cell in self.grid:
            for segment in self.grid[grid_cell].values():
                removed = segment.remove_commuter(commuter_id)
                if removed:
                    segment.total_expired += 1
        
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
            spawn_context="route"  # Route spawning pattern
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
        direction = spawn_request.get('direction', 'OUTBOUND').upper()
        
        if not all([spawn_location, destination, route_id]):
            self.logger.debug(f"Skipping incomplete route spawn request")
            return
        
        # Convert direction string to enum
        commuter_direction = (
            CommuterDirection.INBOUND if direction == 'INBOUND' 
            else CommuterDirection.OUTBOUND
        )
        
        # Spawn commuter at route location
        await self.spawn_commuter(
            route_id=route_id,
            current_location=spawn_location,
            destination=destination,
            direction=commuter_direction,
            priority=priority
        )
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    async def get_stats(self) -> Dict:
        """Get route reservoir statistics"""
        # Get statistics from ReservoirStatistics
        stats = await self.statistics.get_stats()
        
        total_segments = sum(len(routes) for routes in self.grid.values())
        total_inbound = sum(
            len(seg.commuters_inbound)
            for routes in self.grid.values()
            for seg in routes.values()
        )
        total_outbound = sum(
            len(seg.commuters_outbound)
            for routes in self.grid.values()
            for seg in routes.values()
        )
        
        return {
            "service": "route-reservoir",
            "running": self.running,
            "uptime_seconds": stats['uptime_seconds'],
            "total_grid_cells": len(self.grid),
            "total_segments": total_segments,
            "total_active_commuters": len(self.active_commuters),
            "total_inbound": total_inbound,
            "total_outbound": total_outbound,
            "total_spawned": stats['total_spawned'],
            "total_picked_up": stats['total_picked_up'],
            "total_expired": stats['total_expired'],
        }
