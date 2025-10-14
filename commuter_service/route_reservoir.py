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
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
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


@dataclass
class RouteSegment:
    """Segment of route with commuters"""
    route_id: str
    segment_id: str
    grid_cell: Tuple[int, int]
    commuters_inbound: List[LocationAwareCommuter] = field(default_factory=list)
    commuters_outbound: List[LocationAwareCommuter] = field(default_factory=list)
    total_spawned: int = 0
    total_picked_up: int = 0
    total_expired: int = 0
    
    def add_commuter(self, commuter: LocationAwareCommuter):
        """Add commuter to appropriate direction list"""
        if commuter.direction == CommuterDirection.INBOUND:
            self.commuters_inbound.append(commuter)
        else:
            self.commuters_outbound.append(commuter)
        self.total_spawned += 1
    
    def remove_commuter(self, commuter_id: str) -> Optional[LocationAwareCommuter]:
        """Remove commuter from segment"""
        # Check inbound
        for i, commuter in enumerate(self.commuters_inbound):
            if commuter.commuter_id == commuter_id:
                return self.commuters_inbound.pop(i)
        
        # Check outbound
        for i, commuter in enumerate(self.commuters_outbound):
            if commuter.commuter_id == commuter_id:
                return self.commuters_outbound.pop(i)
        
        return None
    
    def get_commuters_by_direction(
        self,
        direction: CommuterDirection
    ) -> List[LocationAwareCommuter]:
        """Get all commuters traveling in specific direction"""
        if direction == CommuterDirection.INBOUND:
            return self.commuters_inbound
        else:
            return self.commuters_outbound
    
    def count(self) -> int:
        """Total commuters in segment"""
        return len(self.commuters_inbound) + len(self.commuters_outbound)


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
        
        # Route data from API
        self.routes: List[RouteData] = []
        
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
        """Start the route reservoir service"""
        if self.running:
            self.logger.warning("Route reservoir already running")
            return
        
        self.logger.info("Starting route reservoir service...")
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # Connect to database
        await self.db.connect()
        
        # Initialize Strapi API client and load route data
        # Strip /api suffix if present (StrapiApiClient adds it internally)
        api_base_url = self.strapi_url.rstrip('/api').rstrip('/')
        self.api_client = StrapiApiClient(api_base_url)
        await self.api_client.connect()
        
        self.logger.info("📡 Loading routes from Strapi API...")
        self.routes = await self.api_client.get_all_routes()
        
        self.logger.info(f"✅ Loaded {len(self.routes)} routes from database")
        
        # Initialize Poisson spawner with GeoJSON population data
        self.logger.info("🌍 Initializing Poisson GeoJSON spawner with population data...")
        self.poisson_spawner = PoissonGeoJSONSpawner(self.api_client)
        await self.poisson_spawner.initialize(country_code="BB")  # Barbados ISO code
        
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
        self.logger.info("📊 ROUTE RESERVOIR - INITIALIZATION COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"� Active Routes: {len(self.routes)}")
        for route in self.routes[:5]:  # Show first 5
            self.logger.info(f"   • {route.short_name}: {route.long_name} ({route.coordinate_count} points)")
        if len(self.routes) > 5:
            self.logger.info(f"   ... and {len(self.routes) - 5} more")
        self.logger.info(f"�🗺️  Grid Cell Size: {self.grid_cell_size}° (~1km)")
        self.logger.info(f"🔄 Active Grid Cells: {len(self.grid)}")
        self.logger.info(f"👥 Active Commuters: {len(self.active_commuters)}")
        self.logger.info("=" * 80)
        
        # Start background tasks
        self.expiration_task = asyncio.create_task(self._expiration_loop())
        self.spawning_task = asyncio.create_task(self._spawning_loop())
        
        self.logger.info("Route reservoir service started successfully")
    
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
    
    async def stop(self):
        """Stop the route reservoir service"""
        if not self.running:
            return
        
        self.logger.info("Stopping route reservoir service...")
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
        # Normalize locations to (float, float) tuples
        current_location = self._normalize_location(current_location)
        destination = self._normalize_location(destination)
        
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
        self.stats["total_spawned"] += 1
        
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
        
        # Log spawn details
        self.logger.info(
            f"✅ ROUTE SPAWN #{self.stats['total_spawned']} | "
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
        self.logger.info("🚀 Starting automatic route passenger spawning loop (using real GeoJSON population data)")
        
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
                
                self.logger.info(f"🎲 Poisson spawner generated {len(spawn_requests)} route spawn requests for hour {current_time.hour}")
                
                # Process spawn requests
                for request in spawn_requests:
                    try:
                        spawn_location = request.get('spawn_location')  # (lat, lon)
                        destination = request.get('destination_location')  # (lat, lon)
                        route_id = request.get('assigned_route')
                        priority = request.get('priority', 3)
                        direction = request.get('direction', 'OUTBOUND').upper()
                        
                        if not all([spawn_location, destination, route_id]):
                            self.logger.debug(f"Skipping incomplete route spawn request: spawn={spawn_location}, dest={destination}, route={route_id}")
                            continue
                        
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
                        
                    except Exception as e:
                        self.logger.error(f"Failed to process route spawn request: {e}", exc_info=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in route spawning loop: {e}")
    
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
                    grid_cell = self.commuter_cells.pop(commuter_id)
                    
                    # Remove from segment
                    if grid_cell in self.grid:
                        for segment in self.grid[grid_cell].values():
                            removed = segment.remove_commuter(commuter_id)
                            if removed:
                                segment.total_expired += 1
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
        """Get route reservoir statistics"""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
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
            "uptime_seconds": uptime,
            "total_grid_cells": len(self.grid),
            "total_segments": total_segments,
            "total_active_commuters": len(self.active_commuters),
            "total_inbound": total_inbound,
            "total_outbound": total_outbound,
            "total_spawned": self.stats["total_spawned"],
            "total_picked_up": self.stats["total_picked_up"],
            "total_expired": self.stats["total_expired"],
        }
