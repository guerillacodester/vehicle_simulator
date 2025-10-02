"""
Depot-Aware Passenger Spawning System
=====================================

This system integrates with depot and route data via dedicated API client
to spawn passengers at realistic frequencies based on:
- Depot locations and capacity
- Route characteristics (urban vs rural, length, complexity)
- Time-based patterns specific to each depot
- Route-specific passenger demand patterns

Uses StrapiApiClient as single source of truth for all API access.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, time
import json
import math
from dataclasses import dataclass

from .strapi_api_client import StrapiApiClient, DepotData, RouteData

@dataclass
class EnhancedDepotInfo:
    """Enhanced depot information with route assignments"""
    depot_data: DepotData
    routes: List[str] = None  # Route codes served by this depot
    
    @property
    def depot_id(self) -> str:
        return self.depot_data.depot_id
    
    @property
    def name(self) -> str:
        return self.depot_data.name
    
    @property
    def location(self) -> Optional[Dict[str, float]]:
        return self.depot_data.location
    
    @property
    def capacity(self) -> int:
        return self.depot_data.capacity
    
    @property
    def is_active(self) -> bool:
        return self.depot_data.is_active

@dataclass
class EnhancedRouteInfo:
    """Enhanced route information with calculated characteristics"""
    route_data: RouteData
    
    # Calculated properties
    route_complexity: float = 1.0  # 1.0 = simple, 2.0 = complex
    urban_ratio: float = 0.5  # 0.0 = rural, 1.0 = urban
    tourist_ratio: float = 0.0  # 0.0 = local, 1.0 = tourist
    
    @property
    def short_name(self) -> str:
        return self.route_data.short_name
    
    @property
    def long_name(self) -> str:
        return self.route_data.long_name
    
    @property
    def coordinates(self) -> List[List[float]]:
        return self.route_data.geometry_coordinates
    
    @property
    def route_length_km(self) -> float:
        return self.route_data.route_length_km
    
    @property
    def coordinate_count(self) -> int:
        return self.route_data.coordinate_count
    
    @property
    def description(self) -> Optional[str]:
        return self.route_data.description
    
    @property
    def parishes(self) -> Optional[List[str]]:
        return self.route_data.parishes
    
    @property
    def is_active(self) -> bool:
        return self.route_data.is_active

@dataclass
class PassengerSpawnRequest:
    """Request to spawn passengers for a specific route/depot"""
    depot_info: EnhancedDepotInfo
    route_info: EnhancedRouteInfo
    spawn_location: Dict[str, float]  # {lat: float, lon: float}
    destination_location: Dict[str, float]
    trip_purpose: str
    spawn_time: datetime
    expected_wait_time: int  # minutes
    priority: float = 1.0

class DepotPassengerSpawner:
    """Spawns passengers based on depot and route data via StrapiApiClient"""
    
    def __init__(self, strapi_base_url: str = "http://localhost:1337"):
        self.api_client = StrapiApiClient(strapi_base_url)
        self.depots: Dict[str, EnhancedDepotInfo] = {}
        self.routes: Dict[str, EnhancedRouteInfo] = {}
        self.depot_routes: Dict[str, List[str]] = {}  # depot_id -> [route_ids]
        self.active_country_plugin = None
        
    async def initialize(self, country_plugin=None) -> bool:
        """Initialize with depot and route data via API client"""
        try:
            self.active_country_plugin = country_plugin
            
            # Connect to API
            if not await self.api_client.connect():
                logging.error("❌ Failed to connect to Strapi API")
                return False
            
            # Load depot data
            await self._load_depots()
            
            # Load route data
            await self._load_routes()
            
            # Calculate route characteristics
            self._calculate_route_characteristics()
            
            # Map depots to routes (simplified - assume all depots serve all routes for now)
            self._map_depots_to_routes()
            
            logging.info(f"✅ Initialized depot spawner: {len(self.depots)} depots, {len(self.routes)} routes")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize depot spawner: {e}")
            return False
    
    async def close(self):
        """Close API client connection"""
        await self.api_client.close()
    
    async def _load_depots(self):
        """Load depot data via API client"""
        try:
            depot_list = await self.api_client.get_all_depots()
            
            for depot_data in depot_list:
                enhanced_depot = EnhancedDepotInfo(
                    depot_data=depot_data,
                    routes=[]  # Will be populated later
                )
                self.depots[depot_data.depot_id] = enhanced_depot
                
            logging.info(f"✅ Loaded {len(self.depots)} depots via API client")
                
        except Exception as e:
            logging.error(f"❌ Failed to load depots: {e}")
    
    async def _load_routes(self):
        """Load route data via API client with GTFS geometry"""
        try:
            route_list = await self.api_client.get_all_routes()
            
            for route_data in route_list:
                enhanced_route = EnhancedRouteInfo(route_data=route_data)
                self.routes[route_data.short_name] = enhanced_route
                    
            logging.info(f"✅ Loaded {len(self.routes)} routes with GTFS geometry via API client")
                
        except Exception as e:
            logging.error(f"❌ Failed to load routes: {e}")
    
    def _calculate_route_characteristics(self):
        """Calculate route characteristics from GTFS geometry data"""
        for route_id, route in self.routes.items():
            coordinates = route.coordinates
            total_length = route.route_length_km
            
            if coordinates and len(coordinates) > 2:
                # Calculate complexity based on coordinate density and turns
                if total_length > 0:
                    coordinate_density = len(coordinates) / total_length  # points per km
                    route.route_complexity = min(2.0, 1.0 + coordinate_density / 10.0)  # More points = more complex
                
                # Estimate urban/rural ratio based on coordinate density
                if total_length > 0:
                    # Urban areas have higher coordinate density in GTFS data
                    coordinate_density = len(coordinates) / total_length
                    route.urban_ratio = min(1.0, coordinate_density / 15.0)  # Normalize to 0-1
                
                # Estimate tourist ratio based on route name and location patterns
                route.tourist_ratio = self._estimate_tourist_ratio(route)
                
                logging.debug(f"Route {route_id}: {total_length:.1f}km, {len(coordinates)} points, "
                            f"complexity={route.route_complexity:.1f}, urban={route.urban_ratio:.1f}, tourist={route.tourist_ratio:.1f}")
    
    def _calculate_linestring_length(self, coordinates: List[List[float]]) -> float:
        """Calculate length of a LineString in kilometers using Haversine formula"""
        total_length = 0.0
        
        for i in range(len(coordinates) - 1):
            lon1, lat1 = coordinates[i]
            lon2, lat2 = coordinates[i + 1]
            distance = self._haversine_distance(lat1, lon1, lat2, lon2)
            total_length += distance
        
        return total_length
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula (km)"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _estimate_tourist_ratio(self, route: EnhancedRouteInfo) -> float:
        """Estimate tourist ratio based on route characteristics"""
        tourist_keywords = ['beach', 'coast', 'cruise', 'airport', 'tourist', 'hotel', 'resort']
        
        # Check route name and description
        text_to_check = f"{route.short_name} {route.long_name or ''} {route.description or ''}".lower()
        
        tourist_score = 0.0
        for keyword in tourist_keywords:
            if keyword in text_to_check:
                tourist_score += 0.2
        
        # Check parishes (some parishes are more touristy)
        if route.parishes:
            tourist_parishes = ['christ church', 'st. james', 'st. peter']  # Example for Barbados
            for parish in route.parishes:
                if parish.lower() in tourist_parishes:
                    tourist_score += 0.3
        
        return min(1.0, tourist_score)
    
    def _map_depots_to_routes(self):
        """Map depots to routes they serve (simplified for now)"""
        # For now, assume all active depots serve all active routes
        # In a real system, this would be based on actual depot-route assignments
        for depot_id in self.depots.keys():
            self.depot_routes[depot_id] = list(self.routes.keys())
    
    async def generate_passenger_spawn_requests(self, current_time: datetime, 
                                              time_window_minutes: int = 5) -> List[PassengerSpawnRequest]:
        """Generate passenger spawn requests for all depots and routes"""
        spawn_requests = []
        
        try:
            for depot_id, depot in self.depots.items():
                if not depot.is_active:
                    continue
                
                # Get routes served by this depot
                route_ids = self.depot_routes.get(depot_id, [])
                
                for route_id in route_ids:
                    route = self.routes.get(route_id)
                    if not route or not route.is_active:
                        continue
                    
                    # Calculate spawn rate for this depot-route combination
                    spawn_rate = self._calculate_spawn_rate(depot, route, current_time)
                    
                    # Calculate number of passengers to spawn in this time window
                    passengers_to_spawn = self._calculate_passengers_to_spawn(
                        spawn_rate, time_window_minutes, depot.capacity
                    )
                    
                    # Generate spawn requests
                    for _ in range(passengers_to_spawn):
                        spawn_request = await self._create_spawn_request(depot, route, current_time)
                        if spawn_request:
                            spawn_requests.append(spawn_request)
            
            logging.debug(f"Generated {len(spawn_requests)} passenger spawn requests")
            return spawn_requests
            
        except Exception as e:
            logging.error(f"❌ Error generating spawn requests: {e}")
            return []
    
    def _calculate_spawn_rate(self, depot: EnhancedDepotInfo, route: EnhancedRouteInfo, current_time: datetime) -> float:
        """Calculate passenger spawn rate for depot-route combination"""
        # Base spawn rate from country plugin
        base_rate = 0.15  # passengers per minute per location
        if self.active_country_plugin:
            plugin_config = self.active_country_plugin.plugin_config
            base_rate = plugin_config.get('base_spawn_rate', 0.15)
        
        # Apply cultural/time-based modifiers
        time_modifier = 1.0
        if self.active_country_plugin:
            time_modifier = self.active_country_plugin.get_spawn_rate_modifier(
                current_time, self._get_depot_location_type(depot)
            )
        
        # Apply depot capacity modifier
        capacity_modifier = math.log10(max(10, depot.capacity)) / 2.0  # Larger depots = more passengers
        
        # Apply route characteristics modifiers
        route_modifier = (
            route.route_complexity *  # Complex routes = more passengers
            (1.0 + route.urban_ratio * 0.5) *  # Urban routes = more passengers
            (1.0 + route.tourist_ratio * 0.3)  # Tourist routes = slightly more passengers
        )
        
        # Apply route length modifier (longer routes = more intermediate stops)
        length_modifier = min(2.0, 1.0 + route.route_length_km / 20.0)
        
        final_rate = base_rate * time_modifier * capacity_modifier * route_modifier * length_modifier
        
        logging.debug(f"Spawn rate for {depot.name} -> {route.short_name}: {final_rate:.3f} "
                     f"(base={base_rate:.2f}, time={time_modifier:.2f}, capacity={capacity_modifier:.2f}, "
                     f"route={route_modifier:.2f}, length={length_modifier:.2f})")
        
        return final_rate
    
    def _get_depot_location_type(self, depot: EnhancedDepotInfo) -> str:
        """Determine location type for depot based on name/characteristics"""
        name_lower = depot.name.lower()
        
        if any(word in name_lower for word in ['airport', 'cruise', 'port']):
            return 'tourist'
        elif any(word in name_lower for word in ['city', 'town', 'bridge']):
            return 'commercial'
        elif any(word in name_lower for word in ['industrial', 'factory']):
            return 'business'
        else:
            return 'general'
    
    def _calculate_passengers_to_spawn(self, spawn_rate: float, time_window_minutes: int, 
                                     depot_capacity: int) -> int:
        """Calculate number of passengers to spawn in time window"""
        # Expected passengers in time window
        expected_passengers = spawn_rate * time_window_minutes
        
        # Add some randomness using Poisson distribution approximation
        import random
        actual_passengers = max(0, int(random.normalvariate(expected_passengers, 
                                                           math.sqrt(expected_passengers))))
        
        # Cap at reasonable limit based on depot capacity
        max_passengers = max(1, depot_capacity // 10)  # Max 10% of depot capacity per time window
        
        return min(actual_passengers, max_passengers)
    
    async def _create_spawn_request(self, depot: EnhancedDepotInfo, route: EnhancedRouteInfo,
                                   current_time: datetime) -> Optional[PassengerSpawnRequest]:
        """Create a passenger spawn request for depot-route combination"""
        try:
            # Get spawn location (depot location for now, could be route stops later)
            spawn_location = self._get_spawn_location(depot, route)
            if not spawn_location:
                return None
            
            # Get destination location (random point along route for now)
            destination_location = self._get_destination_location(route)
            if not destination_location:
                return None
            
            # Determine trip purpose based on time and cultural patterns
            trip_purpose = self._determine_trip_purpose(current_time, depot, route)
            
            # Estimate wait time based on route characteristics
            expected_wait_time = self._estimate_wait_time(route, current_time)
            
            # Calculate priority based on trip purpose and time sensitivity
            priority = self._calculate_priority(trip_purpose, current_time)
            
            return PassengerSpawnRequest(
                depot_info=depot,
                route_info=route,
                spawn_location=spawn_location,
                destination_location=destination_location,
                trip_purpose=trip_purpose,
                spawn_time=current_time,
                expected_wait_time=expected_wait_time,
                priority=priority
            )
            
        except Exception as e:
            logging.error(f"❌ Error creating spawn request: {e}")
            return None
    
    def _get_spawn_location(self, depot: EnhancedDepotInfo, route: EnhancedRouteInfo) -> Optional[Dict[str, float]]:
        """Get passenger spawn location (depot or nearby route stop)"""
        if depot.location and 'lat' in depot.location and 'lon' in depot.location:
            return depot.location
        
        # Fallback: extract first coordinate from route if depot has no location
        coordinates = route.coordinates
        if coordinates and len(coordinates) > 0:
            lon, lat = coordinates[0]
            return {'lat': lat, 'lon': lon}
        
        # Default Barbados location if nothing else available
        return {'lat': 13.1939, 'lon': -59.5432}
    
    def _get_destination_location(self, route: EnhancedRouteInfo) -> Optional[Dict[str, float]]:
        """Get passenger destination location (random point along route)"""
        coordinates = route.coordinates
        
        if coordinates and len(coordinates) > 0:
            # Pick a random coordinate as destination
            import random
            lon, lat = random.choice(coordinates)
            return {'lat': lat, 'lon': lon}
        
        # Fallback: use default Barbados location
        return {'lat': 13.1939, 'lon': -59.5432}
    
    def _determine_trip_purpose(self, current_time: datetime, depot: EnhancedDepotInfo,
                               route: EnhancedRouteInfo) -> str:
        """Determine trip purpose based on context"""
        if self.active_country_plugin:
            purposes = self.active_country_plugin.get_trip_purpose_distribution(
                current_time, self._get_depot_location_type(depot)
            )
            # Pick purpose based on weighted random selection
            import random
            rand_val = random.random()
            cumulative = 0.0
            
            for purpose, weight in purposes.items():
                cumulative += weight
                if rand_val <= cumulative:
                    return purpose
        
        # Fallback purposes based on time
        hour = current_time.hour
        if 6 <= hour <= 9:
            return 'work'
        elif 12 <= hour <= 14:
            return 'shopping'
        elif 15 <= hour <= 17:
            return 'school'
        elif 17 <= hour <= 20:
            return 'social'
        else:
            return 'recreation'
    
    def _estimate_wait_time(self, route: EnhancedRouteInfo, current_time: datetime) -> int:
        """Estimate passenger wait time based on route characteristics"""
        # Base wait time depends on route complexity and time of day
        base_wait = 10  # minutes
        
        # Complex routes = longer wait times
        complexity_factor = route.route_complexity
        
        # Rush hour = shorter wait times (more frequent service)
        hour = current_time.hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            time_factor = 0.7
        elif 22 <= hour or hour <= 6:
            time_factor = 1.5  # Less frequent night service
        else:
            time_factor = 1.0
        
        return int(base_wait * complexity_factor * time_factor)
    
    def _calculate_priority(self, trip_purpose: str, current_time: datetime) -> float:
        """Calculate passenger priority based on trip purpose and timing"""
        purpose_priorities = {
            'work': 1.0,
            'school': 0.9,
            'medical': 1.2,
            'shopping': 0.6,
            'recreation': 0.4,
            'social': 0.5
        }
        
        base_priority = purpose_priorities.get(trip_purpose, 0.5)
        
        # Increase priority during rush hours
        hour = current_time.hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            base_priority *= 1.3
        
        return base_priority