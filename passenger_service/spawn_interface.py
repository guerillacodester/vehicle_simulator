"""
Passenger Spawning Interface
===========================

Comprehensive interface for spawning passengers at depots, along routes,
and at specific stops with different spawning strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .strapi_api_client import StrapiApiClient, DepotData, RouteData


class SpawnType(Enum):
    """Types of passenger spawning"""
    DEPOT_BASED = "depot"           # Spawn at depot locations
    ROUTE_BASED = "route"           # Spawn along route segments  
    STOP_BASED = "stop"             # Spawn at specific bus stops
    MIXED = "mixed"                 # Combination of above


@dataclass
class SpawnLocation:
    """Defines where passengers can be spawned"""
    location_id: str                    # Unique identifier
    location_type: SpawnType           # Type of spawn location
    coordinates: Dict[str, float]      # {lat: float, lon: float}
    name: str                          # Human-readable name
    capacity_factor: float = 1.0       # Spawn rate multiplier
    
    # Context data
    depot_data: Optional[DepotData] = None
    route_data: Optional[RouteData] = None
    stop_data: Optional[Dict] = None


@dataclass
class SpawnRequest:
    """Request to spawn passengers at a specific location"""
    spawn_location: SpawnLocation
    destination_location: Dict[str, float]
    passenger_count: int
    trip_purpose: str
    spawn_time: datetime
    expected_wait_time: int
    priority: float = 1.0
    
    # Route assignment (which route will serve this request)
    assigned_route: Optional[str] = None


class PassengerSpawnStrategy(ABC):
    """Abstract base class for passenger spawning strategies"""
    
    @abstractmethod
    async def get_spawn_locations(self) -> List[SpawnLocation]:
        """Get all available spawn locations for this strategy"""
        pass
    
    @abstractmethod
    async def calculate_spawn_demand(self, location: SpawnLocation, 
                                   current_time: datetime, 
                                   time_window_minutes: int) -> int:
        """Calculate passenger demand for a location in time window"""
        pass
    
    @abstractmethod
    async def generate_spawn_requests(self, current_time: datetime,
                                    time_window_minutes: int) -> List[SpawnRequest]:
        """Generate spawn requests for all locations"""
        pass


class DepotSpawnStrategy(PassengerSpawnStrategy):
    """Spawn passengers at depot locations"""
    
    def __init__(self, api_client: StrapiApiClient):
        self.api_client = api_client
        self.depots: List[DepotData] = []
        self.routes: List[RouteData] = []
    
    async def initialize(self):
        """Load depot and route data"""
        self.depots = await self.api_client.get_all_depots()
        self.routes = await self.api_client.get_all_routes()
    
    async def get_spawn_locations(self) -> List[SpawnLocation]:
        """Get depot-based spawn locations"""
        locations = []
        
        for depot in self.depots:
            if depot.location:
                location = SpawnLocation(
                    location_id=f"depot_{depot.depot_id}",
                    location_type=SpawnType.DEPOT_BASED,
                    coordinates=depot.location,
                    name=f"Depot: {depot.name}",
                    capacity_factor=depot.capacity / 100.0,  # Normalize capacity
                    depot_data=depot
                )
                locations.append(location)
        
        return locations
    
    async def calculate_spawn_demand(self, location: SpawnLocation, 
                                   current_time: datetime, 
                                   time_window_minutes: int) -> int:
        """Calculate passenger demand at depot"""
        if not location.depot_data:
            return 0
        
        # Base demand based on depot capacity and time of day
        base_demand = location.depot_data.capacity * 0.05  # 5% of capacity per hour
        time_factor = self._get_time_factor(current_time)
        
        # Adjust for time window
        demand = base_demand * time_factor * (time_window_minutes / 60.0)
        
        return max(0, int(demand))
    
    def _get_time_factor(self, current_time: datetime) -> float:
        """Get time-based demand multiplier"""
        hour = current_time.hour
        
        if 7 <= hour <= 9:      # Morning rush
            return 2.0
        elif 17 <= hour <= 19:  # Evening rush
            return 1.8
        elif 12 <= hour <= 14:  # Lunch time
            return 1.2
        elif 22 <= hour or hour <= 6:  # Night/early morning
            return 0.3
        else:                   # Regular hours
            return 1.0
    
    async def generate_spawn_requests(self, current_time: datetime,
                                    time_window_minutes: int) -> List[SpawnRequest]:
        """Generate spawn requests for all depots"""
        requests = []
        locations = await self.get_spawn_locations()
        
        for location in locations:
            demand = await self.calculate_spawn_demand(location, current_time, time_window_minutes)
            
            if demand > 0:
                # Create spawn requests
                for _ in range(demand):
                    # Pick a random route for destination
                    route = self._select_destination_route()
                    if route:
                        destination = self._get_route_destination(route)
                        
                        request = SpawnRequest(
                            spawn_location=location,
                            destination_location=destination,
                            passenger_count=1,
                            trip_purpose=self._determine_trip_purpose(current_time),
                            spawn_time=current_time,
                            expected_wait_time=self._estimate_wait_time(current_time),
                            assigned_route=route.short_name
                        )
                        requests.append(request)
        
        return requests
    
    def _select_destination_route(self) -> Optional[RouteData]:
        """Select a random route for passenger destination"""
        if not self.routes:
            return None
        
        import random
        return random.choice(self.routes)
    
    def _get_route_destination(self, route: RouteData) -> Dict[str, float]:
        """Get random destination along route"""
        if route.geometry_coordinates:
            import random
            lon, lat = random.choice(route.geometry_coordinates)
            return {'lat': lat, 'lon': lon}
        
        return {'lat': 13.1939, 'lon': -59.5432}  # Default Barbados location
    
    def _determine_trip_purpose(self, current_time: datetime) -> str:
        """Determine trip purpose based on time"""
        hour = current_time.hour
        
        if 6 <= hour <= 9:
            return 'work'
        elif 15 <= hour <= 17:
            return 'school'
        elif 12 <= hour <= 14:
            return 'shopping'
        elif 17 <= hour <= 20:
            return 'home'
        else:
            return 'recreation'
    
    def _estimate_wait_time(self, current_time: datetime) -> int:
        """Estimate wait time based on time of day"""
        hour = current_time.hour
        
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hour
            return 8  # Frequent service
        elif 22 <= hour or hour <= 6:  # Night
            return 25  # Infrequent service
        else:
            return 15  # Regular service


class RouteSpawnStrategy(PassengerSpawnStrategy):
    """Spawn passengers along route segments"""
    
    def __init__(self, api_client: StrapiApiClient):
        self.api_client = api_client
        self.routes: List[RouteData] = []
    
    async def initialize(self):
        """Load route data"""
        self.routes = await self.api_client.get_all_routes()
    
    async def get_spawn_locations(self) -> List[SpawnLocation]:
        """Get route-based spawn locations"""
        locations = []
        
        for route in self.routes:
            if route.geometry_coordinates:
                # Create spawn locations along route at regular intervals
                coordinate_count = len(route.geometry_coordinates)
                
                # Sample every 10th coordinate or minimum 5 locations per route
                step = max(1, coordinate_count // max(5, coordinate_count // 10))
                
                for i in range(0, coordinate_count, step):
                    lon, lat = route.geometry_coordinates[i]
                    
                    location = SpawnLocation(
                        location_id=f"route_{route.short_name}_pt_{i}",
                        location_type=SpawnType.ROUTE_BASED,
                        coordinates={'lat': lat, 'lon': lon},
                        name=f"Route {route.short_name} - Point {i//step + 1}",
                        capacity_factor=1.0,
                        route_data=route
                    )
                    locations.append(location)
        
        return locations
    
    async def calculate_spawn_demand(self, location: SpawnLocation, 
                                   current_time: datetime, 
                                   time_window_minutes: int) -> int:
        """Calculate passenger demand along route"""
        if not location.route_data:
            return 0
        
        # Base demand based on route characteristics
        route_length = location.route_data.route_length_km
        base_demand_per_km = 2.0  # passengers per km per hour
        
        time_factor = self._get_time_factor(current_time)
        
        # Calculate demand for this specific point
        demand = base_demand_per_km * time_factor * (time_window_minutes / 60.0)
        
        return max(0, int(demand))
    
    def _get_time_factor(self, current_time: datetime) -> float:
        """Get time-based demand multiplier for routes"""
        hour = current_time.hour
        
        if 7 <= hour <= 9:      # Morning rush - people going to work
            return 1.5
        elif 17 <= hour <= 19:  # Evening rush - people going home
            return 1.8
        elif 12 <= hour <= 14:  # Lunch time
            return 0.8
        elif 22 <= hour or hour <= 6:  # Night/early morning
            return 0.2
        else:                   # Regular hours
            return 1.0
    
    async def generate_spawn_requests(self, current_time: datetime,
                                    time_window_minutes: int) -> List[SpawnRequest]:
        """Generate spawn requests along routes"""
        requests = []
        locations = await self.get_spawn_locations()
        
        for location in locations:
            demand = await self.calculate_spawn_demand(location, current_time, time_window_minutes)
            
            if demand > 0:
                # Create spawn requests
                for _ in range(demand):
                    # Destination is further along the same route
                    destination = self._get_forward_destination(location)
                    
                    request = SpawnRequest(
                        spawn_location=location,
                        destination_location=destination,
                        passenger_count=1,
                        trip_purpose=self._determine_trip_purpose(current_time),
                        spawn_time=current_time,
                        expected_wait_time=self._estimate_wait_time(current_time),
                        assigned_route=location.route_data.short_name
                    )
                    requests.append(request)
        
        return requests
    
    def _get_forward_destination(self, location: SpawnLocation) -> Dict[str, float]:
        """Get destination further along the route"""
        if not location.route_data or not location.route_data.geometry_coordinates:
            return location.coordinates
        
        # Find current position in route coordinates
        current_coords = [location.coordinates['lon'], location.coordinates['lat']]
        coordinates = location.route_data.geometry_coordinates
        
        # Find closest coordinate index
        min_distance = float('inf')
        current_index = 0
        
        for i, coord in enumerate(coordinates):
            distance = ((coord[0] - current_coords[0])**2 + (coord[1] - current_coords[1])**2)**0.5
            if distance < min_distance:
                min_distance = distance
                current_index = i
        
        # Pick destination 20-80% forward along route
        import random
        forward_percent = random.uniform(0.2, 0.8)
        remaining_coords = len(coordinates) - current_index
        forward_steps = int(remaining_coords * forward_percent)
        
        destination_index = min(len(coordinates) - 1, current_index + max(1, forward_steps))
        lon, lat = coordinates[destination_index]
        
        return {'lat': lat, 'lon': lon}
    
    def _determine_trip_purpose(self, current_time: datetime) -> str:
        """Determine trip purpose for route-based spawning"""
        hour = current_time.hour
        
        if 7 <= hour <= 9:
            return 'work'
        elif 15 <= hour <= 17:
            return 'school'
        elif 10 <= hour <= 14:
            return 'shopping'
        elif 17 <= hour <= 20:
            return 'home'
        else:
            return 'social'
    
    def _estimate_wait_time(self, current_time: datetime) -> int:
        """Estimate wait time for route stops"""
        hour = current_time.hour
        
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hour
            return 12  # More frequent during rush
        elif 22 <= hour or hour <= 6:  # Night
            return 30  # Less frequent at night
        else:
            return 18  # Regular service


class MixedSpawnStrategy(PassengerSpawnStrategy):
    """Combines depot and route spawning strategies"""
    
    def __init__(self, api_client: StrapiApiClient, depot_weight: float = 0.3, route_weight: float = 0.7):
        self.depot_strategy = DepotSpawnStrategy(api_client)
        self.route_strategy = RouteSpawnStrategy(api_client)
        self.depot_weight = depot_weight
        self.route_weight = route_weight
    
    async def initialize(self):
        """Initialize both strategies"""
        await self.depot_strategy.initialize()
        await self.route_strategy.initialize()
    
    async def get_spawn_locations(self) -> List[SpawnLocation]:
        """Get all spawn locations from both strategies"""
        depot_locations = await self.depot_strategy.get_spawn_locations()
        route_locations = await self.route_strategy.get_spawn_locations()
        
        return depot_locations + route_locations
    
    async def calculate_spawn_demand(self, location: SpawnLocation, 
                                   current_time: datetime, 
                                   time_window_minutes: int) -> int:
        """Calculate demand based on location type"""
        if location.location_type == SpawnType.DEPOT_BASED:
            return await self.depot_strategy.calculate_spawn_demand(location, current_time, time_window_minutes)
        elif location.location_type == SpawnType.ROUTE_BASED:
            return await self.route_strategy.calculate_spawn_demand(location, current_time, time_window_minutes)
        else:
            return 0
    
    async def generate_spawn_requests(self, current_time: datetime,
                                    time_window_minutes: int) -> List[SpawnRequest]:
        """Generate spawn requests from both strategies with weighting"""
        depot_requests = await self.depot_strategy.generate_spawn_requests(current_time, time_window_minutes)
        route_requests = await self.route_strategy.generate_spawn_requests(current_time, time_window_minutes)
        
        # Apply weighting to requests
        weighted_depot = int(len(depot_requests) * self.depot_weight) if depot_requests else 0
        weighted_route = int(len(route_requests) * self.route_weight) if route_requests else 0
        
        final_requests = []
        final_requests.extend(depot_requests[:weighted_depot])
        final_requests.extend(route_requests[:weighted_route])
        
        return final_requests


class PassengerSpawnManager:
    """Main manager for passenger spawning with multiple strategies"""
    
    def __init__(self, api_client: StrapiApiClient, strategy: PassengerSpawnStrategy):
        self.api_client = api_client
        self.strategy = strategy
        self._initialized = False
    
    async def initialize(self):
        """Initialize the spawn manager and strategy"""
        await self.strategy.initialize()
        self._initialized = True
    
    async def spawn_passengers(self, current_time: datetime, 
                             time_window_minutes: int = 5) -> List[SpawnRequest]:
        """Generate passenger spawn requests using active strategy"""
        if not self._initialized:
            raise RuntimeError("SpawnManager not initialized. Call initialize() first.")
        
        return await self.strategy.generate_spawn_requests(current_time, time_window_minutes)
    
    async def get_spawn_statistics(self) -> Dict[str, Any]:
        """Get statistics about spawn locations and capacity"""
        if not self._initialized:
            return {"error": "Not initialized"}
        
        locations = await self.strategy.get_spawn_locations()
        
        stats = {
            "total_locations": len(locations),
            "location_types": {},
            "locations_by_type": {}
        }
        
        for location in locations:
            loc_type = location.location_type.value
            if loc_type not in stats["location_types"]:
                stats["location_types"][loc_type] = 0
                stats["locations_by_type"][loc_type] = []
            
            stats["location_types"][loc_type] += 1
            stats["locations_by_type"][loc_type].append({
                "id": location.location_id,
                "name": location.name,
                "coordinates": location.coordinates,
                "capacity_factor": location.capacity_factor
            })
        
        return stats