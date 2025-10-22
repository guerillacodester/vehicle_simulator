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
    
    def __init__(self, config: PluginConfig, api_client: Any, logger: Optional[logging.Logger] = None):
        super().__init__(config, api_client, logger)
        
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
            # Get country info
            country_data = await self.api_client.get_country_by_code(self.config.country_code)
            if not country_data:
                raise ValueError(f"Country {self.config.country_code} not found")
            
            country_id = country_data['id']
            self.logger.info(f"Loading data for {country_data['name']} (ID: {country_id})")
            
            # Load landuse zones (population)
            landuse_zones = await self.api_client.get_landuse_zones_by_country(country_id)
            self.population_zones = self._process_landuse_zones(landuse_zones)
            
            # Load POIs (amenities)
            pois = await self.api_client.get_pois_by_country(country_id)
            self.amenity_zones = self._process_poi_zones(pois)
            
            self.logger.info(
                f"Loaded {len(self.population_zones)} population zones, "
                f"{len(self.amenity_zones)} amenity zones"
            )
        
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
        """Generate spawn requests using Poisson distribution"""
        
        if not self._initialized:
            self.logger.warning("Plugin not initialized")
            return []
        
        spawn_requests = []
        current_hour = current_time.hour
        
        # Process population zones
        for zone in self.population_zones:
            try:
                spawn_rate = self._calculate_poisson_rate(
                    zone, current_hour, time_window_minutes, context
                )
                
                if spawn_rate > 0:
                    passenger_count = np.random.poisson(spawn_rate)
                    
                    if passenger_count > 0:
                        requests = await self._create_zone_spawn_requests(
                            zone, passenger_count, current_time, context, **kwargs
                        )
                        spawn_requests.extend(requests)
            
            except Exception as e:
                self.logger.error(f"Error processing population zone {zone['zone_id']}: {e}")
        
        # Process amenity zones
        for zone in self.amenity_zones:
            try:
                spawn_rate = self._calculate_poisson_rate(
                    zone, current_hour, time_window_minutes, context
                )
                
                if spawn_rate > 0:
                    passenger_count = np.random.poisson(spawn_rate)
                    
                    if passenger_count > 0:
                        requests = await self._create_zone_spawn_requests(
                            zone, passenger_count, current_time, context, **kwargs
                        )
                        spawn_requests.extend(requests)
            
            except Exception as e:
                self.logger.error(f"Error processing amenity zone {zone['zone_id']}: {e}")
        
        self._record_spawns(spawn_requests)
        
        self.logger.info(
            f"Generated {len(spawn_requests)} Poisson spawn requests "
            f"(hour={current_hour}, context={context.value})"
        )
        
        return spawn_requests
    
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
