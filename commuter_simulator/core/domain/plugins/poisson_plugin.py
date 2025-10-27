"""
Poisson GeoJSON Statistical Plugin

Statistical passenger spawning using Poisson distribution based on
GeoJSON population and land use data. This is the primary simulation
model for realistic passenger generation.

This plugin is ported from commuter_service/poisson_geojson_spawner.py
with improvements for the new architecture.
"""

import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from geopy.distance import geodesic

from commuter_simulator.core.domain.spawning_plugin import (
    BaseSpawningPlugin,
    PluginConfig,
    PluginType,
    SpawnContext,
    SpawnRequest
)


class PoissonGeoJSONPlugin(BaseSpawningPlugin):
    """
    Poisson-based statistical passenger spawning plugin.
    
    Generates passengers using Poisson distribution based on:
    - Population zones (residential, commercial, etc.)
    - Amenity zones (schools, hospitals, shopping, etc.)
    - Time of day patterns
    - Route/depot activity levels
    
    Configuration:
        config = PluginConfig(
            plugin_name="poisson_geojson",
            plugin_type=PluginType.STATISTICAL,
            country_code="BB",
            spawn_rate_multiplier=1.0,
            temporal_adjustment=True,
            use_spatial_cache=True
        )
    """
    
    def __init__(
        self, 
        config: PluginConfig, 
        api_client: Any, 
        passenger_repository: Optional[Any] = None,
        logger: Optional[logging.Logger] = None
    ):
        super().__init__(config, api_client, logger)
        
        # Database repository for persisting spawned passengers
        self.passenger_repository = passenger_repository
        
        # Will be populated during initialization
        self.population_zones: List[Dict[str, Any]] = []
        self.amenity_zones: List[Dict[str, Any]] = []
        self.routes: List[Any] = []
        self.depots: List[Any] = []
        self.spatial_cache: Optional[Any] = None
    
    async def initialize(self) -> bool:
        """Initialize plugin with geographic and population data"""
        try:
            self.logger.info(f"Initializing Poisson GeoJSON plugin for {self.config.country_code}...")
            
            # Load routes and depots from API
            self.routes = await self.api_client.get_all_routes()
            self.depots = await self.api_client.get_all_depots()
            
            self.logger.info(f"Loaded {len(self.routes)} routes, {len(self.depots)} depots")
            
            # Load geographic data
            if self.config.use_spatial_cache:
                await self._load_with_spatial_cache()
            else:
                await self._load_all_geographic_data()
            
            self._initialized = True
            self.logger.info(
                f"✅ Poisson plugin initialized: {len(self.population_zones)} population zones, "
                f"{len(self.amenity_zones)} amenity zones"
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Poisson plugin: {e}")
            return False
    
    async def _load_with_spatial_cache(self):
        """Load data using spatial cache (optimized for route-specific spawning)"""
        # TODO: Implement spatial cache loading
        # For now, fall back to loading all data
        self.logger.warning("Spatial cache not yet implemented, loading all data")
        await self._load_all_geographic_data()
    
    async def _load_all_geographic_data(self):
        """Load all geographic data for the country"""
        try:
            # For route-based spawning, we don't need to pre-load all geographic data
            # Buildings are queried on-demand in _get_buildings_near_route()
            self.logger.info(
                f"Skipping full geographic data load - using on-demand building lookup for {self.config.country_code}"
            )
            
            # Initialize empty lists (populated on-demand)
            self.population_zones = []
            self.amenity_zones = []
        
        except Exception as e:
            self.logger.error(f"Error loading geographic data: {e}")
            raise
    
    def _process_landuse_zones(self, landuse_zones: List[Dict]) -> List[Dict[str, Any]]:
        """Process landuse zones into spawning zones"""
        processed = []
        
        for zone_data in landuse_zones:
            try:
                zone_type = zone_data.get('zone_type', 'unknown')
                population_density = self._estimate_population_density(zone_type)
                
                if population_density > 0:
                    processed.append({
                        'zone_id': f"landuse_{zone_data['id']}",
                        'zone_type': zone_type,
                        'geometry': zone_data.get('geometry_geojson') or zone_data.get('geometry'),
                        'spawn_rate_per_hour': population_density * 0.1,
                        'peak_hours': self._get_peak_hours(zone_type),
                        'is_amenity': False
                    })
            except Exception as e:
                self.logger.debug(f"Skipping invalid landuse zone: {e}")
        
        return processed
    
    def _process_poi_zones(self, pois: List[Dict]) -> List[Dict[str, Any]]:
        """Process POIs into amenity zones"""
        processed = []
        
        for poi_data in pois:
            try:
                lat = poi_data.get('latitude')
                lon = poi_data.get('longitude')
                
                if lat is None or lon is None:
                    continue
                
                poi_type = poi_data.get('poi_type', 'unknown')
                activity_level = self._estimate_activity_level(poi_type)
                
                if activity_level > 0:
                    processed.append({
                        'zone_id': f"poi_{poi_data['id']}",
                        'zone_type': poi_type,
                        'center_point': (lat, lon),
                        'spawn_rate_per_hour': activity_level,
                        'peak_hours': self._get_amenity_peak_hours(poi_type),
                        'is_amenity': True
                    })
            except Exception as e:
                self.logger.debug(f"Skipping invalid POI: {e}")
        
        return processed
    
    async def generate_spawn_requests(
        self,
        current_time: datetime,
        time_window_minutes: int,
        context: SpawnContext,
        **kwargs
    ) -> List[SpawnRequest]:
        """
        Generate spawn requests using route-specific spawn-config from database.
        
        NEW IMPLEMENTATION: Uses spawn-config table with route linkage instead of
        hardcoded zone-based logic.
        """
        
        if not self._initialized:
            self.logger.warning("Plugin not initialized")
            return []
        
        # Extract route_id from kwargs (required for route-based spawning)
        route_id = kwargs.get('route_id')
        if not route_id:
            self.logger.error("route_id required for spawn generation")
            return []
        
        try:
            # Load route-specific spawn configuration from database
            from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader
            from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
            
            config_loader = SpawnConfigLoader(api_base_url=self.config.custom_params.get('strapi_url', 'http://localhost:1337/api'))
            geo_client = GeospatialClient(base_url=self.config.custom_params.get('geo_url', 'http://localhost:8001'))
            
            # Get spawn config for this route
            spawn_config = await self._get_route_spawn_config(config_loader, route_id)
            if not spawn_config:
                self.logger.warning(f"No spawn config found for route {route_id}")
                return []
            
            # Get route geometry from geospatial service (SINGLE SOURCE OF TRUTH)
            route_geom = await self._get_route_geometry(geo_client, route_id)
            if not route_geom:
                self.logger.error(f"No route geometry found for route {route_id}")
                return []
            
            # Get buildings near route
            buildings = await self._get_buildings_near_route(geo_client, route_geom, spawn_config)
            # Don't fail if no buildings - will use fallback count
            
            # Calculate spawns using spawn-config parameters
            spawn_requests = await self._generate_route_based_spawns(
                route_id=route_id,
                route_geometry=route_geom,
                buildings=buildings,
                spawn_config=spawn_config,
                config_loader=config_loader,
                current_time=current_time,
                time_window_minutes=time_window_minutes
            )
            
            self._record_spawns(spawn_requests)
            
            self.logger.info(
                f"Generated {len(spawn_requests)} spawn requests for route {route_id} "
                f"(hour={current_time.hour}, {len(buildings)} buildings)"
            )
            
            return spawn_requests
            
        except Exception as e:
            self.logger.error(f"Error generating spawn requests for route {route_id}: {e}", exc_info=True)
            return []
    
    async def _get_route_spawn_config(self, config_loader: Any, route_id: str) -> Optional[Dict]:
        """Load spawn config for route from Strapi"""
        try:
            import httpx
            
            # Query spawn-config by route document_id
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{config_loader.api_base_url}/spawn-configs?populate=*&filters[route][documentId][$eq]={route_id}"
                )
                data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                return data['data'][0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading spawn config for route {route_id}: {e}")
            return None
    
    async def _get_route_geometry(self, geo_client: Any, route_id: str) -> Optional[Dict]:
        """Get route geometry from geospatial service"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{geo_client.base_url}/spatial/route-geometry/{route_id}")
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            self.logger.error(f"Error loading route geometry for {route_id}: {e}")
            return None
    
    async def _get_buildings_near_route(self, geo_client: Any, route_geom: Dict, spawn_config: Dict) -> List[Dict]:
        """Get buildings near route using geospatial service"""
        try:
            # Get spawn radius from distribution params (database is source of truth)
            dist_params = spawn_config.get('distribution_params', {})
            if isinstance(dist_params, list) and len(dist_params) > 0:
                dist_params = dist_params[0]
            
            # Spawn radius MUST come from config
            spawn_radius = dist_params.get('spawn_radius_meters')
            if spawn_radius is None:
                self.logger.error("spawn_radius_meters not found in distribution_params - this is REQUIRED")
                return []
            
            # Extract route coordinates
            route_coords = route_geom.get('coordinates', [])
            if not route_coords or len(route_coords) < 2:
                self.logger.warning("Invalid route geometry for building lookup")
                return []
            
            # Convert from GeoJSON [lon, lat] to (lat, lon) tuples for geospatial service
            route_lat_lon = [(lat, lon) for lon, lat in route_coords]
            
            # Use geospatial service to find buildings along route
            self.logger.info(f"Querying buildings within {spawn_radius}m of route via geospatial service...")
            result = geo_client.buildings_along_route(
                route_coordinates=route_lat_lon,
                buffer_meters=spawn_radius,
                limit=200
            )
            
            buildings = result.get('buildings', [])
            self.logger.info(f"✓ Found {len(buildings)} buildings within {spawn_radius}m of route")
            
            # Convert geospatial service response to our internal format
            buildings_near_route = []
            for building in buildings:
                try:
                    buildings_near_route.append({
                        'id': building.get('id') or building.get('osm_id'),
                        'building_type': building.get('building') or building.get('building_type', 'unknown'),
                        'latitude': building.get('latitude') or building.get('lat'),
                        'longitude': building.get('longitude') or building.get('lon'),
                        'geometry': building.get('geometry')
                    })
                except Exception as e:
                    self.logger.debug(f"Skipping invalid building: {e}")
                    continue
            
            return buildings_near_route
            
        except Exception as e:
            self.logger.error(f"Error loading buildings near route: {e}", exc_info=True)
            return []
    
    async def _generate_route_based_spawns(
        self,
        route_id: str,
        route_geometry: Dict,
        buildings: List[Dict],
        spawn_config: Dict,
        config_loader: Any,
        current_time: datetime,
        time_window_minutes: int
    ) -> List[SpawnRequest]:
        """
        Generate spawns based on route-specific spawn-config.
        
        Uses:
        - Hourly spawn rates from spawn-config
        - Day multipliers from spawn-config  
        - Building count (not zone count)
        - Distribution parameters (min_interval, spawn_radius, etc.)
        
        NEW: Saves passengers directly to database via PassengerRepository.
        """
        spawn_requests = []
        
        try:
            hour = current_time.hour
            day_of_week = current_time.strftime('%A').lower()
            
            # Get ALL rates from spawn-config (database is source of truth)
            hourly_rate = config_loader.get_hourly_rate(spawn_config, hour)
            day_mult = config_loader.get_day_multiplier(spawn_config, day_of_week)
            dist_params = config_loader.get_distribution_params(spawn_config)
            
            # Validate all required parameters are present
            if not dist_params.get('passengers_per_building_per_hour'):
                self.logger.error("passengers_per_building_per_hour not in spawn config distribution_params")
                return spawn_requests
            
            # Calculate base spawns combining BOTH spatial and temporal factors
            # Spatial: building/landuse clusters provide base demand
            # Temporal: hourly_rate is a time-of-day multiplier on that base demand
            num_buildings = len(buildings) if buildings else 0
            if num_buildings == 0:
                self.logger.warning("No buildings found - using conservative estimate based on route length")
                # Estimate buildings based on route length and typical urban density
                route_coords = route_geometry.get('coordinates', [])
                route_length_km = len(route_coords) * 0.001  # Rough estimate
                num_buildings = max(5, int(route_length_km * 10))  # ~10 buildings per km as fallback
            
            passengers_per_building_per_hour = dist_params['passengers_per_building_per_hour']
            
            # Base spawns from spatial distribution (building/landuse density)
            spatial_base_spawns = num_buildings * passengers_per_building_per_hour
            
            # Apply temporal multiplier (hourly_rate) and day multiplier
            base_spawns_per_hour = spatial_base_spawns * hourly_rate * day_mult
            
            # Scale by time window (e.g., 10 minutes = 10/60 of hourly rate)
            base_spawns_for_window = base_spawns_per_hour * (time_window_minutes / 60.0)
            
            # Apply Poisson distribution
            target_spawns = int(np.random.poisson(base_spawns_for_window))
            
            # Enforce minimum spawn interval
            min_interval = dist_params.get('min_spawn_interval_seconds', 45)
            if not min_interval:
                self.logger.error("min_spawn_interval_seconds not in spawn config")
                return spawn_requests
            max_possible = int((time_window_minutes * 60) / min_interval)
            target_spawns = min(target_spawns, max_possible)
            
            self.logger.info(
                f"Route {route_id}: spatial_base={spatial_base_spawns:.1f} × hourly_rate={hourly_rate} × day_mult={day_mult} = "
                f"hourly={base_spawns_per_hour:.1f}, target_spawns={target_spawns}"
            )
            
            # Generate spawn requests and save to database
            if self.passenger_repository and target_spawns > 0:
                import uuid
                
                # Get route coordinates for spawn location selection
                route_coords = route_geometry.get('coordinates', [])
                if not route_coords or len(route_coords) < 2:
                    self.logger.error(f"Invalid route geometry for {route_id}")
                    return spawn_requests
                
                # Calculate cumulative distances along route for minimum distance enforcement
                cumulative_distances = [0.0]
                for j in range(1, len(route_coords)):
                    coord1 = route_coords[j-1]
                    coord2 = route_coords[j]
                    if coord1 and coord2 and len(coord1) >= 2 and len(coord2) >= 2:
                        segment_dist = self._haversine_distance(coord1[0], coord1[1], coord2[0], coord2[1])
                        cumulative_distances.append(cumulative_distances[-1] + segment_dist)
                    else:
                        cumulative_distances.append(cumulative_distances[-1])
                
                total_route_distance = cumulative_distances[-1] if cumulative_distances else 0
                
                # Generate spawns distributed along route
                for i in range(target_spawns):
                    try:
                        # Step 1: Randomly select boarding location along entire route
                        max_spawn_idx = len(route_coords) - 1
                        if max_spawn_idx <= 0:
                            continue
                        
                        segment_idx = np.random.randint(0, max_spawn_idx)
                        coord = route_coords[segment_idx]
                        
                        # Validate coordinates
                        if coord is None or len(coord) < 2 or coord[0] is None or coord[1] is None:
                            self.logger.warning(f"Invalid coordinates at index {segment_idx}, skipping")
                            continue
                        
                        spawn_lat, spawn_lon = coord[0], coord[1]
                        spawn_distance = cumulative_distances[segment_idx]
                        
                        # Calculate remaining distance to route end
                        remaining_distance = total_route_distance - spawn_distance
                        
                        # Step 2: Select trip distance - INDEPENDENT of boarding position
                        # Trip distance follows configured distribution regardless of where passenger boards
                        # Only constrained by: minimum trip distance and remaining route
                        
                        # Get trip distance parameters from spawn config (database is source of truth)
                        min_trip_distance = dist_params.get('min_trip_distance_meters')
                        max_trip_ratio = dist_params.get('max_trip_distance_ratio')
                        trip_mean = dist_params.get('trip_distance_mean_meters')
                        trip_std = dist_params.get('trip_distance_std_meters')
                        
                        if not all([min_trip_distance, max_trip_ratio, trip_mean, trip_std]):
                            self.logger.error(f"Missing trip distance params: min={min_trip_distance}, ratio={max_trip_ratio}, mean={trip_mean}, std={trip_std}")
                            continue
                        
                        max_trip_distance = remaining_distance * max_trip_ratio
                        
                        if max_trip_distance < min_trip_distance:
                            # Passenger is too close to end, skip
                            continue
                        
                        # Use configured normal distribution
                        # This is independent of position - the clipping handles spatial constraints naturally
                        trip_distance = np.random.normal(loc=trip_mean, scale=trip_std)
                        trip_distance = np.clip(trip_distance, min_trip_distance, max_trip_distance)
                        
                        # Step 3: Find destination at target trip distance from boarding point
                        target_dest_distance = spawn_distance + trip_distance
                        
                        # Find closest index to target distance
                        dest_idx = None
                        min_distance_diff = float('inf')
                        
                        for idx in range(segment_idx + 1, len(route_coords)):
                            dist_diff = abs(cumulative_distances[idx] - target_dest_distance)
                            if dist_diff < min_distance_diff:
                                min_distance_diff = dist_diff
                                dest_idx = idx
                        
                        if dest_idx is None or dest_idx <= segment_idx:
                            # Couldn't find valid destination
                            continue
                        
                        dest_coord = route_coords[dest_idx]
                        
                        if dest_coord is None or len(dest_coord) < 2 or dest_coord[0] is None or dest_coord[1] is None:
                            self.logger.warning(f"Invalid destination coordinates at index {dest_idx}, skipping")
                            continue
                        
                        dest_lat, dest_lon = dest_coord[0], dest_coord[1]
                        
                        # Calculate route position (distance from start)
                        route_position = self._calculate_route_position(route_coords, segment_idx)
                        
                        # Generate passenger ID
                        passenger_id = f"PASS_{uuid.uuid4().hex[:8].upper()}"
                        
                        # Save to database
                        success = await self.passenger_repository.insert_passenger(
                            passenger_id=passenger_id,
                            route_id=route_id,
                            latitude=spawn_lat,
                            longitude=spawn_lon,
                            destination_lat=dest_lat,
                            destination_lon=dest_lon,
                            destination_name=f"Stop {dest_idx}",
                            direction="OUTBOUND",
                            priority=3,
                            expires_minutes=30,
                            spawned_at=current_time
                            # Note: route_position removed - not in active-passengers schema
                        )
                        
                        if success:
                            # Create SpawnRequest for tracking
                            spawn_request = SpawnRequest(
                                passenger_id=passenger_id,
                                spawn_location=(spawn_lat, spawn_lon),
                                destination_location=(dest_lat, dest_lon),
                                route_id=route_id,
                                spawn_time=current_time,
                                spawn_context=SpawnContext.ROUTE,
                                priority=1.0,
                                generation_method="poisson_statistical"
                            )
                            spawn_requests.append(spawn_request)
                        
                    except Exception as e:
                        self.logger.error(f"Error creating spawn {i}: {e}")
                        continue
                
                self.logger.info(f"✅ Saved {len(spawn_requests)} passengers to database for route {route_id}")
            else:
                if not self.passenger_repository:
                    self.logger.warning("PassengerRepository not configured - spawns not persisted")
            
        except Exception as e:
            self.logger.error(f"Error calculating route-based spawns: {e}", exc_info=True)
        
        return spawn_requests
    
    def _calculate_route_position(self, coordinates: List[List[float]], segment_idx: int) -> float:
        """Calculate distance along route from start to segment index"""
        distance = 0.0
        for i in range(segment_idx):
            if i + 1 < len(coordinates):
                lat1, lon1 = coordinates[i]
                lat2, lon2 = coordinates[i + 1]
                distance += geodesic((lat1, lon1), (lat2, lon2)).meters
        return distance
    
    def _calculate_poisson_rate(
        self,
        zone: Dict[str, Any],
        hour: int,
        time_window_minutes: int,
        context: SpawnContext
    ) -> float:
        """Calculate Poisson lambda (rate) for a zone"""
        base_rate = zone['spawn_rate_per_hour']
        
        # Apply multipliers
        base_rate = self._apply_spawn_rate_multiplier(base_rate)
        
        # Peak hour multiplier
        peak_multiplier = 2.5 if hour in zone['peak_hours'] else 1.0
        
        # Temporal adjustment
        if self.config.temporal_adjustment:
            temporal_mult = self._get_temporal_multiplier(hour, context)
        else:
            temporal_mult = 1.0
        
        # Zone type adjustment
        zone_mult = self._get_zone_multiplier(zone['zone_type'], hour, context)
        
        # Calculate final rate
        hourly_rate = base_rate * peak_multiplier * temporal_mult * zone_mult
        time_window_rate = hourly_rate * (time_window_minutes / 60.0)
        
        return max(0.0, time_window_rate)
    
    async def _create_zone_spawn_requests(
        self,
        zone: Dict[str, Any],
        passenger_count: int,
        current_time: datetime,
        context: SpawnContext,
        **kwargs
    ) -> List[SpawnRequest]:
        """Create spawn requests for a zone"""
        requests = []
        
        for _ in range(passenger_count):
            # Find nearest route
            nearest_route = self._find_nearest_route(zone)
            if not nearest_route:
                continue
            
            # Generate spawn location
            spawn_loc = self._generate_spawn_location(zone, nearest_route)
            
            # Generate destination
            dest_loc = self._generate_destination(zone, current_time, nearest_route)
            
            request = SpawnRequest(
                passenger_id=None,  # New passenger
                spawn_location=spawn_loc,
                destination_location=dest_loc,
                route_id=nearest_route.get('id') or nearest_route.get('short_name'),
                spawn_time=current_time,
                spawn_context=context,
                zone_id=zone['zone_id'],
                zone_type=zone['zone_type'],
                trip_purpose=self._determine_trip_purpose(zone['zone_type'], current_time),
                priority=self._calculate_priority(zone['zone_type'], current_time.hour),
                generation_method='poisson_geojson',
                is_historical=False,
                plugin_name=self.config.plugin_name,
                plugin_version='2.0.0'
            )
            
            requests.append(request)
        
        return requests
    
    def _find_nearest_route(self, zone: Dict[str, Any]) -> Optional[Dict]:
        """Find nearest route to zone"""
        if not self.routes:
            return None
        
        # Get zone center
        if zone.get('center_point'):
            zone_center = zone['center_point']
        elif zone.get('geometry'):
            # TODO: Calculate centroid from geometry
            return self.routes[0] if self.routes else None
        else:
            return self.routes[0] if self.routes else None
        
        # Find closest route
        min_distance = float('inf')
        nearest_route = None
        
        for route in self.routes:
            if route.get('geometry_coordinates'):
                for coord in route['geometry_coordinates'][:10]:  # Check first 10 points
                    route_point = (coord[1], coord[0])
                    distance = geodesic(zone_center, route_point).kilometers
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_route = route
        
        return nearest_route or (self.routes[0] if self.routes else None)
    
    def _generate_spawn_location(self, zone: Dict[str, Any], route: Dict) -> Tuple[float, float]:
        """Generate spawn location (lat, lon)"""
        # For simplicity, use zone center or first route point
        if zone.get('center_point'):
            return zone['center_point']
        elif route.get('geometry_coordinates'):
            coord = route['geometry_coordinates'][0]
            return (coord[1], coord[0])
        else:
            return (13.1939, -59.5432)  # Default center of Barbados
    
    def _generate_destination(self, zone: Dict[str, Any], current_time: datetime, route: Dict) -> Tuple[float, float]:
        """Generate destination location (lat, lon)"""
        # Simple implementation: pick a point along the route
        if route.get('geometry_coordinates'):
            coords = route['geometry_coordinates']
            if len(coords) > 10:
                coord = coords[len(coords) // 2]  # Middle of route
                return (coord[1], coord[0])
        
        return (13.1939, -59.5432)  # Default
    
    def _determine_trip_purpose(self, zone_type: str, current_time: datetime) -> str:
        """Determine trip purpose based on zone and time"""
        hour = current_time.hour
        
        if 7 <= hour <= 9:
            return "commute_to_work"
        elif 17 <= hour <= 19:
            return "commute_to_home"
        elif zone_type in ['shopping', 'mall', 'market']:
            return "shopping"
        elif zone_type in ['restaurant', 'cafe']:
            return "dining"
        elif zone_type in ['school', 'university']:
            return "education"
        else:
            return "general"
    
    def _calculate_priority(self, zone_type: str, hour: int) -> float:
        """Calculate spawn priority"""
        # Higher priority for rush hours
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return 1.5
        return 1.0
    
    # Helper methods (simplified from original)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate haversine distance in meters between two coordinates"""
        import math
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _estimate_population_density(self, landuse_type: str) -> float:
        """Estimate population density (adjusted for realistic spawning)"""
        density_map = {
            'residential': 120.0,
            'urban': 170.0,
            'suburban': 60.0,
            'rural': 7.0,
            'commercial': 34.0,
            'industrial': 14.0,
            'mixed': 95.0
        }
        return density_map.get(landuse_type.lower(), 3.0)
    
    def _estimate_activity_level(self, amenity_type: str) -> float:
        """Estimate activity level for amenities"""
        activity_map = {
            'school': 0.17,
            'university': 0.27,
            'hospital': 0.17,
            'shopping': 0.23,
            'mall': 0.34,
            'restaurant': 0.13,
            'bank': 0.10
        }
        return activity_map.get(amenity_type.lower(), 0.03)
    
    def _get_peak_hours(self, zone_type: str) -> List[int]:
        """Get peak hours for zone type"""
        peak_hours_map = {
            'residential': [7, 8, 17, 18, 19],
            'commercial': [9, 10, 11, 12, 13, 14, 15, 16],
            'school': [7, 8, 15, 16]
        }
        return peak_hours_map.get(zone_type.lower(), [9, 12, 17])
    
    def _get_amenity_peak_hours(self, amenity_type: str) -> List[int]:
        """Get peak hours for amenity type"""
        amenity_peaks = {
            'school': [7, 8, 15, 16],
            'shopping': [10, 11, 12, 17, 18, 19],
            'restaurant': [12, 13, 18, 19, 20]
        }
        return amenity_peaks.get(amenity_type.lower(), [10, 14, 18])
    
    def _get_temporal_multiplier(self, hour: int, context: SpawnContext) -> float:
        """Get temporal multiplier based on context"""
        if context == SpawnContext.DEPOT:
            # Depot: peaks at rush hours
            if 7 <= hour <= 9:
                return 2.5
            elif 17 <= hour <= 19:
                return 2.0
            elif 20 <= hour <= 22:
                return 0.3
            else:
                return 1.0
        else:
            # Route: builds through day
            if 12 <= hour <= 16:
                return 1.8
            elif 10 <= hour <= 11:
                return 1.3
            else:
                return 1.0
    
    def _get_zone_multiplier(self, zone_type: str, hour: int, context: SpawnContext) -> float:
        """Get zone-specific multiplier"""
        # Simplified version
        if zone_type in ['residential', 'urban']:
            if 7 <= hour <= 9 or 17 <= hour <= 19:
                return 2.5
            return 1.0
        elif zone_type in ['commercial', 'office']:
            if 9 <= hour <= 17:
                return 2.0
            return 0.5
        else:
            return 1.0
    
    async def shutdown(self):
        """Cleanup plugin resources"""
        self.logger.info("Shutting down Poisson GeoJSON plugin")
        self.population_zones = []
        self.amenity_zones = []
        self.routes = []
        self.depots = []
        self._initialized = False
