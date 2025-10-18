"""
Poisson-Based GeoJSON Passenger Spawning System
==============================================

Statistical passenger spawning using Poisson distribution based on
GeoJSON population and land use data for realistic passenger patterns.
"""

import asyncio
import logging
import json
import random
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon, shape
from shapely.ops import unary_union

from .strapi_api_client import StrapiApiClient, DepotData, RouteData
from .simple_spatial_cache import SimpleSpatialZoneCache


@dataclass
class GeoJSONFeature:
    """Represents a GeoJSON feature with population/activity data"""
    geometry: Any  # Shapely geometry object
    properties: Dict[str, Any]
    feature_type: str  # 'residential', 'commercial', 'amenity', etc.
    population_density: float = 0.0
    activity_multiplier: float = 1.0


@dataclass 
class PopulationZone:
    """Population zone with spawn probability"""
    zone_id: str
    center_point: Tuple[float, float]  # (lat, lon)
    geometry: Any  # Shapely geometry
    base_population: int
    zone_type: str  # residential, commercial, industrial, etc.
    spawn_rate_per_hour: float  # Poisson lambda parameter
    peak_hours: List[int]  # Hours with higher activity


class GeoJSONDataLoader:
    """Loads and processes GeoJSON data from Strapi API for population-based spawning"""
    
    def __init__(self, api_client: StrapiApiClient):
        self.api_client = api_client
        self.population_zones: List[PopulationZone] = []
        self.amenity_zones: List[PopulationZone] = []
        self.transport_hubs: List[Dict[str, Any]] = []
        self.country_id: Optional[int] = None
        
    async def load_geojson_data(self, country_code: str = "barbados") -> bool:
        """Load all GeoJSON data from Strapi API for a country"""
        try:
            # Get country information
            country_data = await self.api_client.get_country_by_code(country_code.upper())
            if not country_data:
                logging.error(f"❌ Country {country_code} not found in database")
                return False
            
            self.country_id = country_data['id']
            logging.info(f"[INIT] Loading geographic data for {country_data['name']} (ID: {self.country_id})")
            
            # Load different types of GeoJSON data from API
            await self._load_landuse_data_from_api()
            await self._load_amenities_data_from_api()
            await self._load_places_data_from_api()
            await self._load_regions_data_from_api()
            
            logging.info(f"[OK] Loaded GeoJSON data from API: {len(self.population_zones)} population zones, "
                        f"{len(self.amenity_zones)} amenity zones, {len(self.transport_hubs)} transport hubs")
            return True
            
        except Exception as e:
            logging.error(f"[ERROR] Failed to load GeoJSON data from API: {e}")
            return False
    
    async def _load_landuse_data_from_api(self):
        """Load land use data from Strapi API for population estimation"""
        if not self.country_id:
            logging.warning("No country ID set for landuse data loading")
            return
            
        landuse_zones = await self.api_client.get_landuse_zones_by_country(self.country_id)
        logging.info(f"[LANDUSE] Loading {len(landuse_zones)} landuse zones from API")
        
        for zone_data in landuse_zones:
            try:
                # Extract geometry from Strapi format (Strapi uses 'geometry_geojson' field)
                geometry_data = zone_data.get('geometry_geojson') or zone_data.get('geometry')
                if not geometry_data:
                    continue
                
                geometry = shape(geometry_data)
                
                # Extract landuse type (database uses 'zone_type' field)
                landuse_type = zone_data.get('zone_type', 'unknown')
                
                # Calculate population density based on land use
                population_density = self._estimate_population_density(landuse_type)
                
                if population_density > 0:
                    # Create population zone
                    zone = PopulationZone(
                        zone_id=f"landuse_{zone_data['id']}",
                        center_point=self._get_geometry_center(geometry),
                        geometry=geometry,
                        base_population=int(geometry.area * 1000000 * population_density),  # Rough estimate
                        zone_type=landuse_type,
                        spawn_rate_per_hour=population_density * 0.1,  # Base spawn rate
                        peak_hours=self._get_peak_hours(landuse_type)
                    )
                    self.population_zones.append(zone)
                    
            except Exception as e:
                logging.debug(f"Skipping invalid landuse zone {zone_data.get('id', 'unknown')}: {e}")
    
    async def _load_amenities_data_from_api(self):
        """Load amenities data from Strapi API for activity-based spawning"""
        if not self.country_id:
            logging.warning("No country ID set for amenities data loading")
            return
            
        pois = await self.api_client.get_pois_by_country(self.country_id)
        logging.info(f"[POI] Loading {len(pois)} POIs from API")
        
        for poi_data in pois:
            try:
                # Create point geometry from lat/lon
                lat = poi_data.get('latitude')
                lon = poi_data.get('longitude')
                if lat is None or lon is None:
                    continue
                
                geometry = Point(lon, lat)  # Point(x, y) = Point(lon, lat)
                
                # Extract amenity/POI type
                poi_type = poi_data.get('poi_type', 'unknown')
                
                # Calculate activity multiplier
                activity_level = self._estimate_activity_level(poi_type, poi_data)
                
                if activity_level > 0:
                    zone = PopulationZone(
                        zone_id=f"poi_{poi_data['id']}",
                        center_point=(lat, lon),
                        geometry=geometry,
                        base_population=0,  # POIs don't have residential population
                        zone_type=poi_type,
                        spawn_rate_per_hour=activity_level,
                        peak_hours=self._get_amenity_peak_hours(poi_type)
                    )
                    self.amenity_zones.append(zone)
                    
            except Exception as e:
                logging.debug(f"Skipping invalid POI {poi_data.get('id', 'unknown')}: {e}")
    
    async def _load_places_data_from_api(self):
        """Load place names from Strapi API for enhanced zone identification"""
        if not self.country_id:
            logging.warning("No country ID set for places data loading")
            return
            
        places = await self.api_client.get_places_by_country(self.country_id)
        logging.info(f"[PLACE] Loading {len(places)} places from API")
        
        # Use places data to enhance existing zones with better identification
        for place_data in places:
            try:
                # Create point geometry from lat/lon or use geometry if available
                geometry_data = place_data.get('geometry_geojson') or place_data.get('geometry')
                lat = place_data.get('latitude')
                lon = place_data.get('longitude')
                
                if geometry_data:
                    geometry = shape(geometry_data)
                elif lat is not None and lon is not None:
                    geometry = Point(lon, lat)
                else:
                    continue
                
                name = place_data.get('name', '')
                place_type = place_data.get('place_type', 'unknown')
                
                # Enhance nearby population zones with place names
                center = self._get_geometry_center(geometry)
                self._enhance_nearby_zones(center, name, place_type)
                
            except Exception as e:
                logging.debug(f"Skipping invalid place {place_data.get('id', 'unknown')}: {e}")
    
    async def _load_regions_data_from_api(self):
        """Load regions from Strapi API as administrative boundaries"""
        if not self.country_id:
            logging.warning("No country ID set for regions data loading")
            return
            
        regions = await self.api_client.get_regions_by_country(self.country_id)
        logging.info(f"[REGION] Loading {len(regions)} regions from API")
        
        for region_data in regions:
            try:
                # Extract geometry from Strapi format (Strapi uses 'geometry_geojson' field)
                geometry_data = region_data.get('geometry_geojson') or region_data.get('geometry')
                if not geometry_data:
                    continue
                
                geometry = shape(geometry_data)
                
                region_info = {
                    'id': f"region_{region_data['id']}",
                    'name': region_data.get('name', f"Region {region_data['id']}"),
                    'coordinates': self._get_geometry_center(geometry),
                    'type': 'administrative_region',
                    'geometry': geometry,
                    'region_type': region_data.get('region_type', 'unknown')
                }
                self.transport_hubs.append(region_info)  # Using transport_hubs for now
                
            except Exception as e:
                logging.debug(f"Skipping invalid bus stop feature: {e}")
    
    def _estimate_population_density(self, landuse_type: str) -> float:
        """Estimate population density based on land use type
        
        ADJUSTED DENSITIES (2024-10-13): Reduced by ~18x (6x * 3x) for realistic spawn rates.
        These represent effective transit-using population, not total population.
        Target: 90-180 passengers/hour total at 8 PM
        """
        density_map = {
            'residential': 120.0,   # Was 350.0 (orig 2000.0) - not everyone uses transit
            'urban': 170.0,         # Was 500.0 (orig 3000.0)
            'suburban': 60.0,       # Was 180.0 (orig 1000.0) - lower transit usage
            'rural': 7.0,           # Was 20.0 (orig 100.0) - minimal transit
            'village': 48.0,        # Was 140.0 (orig 800.0)
            'town': 85.0,           # Was 250.0 (orig 1500.0)
            'city': 240.0,          # Was 700.0 (orig 4000.0)
            'commercial': 34.0,     # Was 100.0 (orig 500.0) - workers during day
            'industrial': 14.0,     # Was 40.0 (orig 200.0) - shift workers
            'mixed': 95.0,          # Was 280.0 (orig 1500.0)
            'retail': 50.0,         # Was 150.0 (orig 800.0)
            'office': 75.0          # Was 220.0 (orig 1200.0)
        }
        
        return density_map.get(landuse_type.lower(), 3.0)  # Default low density (was 10.0)
    
    def _estimate_activity_level(self, amenity_type: str, properties: Dict) -> float:
        """Estimate activity level (spawn rate) for amenities
        
        ADJUSTED RATES (2024-10-13): Reduced by ~18x (6x * 3x) for realistic evening spawn rates.
        Base rates assume peak activity - will be multiplied by temporal and zone modifiers.
        Target: 90-180 passengers/hour total at 8 PM (60-120 depot + 30-60 route)
        """
        activity_map = {
            'school': 0.17,         # Was 0.5 (orig 3.0) - schools have burst activity during commute hours only
            'university': 0.27,     # Was 0.8 (orig 5.0) - universities have more distributed activity
            'hospital': 0.17,       # Was 0.5 (orig 2.0) - steady but lower than expected
            'clinic': 0.10,         # Was 0.3 (orig 1.5)
            'shopping': 0.23,       # Was 0.7 (orig 4.0) - high activity but reduced base
            'mall': 0.34,           # Was 1.0 (orig 6.0) - highest activity amenity
            'market': 0.20,         # Was 0.6 (orig 3.5)
            'restaurant': 0.13,     # Was 0.4 (orig 2.0) - clustered around meal times
            'cafe': 0.07,           # Was 0.2 (orig 1.0)
            'bank': 0.10,           # Was 0.3 (orig 1.5)
            'post_office': 0.07,    # Was 0.2 (orig 1.0)
            'government': 0.13,     # Was 0.4 (orig 2.0)
            'church': 0.05,         # Was 0.15 (orig 0.8) - mainly weekend activity
            'mosque': 0.05,         # Was 0.15 (orig 0.8)
            'temple': 0.05,         # Was 0.15 (orig 0.8)
            'park': 0.03,           # Was 0.1 (orig 0.5)
            'beach': 0.08,          # Was 0.25 (orig 1.2) - leisure activity
            'tourist': 0.17,        # Was 0.5 (orig 2.5)
            'hotel': 0.12,          # Was 0.35 (orig 1.8)
            'fuel': 0.05            # Was 0.15 (orig 0.8)
        }
        
        return activity_map.get(amenity_type.lower(), 0.03)  # Default low activity (was 0.1)
    
    def _get_peak_hours(self, zone_type: str) -> List[int]:
        """Get peak hours for different zone types"""
        peak_hours_map = {
            'residential': [7, 8, 17, 18, 19],  # Morning and evening commute
            'commercial': [9, 10, 11, 12, 13, 14, 15, 16],  # Business hours
            'industrial': [6, 7, 15, 16, 17],  # Shift changes
            'retail': [10, 11, 12, 13, 17, 18, 19],  # Shopping hours
            'office': [8, 9, 12, 13, 17, 18],  # Office hours
            'mixed': [8, 9, 12, 13, 17, 18, 19]  # Combined pattern
        }
        
        return peak_hours_map.get(zone_type.lower(), [9, 12, 17])  # Default pattern
    
    def _get_amenity_peak_hours(self, amenity_type: str) -> List[int]:
        """Get peak hours for different amenity types"""
        amenity_peaks = {
            'school': [7, 8, 15, 16],
            'university': [8, 9, 10, 11, 14, 15, 16],
            'hospital': list(range(8, 18)),  # All day activity
            'shopping': [10, 11, 12, 17, 18, 19],
            'restaurant': [12, 13, 18, 19, 20],
            'bank': [9, 10, 11, 12, 14, 15, 16],
            'church': [9, 10, 18, 19],  # Sunday service times
            'beach': [10, 11, 12, 13, 14, 15, 16],  # Daytime
            'tourist': [9, 10, 11, 12, 13, 14, 15, 16]
        }
        
        return amenity_peaks.get(amenity_type.lower(), [10, 14, 18])
    
    def _get_geometry_center(self, geometry) -> Tuple[float, float]:
        """Get center point of geometry as (lat, lon)"""
        centroid = geometry.centroid
        return (centroid.y, centroid.x)  # (lat, lon)
    
    def _enhance_nearby_zones(self, center: Tuple[float, float], name: str, place_type: str):
        """Enhance nearby zones with place name information"""
        for zone in self.population_zones:
            zone_center = zone.center_point
            distance = geodesic(center, zone_center).kilometers
            
            if distance < 1.0:  # Within 1km
                # Add place name to zone ID for better identification
                if name and name not in zone.zone_id:
                    zone.zone_id = f"{zone.zone_id}_{name.replace(' ', '_')}"


class PoissonGeoJSONSpawner:
    """Poisson-based passenger spawning using GeoJSON population data"""
    
    def __init__(self, api_client: StrapiApiClient, spatial_cache: Optional[SimpleSpatialZoneCache] = None):
        self.api_client = api_client
        self.geojson_loader = GeoJSONDataLoader(self.api_client)
        self.spatial_cache = spatial_cache  # Optional spatial zone cache for performance
        self.routes: List[RouteData] = []
        self.depots: List[DepotData] = []
        self._initialized = False
        self._using_cache = False
    
    async def initialize(self, country_code: str = "barbados", use_spatial_cache: bool = True) -> bool:
        """Initialize with GeoJSON and API data
        
        Args:
            country_code: Country code for geographic data
            use_spatial_cache: If True and spatial_cache is set, use cached zones instead of loading all
        """
        try:
            # Load API data (routes and depots)
            self.routes = await self.api_client.get_all_routes()
            self.depots = await self.api_client.get_all_depots()
            
            # Determine if we should use spatial cache
            if use_spatial_cache and self.spatial_cache:
                # Get cached zones (already loaded during initialization)
                population_zones, amenity_zones = await self.spatial_cache.get_cached_zones()
                
                # Convert cached zones to PopulationZone objects
                self.geojson_loader.population_zones = await self._convert_cached_zones(
                    population_zones, is_amenity=False
                )
                self.geojson_loader.amenity_zones = await self._convert_cached_zones(
                    amenity_zones, is_amenity=True
                )
                
                stats = self.spatial_cache.get_stats()
                logging.info(
                    f"✅ Using spatial cache: {stats['population_zones']} population zones, "
                    f"{stats['amenity_zones']} amenity zones (±{stats['buffer_km']}km buffer)"
                )
                self._using_cache = True
            else:
                # Traditional full load (all zones, blocks main thread)
                logging.info("📦 Loading all zones (no spatial filtering)...")
                if not await self.geojson_loader.load_geojson_data(country_code):
                    return False
            
            self._initialized = True
            logging.info(f"✅ Poisson GeoJSON spawner initialized for {country_code}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize Poisson spawner: {e}")
            return False
    
    async def _convert_cached_zones(
        self,
        cached_zones: List[Dict[str, Any]],
        is_amenity: bool = False
    ) -> List[PopulationZone]:
        """Convert cached zone dictionaries to PopulationZone objects
        
        Args:
            cached_zones: List of zone dictionaries from spatial cache
            is_amenity: True if these are amenity zones
        
        Returns:
            List of PopulationZone objects
        """
        logging.info(f"🔄 Converting {len(cached_zones)} cached {'amenity' if is_amenity else 'population'} zones...")
        zones = []
        
        for i, zone_data in enumerate(cached_zones):
            try:
                if i % 5 == 0:  # Log progress every 5 zones
                    logging.info(f"   Processing zone {i+1}/{len(cached_zones)}...")
                
                # Extract geometry
                geometry_data = zone_data.get('geometry_geojson') or zone_data.get('geometry')
                if not geometry_data:
                    continue
                
                geometry = shape(geometry_data)
                
                # Extract zone type
                zone_type = zone_data.get('zone_type') or zone_data.get('amenity_type', 'unknown')
                
                # Calculate population density
                if is_amenity:
                    # For amenities, use activity level estimation
                    # Pass empty dict for properties since we don't have them in cached zones
                    population_density = self.geojson_loader._estimate_activity_level(
                        zone_type, 
                        zone_data.get('properties', {})
                    )
                else:
                    population_density = self.geojson_loader._estimate_population_density(zone_type)
                
                if population_density > 0:
                    zone = PopulationZone(
                        zone_id=f"{'amenity' if is_amenity else 'landuse'}_{zone_data['id']}",
                        center_point=self.geojson_loader._get_geometry_center(geometry),
                        geometry=geometry,
                        base_population=int(geometry.area * 1000000 * population_density),
                        zone_type=zone_type,
                        spawn_rate_per_hour=population_density * 0.1,
                        peak_hours=self.geojson_loader._get_peak_hours(zone_type)
                    )
                    zones.append(zone)
                    
            except Exception as e:
                logging.warning(f"Failed to convert cached zone {i+1}: {e}")
                continue
        
        logging.info(f"✅ Converted {len(zones)} zones successfully")
        return zones
    
    async def generate_poisson_spawn_requests(self, current_time: datetime, 
                                            time_window_minutes: int = 5,
                                            spawn_context: str = "depot") -> List[Dict[str, Any]]:
        """Generate spawn requests using Poisson distribution
        
        Args:
            current_time: Current simulation time
            time_window_minutes: Time window for Poisson calculation
            spawn_context: "depot" or "route" - affects temporal patterns
                          depot: peaks at rush hours (journey starts)
                          route: builds throughout day (people already out)
        """
        if not self._initialized:
            raise RuntimeError("Spawner not initialized")
        
        spawn_requests = []
        current_hour = current_time.hour
        
        logging.info(f"🎲 [{spawn_context.upper()}] Starting spawn generation for hour {current_hour}: {len(self.geojson_loader.population_zones)} population zones, {len(self.geojson_loader.amenity_zones)} amenity zones")
        
        # Process population zones with error handling
        pop_zones_processed = 0
        pop_zones_with_spawns = 0
        try:
            for zone in self.geojson_loader.population_zones:
                try:
                    spawn_rate = self._calculate_poisson_rate(zone, current_hour, time_window_minutes, spawn_context)
                    
                    if spawn_rate > 0:
                        # Use Poisson distribution for passenger count
                        passenger_count = np.random.poisson(spawn_rate)
                        
                        if passenger_count > 0:
                            pop_zones_with_spawns += 1
                            requests = await self._create_zone_spawn_requests(
                                zone, passenger_count, current_time
                            )
                            spawn_requests.extend(requests)
                    
                    pop_zones_processed += 1
                except Exception as e:
                    logging.error(f"Error processing population zone {zone.zone_id}: {e}")
                    continue
        except Exception as e:
            logging.error(f"Error in population zone loop: {e}")
        
        logging.info(f"🎲 [{spawn_context.upper()}] Processed {pop_zones_processed} population zones, {pop_zones_with_spawns} generated spawns")
        
        # Process amenity zones with error handling
        amenity_zones_processed = 0
        amenity_spawn_count = 0
        try:
            for zone in self.geojson_loader.amenity_zones:
                try:
                    spawn_rate = self._calculate_poisson_rate(zone, current_hour, time_window_minutes, spawn_context)
                    
                    if spawn_rate > 0:
                        passenger_count = np.random.poisson(spawn_rate)
                        
                        if passenger_count > 0:
                            amenity_spawn_count += 1
                            if amenity_spawn_count <= 3:
                                logging.debug(f"  [AMENITY] Amenity spawn: {zone.zone_type} (rate={spawn_rate:.3f}, count={passenger_count})")
                            requests = await self._create_zone_spawn_requests(
                                zone, passenger_count, current_time
                            )
                            spawn_requests.extend(requests)
                    
                    amenity_zones_processed += 1
                except Exception as e:
                    logging.error(f"Error processing amenity zone {zone.zone_id}: {e}")
                    continue
        except Exception as e:
            logging.error(f"Error in amenity zone loop: {e}")
        
        logging.info(f"🎲 [{spawn_context.upper()}] Processed {amenity_zones_processed} amenity zones, {amenity_spawn_count} with spawns")
        
        if amenity_spawn_count > 0:
            logging.info(f"🎲 [{spawn_context.upper()}] Generated {len(spawn_requests)} Poisson-based spawn requests ({amenity_spawn_count} from amenities)")
        else:
            logging.info(f"🎲 [{spawn_context.upper()}] Generated {len(spawn_requests)} Poisson-based spawn requests")
        return spawn_requests
    
    def _calculate_poisson_rate(self, zone: PopulationZone, hour: int, 
                                time_window_minutes: int, spawn_context: str = "depot",
                                route: Optional[RouteData] = None,
                                depot: Optional['DepotData'] = None) -> float:
        """Calculate Poisson lambda (mean) rate for a zone
        
        Args:
            zone: Population zone to calculate rate for
            hour: Current hour (0-23)
            time_window_minutes: Time window for calculation
            spawn_context: "depot" or "route" - affects temporal multipliers
            route: Optional route data for route-specific activity multiplier
            depot: Optional depot data for depot-specific activity multiplier
        """
        base_rate = zone.spawn_rate_per_hour
        
        # Apply peak hour multiplier
        if hour in zone.peak_hours:
            peak_multiplier = 2.5
        else:
            peak_multiplier = 1.0
        
        # Apply zone type modifiers WITH spawn context
        zone_modifier = self._get_zone_modifier(zone.zone_type, hour, spawn_context)
        
        # Apply route/depot activity multiplier
        activity_multiplier = 1.0
        if spawn_context == "route" and route:
            activity_multiplier = self._get_route_activity_multiplier(route)
        elif spawn_context == "depot" and depot:
            activity_multiplier = self._get_depot_activity_multiplier(depot)
        
        # Convert to time window rate
        hourly_rate = base_rate * peak_multiplier * zone_modifier * activity_multiplier
        time_window_rate = hourly_rate * (time_window_minutes / 60.0)
        
        return max(0.0, time_window_rate)
    
    def _get_context_multiplier(self, hour: int, spawn_context: str) -> float:
        """Calculate spawn rate multiplier based on context (depot vs route)
        
        DEPOT Pattern (Journey Starts):
        - High: 7-9am (morning rush), 5-7pm (evening rush)
        - Medium: 10am-4pm (some travel)  
        - Low: 8-10pm (evening wind-down)
        - Very Low: 11pm-6am (night)
        
        ROUTE Pattern (Already Out):
        - Builds throughout day as people go out
        - Peaks: 12pm-5pm (lunch, afternoon activities)
        - Medium: 7-11am (morning activities)
        - Lower: 6-7pm (rush hour - people going TO depots)
        - Low: 8pm-11pm (evening)
        - Very Low: 12am-6am (night)
        """
        if spawn_context == "depot":
            # Depot spawning - journey starts
            if 7 <= hour <= 9:  # Morning rush peak
                return 2.5
            elif 17 <= hour <= 19:  # Evening rush peak
                return 2.0
            elif 10 <= hour <= 16:  # Mid-day moderate
                return 0.7
            elif 20 <= hour <= 22:  # Evening wind-down
                return 0.3
            elif 23 <= hour or hour <= 6:  # Night minimal
                return 0.05
            else:
                return 1.0
        
        else:  # "route" context
            # Route spawning - people already out
            if 12 <= hour <= 16:  # Afternoon peak (people out for lunch, errands, activities)
                return 1.8
            elif 10 <= hour <= 11:  # Late morning build-up
                return 1.3
            elif 7 <= hour <= 9:  # Morning activities
                return 1.0
            elif 17 <= hour <= 18:  # Early evening (people heading to depots)
                return 0.6
            elif 19 <= hour <= 22:  # Evening (fewer people out)
                return 0.4
            elif 23 <= hour or hour <= 6:  # Night minimal
                return 0.05
            else:
                return 1.0
    
    def _get_route_activity_multiplier(self, route: RouteData) -> float:
        """Get activity multiplier from route database field
        
        Returns the activity_level from the database (0.5-2.0, default 1.0).
        This allows operators to configure route importance/activity without code changes.
        
        Examples:
        - 0.5-0.7: Low activity routes (local shuttles, off-peak routes)
        - 0.8-1.2: Normal activity routes (standard service)
        - 1.3-2.0: High activity routes (main trunk routes, express services)
        """
        return route.activity_level
    
    def _get_depot_activity_multiplier(self, depot: 'DepotData') -> float:
        """Get activity multiplier from depot database field
        
        Returns the activity_level from the database (0.5-2.0, default 1.0).
        This allows operators to configure depot importance/activity without code changes.
        
        Examples:
        - 0.5-0.7: Low activity depots (small satellite depots, low ridership areas)
        - 0.8-1.2: Normal activity depots (standard terminals)
        - 1.3-2.0: High activity depots (major city terminals, transfer hubs)
        """
        return depot.activity_level
    
    def _get_zone_modifier(self, zone_type: str, hour: int, spawn_context: str = "depot") -> float:
        """Get zone-specific modifier based on time of day and spawn context
        
        TEMPORAL MULTIPLIERS with Context Awareness:
        - DEPOT spawning: People starting journeys (peaks at rush hours, low mid-day/night)
        - ROUTE spawning: People already out and about (builds through day, peaks afternoon)
        
        Args:
            zone_type: Type of zone (residential, commercial, etc.)
            hour: Current hour (0-23)
            spawn_context: "depot" or "route"
        """
        # Context multiplier applied on top of zone patterns
        context_mult = self._get_context_multiplier(hour, spawn_context)
        
        if zone_type in ['residential', 'urban', 'suburban']:
            if 7 <= hour <= 9:  # Morning commute peak
                return 3.0 * context_mult
            elif 17 <= hour <= 19:  # Evening commute peak
                return 2.5 * context_mult
            elif 20 <= hour <= 21:  # Evening
                return 0.8 * context_mult
            elif 22 <= hour or hour <= 6:  # Night
                return 0.1 * context_mult
            else:
                return 1.0 * context_mult
        
        elif zone_type in ['commercial', 'retail', 'office']:
            if 9 <= hour <= 17:  # Business hours
                return 2.0 * context_mult
            elif hour in [8, 18]:  # Start/end of business
                return 1.5 * context_mult
            elif 19 <= hour <= 21:  # Evening shopping
                return 1.2 * context_mult
            elif 22 <= hour or hour <= 7:  # Closed
                return 0.05 * context_mult
            else:
                return 1.0 * context_mult
        
        elif zone_type in ['school', 'university']:
            if hour in [7, 8, 15, 16]:  # School commute hours
                return 4.0 * context_mult
            elif 9 <= hour <= 14:  # During classes
                return 0.3 * context_mult
            elif 17 <= hour <= 23:  # After school hours - universities may have evening classes
                mult = 0.1 if zone_type == 'school' else 0.5
                return mult * context_mult
            else:
                return 0.05 * context_mult
        
        elif zone_type in ['restaurant', 'cafe']:
            if 12 <= hour <= 13:  # Lunch peak
                return 3.0 * context_mult
            elif 18 <= hour <= 21:  # Dinner peak
                return 2.5 * context_mult
            elif 7 <= hour <= 9:  # Breakfast
                return 1.5 * context_mult
            elif 22 <= hour or hour <= 6:  # Closed/very quiet
                return 0.1 * context_mult
            else:
                return 1.0 * context_mult
        
        elif zone_type in ['shopping', 'mall', 'market']:
            if 10 <= hour <= 13:  # Midday shopping
                return 2.0 * context_mult
            elif 17 <= hour <= 20:  # Evening shopping
                return 2.5 * context_mult
            elif 21 <= hour or hour <= 8:  # Closed
                return 0.05 * context_mult
            else:
                return 1.0 * context_mult
        
        elif zone_type in ['hospital', 'clinic']:
            if 8 <= hour <= 17:  # Regular hours
                return 2.0 * context_mult
            elif 18 <= hour <= 22:  # Evening reduced
                return 0.8 * context_mult
            else:
                return 0.5 * context_mult
        
        elif zone_type in ['beach', 'park', 'tourist']:
            if 10 <= hour <= 16:  # Daytime leisure
                return 2.0 * context_mult
            elif 17 <= hour <= 19:  # Evening visits
                return 1.0 * context_mult
            elif 20 <= hour or hour <= 7:  # Closed/dark
                return 0.1 * context_mult
            else:
                return 0.8 * context_mult
        
        else:
            # Default pattern for unknown types
            if 8 <= hour <= 18:
                return 1.5 * context_mult
            elif 19 <= hour <= 21:
                return 0.8 * context_mult
            else:
                return 0.3 * context_mult
    
    async def _create_zone_spawn_requests(self, zone: PopulationZone, 
                                        passenger_count: int, 
                                        current_time: datetime) -> List[Dict[str, Any]]:
        """Create spawn requests for a population zone"""
        requests = []
        
        for _ in range(passenger_count):
            # Find nearest route for spawning
            nearest_route = self._find_nearest_route(zone.center_point)
            
            if nearest_route:
                # Generate spawn location ON the route (snapped to route geometry)
                spawn_location = self._generate_spawn_location_in_zone(zone, nearest_route)
                
                # Generate destination based on trip purpose and time
                destination = self._generate_destination(zone, current_time, nearest_route)
                
                request = {
                    'zone_id': zone.zone_id,
                    'zone_type': zone.zone_type,
                    'spawn_location': spawn_location,
                    'destination_location': destination,
                    'assigned_route': nearest_route.short_name,
                    'trip_purpose': self._determine_trip_purpose(zone.zone_type, current_time),
                    'spawn_time': current_time,
                    'priority': self._calculate_priority(zone.zone_type, current_time.hour),
                    'generation_method': 'poisson_geojson'
                }
                requests.append(request)
        
        return requests
    
    def _find_nearest_route(self, location: Tuple[float, float]) -> Optional[RouteData]:
        """Find the nearest route to a location"""
        if not self.routes:
            return None
        
        min_distance = float('inf')
        nearest_route = None
        
        for route in self.routes:
            if route.geometry_coordinates:
                # Check distance to route
                for coord in route.geometry_coordinates:
                    route_point = (coord[1], coord[0])  # Convert to (lat, lon)
                    distance = geodesic(location, route_point).kilometers
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_route = route
        
        return nearest_route
    
    def _generate_spawn_location_in_zone(self, zone: PopulationZone, route: RouteData = None) -> Dict[str, float]:
        """Generate spawn location ON the route geometry (not in zone center).
        
        For route spawns, passengers MUST spawn at actual route points, not in nearby zones.
        This ensures trip distances are realistic and <= route length.
        
        Args:
            zone: Population zone where spawning occurs
            route: Route to snap spawn location to (if provided)
            
        Returns:
            Dict with 'lat' and 'lon' of spawn location
        """
        if route and route.geometry_coordinates:
            # Find closest point on route to zone center
            zone_center = zone.center_point
            min_dist = float('inf')
            closest_route_point = None
            
            for coord in route.geometry_coordinates:
                route_point = (coord[1], coord[0])  # Convert to (lat, lon)
                dist = geodesic(zone_center, route_point).kilometers
                
                if dist < min_dist:
                    min_dist = dist
                    closest_route_point = route_point
            
            # Return the actual route point, not zone center!
            if closest_route_point:
                return {
                    'lat': closest_route_point[0],
                    'lon': closest_route_point[1]
                }
        
        # Fallback: use zone center with small offset (for depot spawns or if no route)
        lat, lon = zone.center_point
        
        # Add small random offset (within ~100m)
        lat_offset = random.uniform(-0.001, 0.001)
        lon_offset = random.uniform(-0.001, 0.001)
        
        return {
            'lat': lat + lat_offset,
            'lon': lon + lon_offset
        }
    
    def _generate_destination(self, zone: PopulationZone, current_time: datetime, 
                            route: RouteData) -> Dict[str, float]:
        """Generate realistic destination based on zone type and time"""
        hour = current_time.hour
        
        # Destination logic based on zone type and time
        if zone.zone_type in ['residential', 'urban', 'suburban']:
            if 7 <= hour <= 9:  # Morning - go to work/commercial areas
                return self._find_commercial_destination(route)
            elif 17 <= hour <= 19:  # Evening - return home or social
                return self._find_residential_destination(route)
            else:
                return self._find_random_destination(route)
        
        elif zone.zone_type in ['commercial', 'retail']:
            # From commercial areas, go to residential or other commercial
            return self._find_mixed_destination(route)
        
        else:
            return self._find_random_destination(route)
    
    def _find_commercial_destination(self, route: RouteData) -> Dict[str, float]:
        """Find destination in commercial/business areas ALONG THE ROUTE"""
        # For route spawns, destinations MUST be on the route itself
        # We'll use route geometry instead of searching arbitrary zones
        spawn_loc = self._approx_route_spawn_point(route)
        return self._select_destination_along_route(route, spawn_loc, min_distance_km=0.5, max_distance_km=3.0)
    
    def _find_residential_destination(self, route: RouteData) -> Dict[str, float]:
        """Find destination in residential areas ALONG THE ROUTE"""
        # For route spawns, destinations MUST be on the route itself
        spawn_loc = self._approx_route_spawn_point(route)
        return self._select_destination_along_route(route, spawn_loc, min_distance_km=0.5, max_distance_km=3.0)
    
    def _find_mixed_destination(self, route: RouteData) -> Dict[str, float]:
        """Find mixed destination ALONG THE ROUTE"""
        # For route spawns, destinations MUST be on the route itself
        spawn_loc = self._approx_route_spawn_point(route)
        return self._select_destination_along_route(route, spawn_loc, min_distance_km=0.5, max_distance_km=3.0)

    def _approx_route_spawn_point(self, route: RouteData) -> Tuple[float, float]:
        """Approximate a spawn location on the route to compute distances.

        This picks a random point along the route (latitude, longitude) to act
        as the passenger spawn location when calculating destination distances.
        Using a random point is a reasonable approximation since spawn locations
        are already sampled within source zones.
        """
        if route.geometry_coordinates and len(route.geometry_coordinates) > 0:
            coord = random.choice(route.geometry_coordinates)
            return (coord[1], coord[0])
        # Default fallback (center of Barbados)
        return (13.1939, -59.5432)

    def _select_destination_by_log_normal_distance(self, zones: List[PopulationZone],
                                                   spawn_location: Tuple[float, float],
                                                   mu: float = 1.5,
                                                   sigma: float = 0.7) -> Optional[Dict[str, float]]:
        """Select a destination zone using a log-normal desired trip distance.
        
        NOTE: This method is DEPRECATED for route spawns. Route spawns should use
        _select_destination_along_route() instead to ensure destinations are ON the route.
        
        This method picks destinations from ANY zone, which can result in trips longer
        than the route itself - a logical impossibility!

        - samples a desired trip distance in kilometers from a log-normal
          distribution (parameters mu, sigma)
        - computes distances from spawn_location to each candidate zone
        - selects the zone whose distance is closest to the sampled distance

        Returns a dict with 'lat' and 'lon', or None if zones list is empty.
        """
        if not zones:
            return None

        # Compute distances for candidate zones
        zone_distances = []  # tuples of (zone, distance_km)
        for z in zones:
            dest = (z.center_point[0], z.center_point[1])
            dist_km = geodesic(spawn_location, dest).kilometers
            zone_distances.append((z, dist_km))

        # Sample desired trip distance from log-normal distribution
        desired_km = float(np.random.lognormal(mean=mu, sigma=sigma))

        # Choose the zone whose distance is closest to desired_km
        best_zone, best_dist = min(zone_distances, key=lambda x: abs(x[1] - desired_km))

        return {'lat': best_zone.center_point[0], 'lon': best_zone.center_point[1]}
    
    def _select_destination_along_route(self, route: RouteData, spawn_location: Tuple[float, float],
                                       min_distance_km: float = 0.5,
                                       max_distance_km: float = None) -> Dict[str, float]:
        """Select a destination point ALONG the route geometry.
        
        This ensures passengers spawning on a route have destinations that are actually
        reachable by that route. The destination will be a point from the route's shape.
        
        Args:
            route: The route the passenger will travel on
            spawn_location: Where the passenger is spawning (lat, lon)
            min_distance_km: Minimum trip distance (default 0.5 km)
            max_distance_km: Maximum trip distance (default: full route length)
            
        Returns:
            Dict with 'lat' and 'lon' of a point along the route
        """
        if not route.geometry_coordinates or len(route.geometry_coordinates) < 2:
            # Fallback if route has no geometry
            return {'lat': 13.1939, 'lon': -59.5432}
        
        # Find the closest point on the route to the spawn location
        min_spawn_dist = float('inf')
        closest_spawn_idx = 0
        
        for i, coord in enumerate(route.geometry_coordinates):
            route_point = (coord[1], coord[0])  # Convert to (lat, lon)
            dist = geodesic(spawn_location, route_point).kilometers
            if dist < min_spawn_dist:
                min_spawn_dist = dist
                closest_spawn_idx = i
        
        # Calculate cumulative distances along the route
        cumulative_distances = [0.0]
        for i in range(len(route.geometry_coordinates) - 1):
            coord1 = route.geometry_coordinates[i]
            coord2 = route.geometry_coordinates[i + 1]
            point1 = (coord1[1], coord1[0])
            point2 = (coord2[1], coord2[0])
            segment_dist = geodesic(point1, point2).kilometers
            cumulative_distances.append(cumulative_distances[-1] + segment_dist)
        
        total_route_length = cumulative_distances[-1]
        
        # Set max distance to route length if not specified
        if max_distance_km is None:
            max_distance_km = total_route_length
        
        spawn_distance_along_route = cumulative_distances[closest_spawn_idx]
        
        # Find candidate destination points that are within min/max distance
        candidates = []
        for i, cum_dist in enumerate(cumulative_distances):
            trip_distance = abs(cum_dist - spawn_distance_along_route)
            
            if min_distance_km <= trip_distance <= max_distance_km:
                coord = route.geometry_coordinates[i]
                candidates.append({
                    'index': i,
                    'lat': coord[1],
                    'lon': coord[0],
                    'trip_distance': trip_distance
                })
        
        # If no candidates found (route too short), pick the furthest point
        if not candidates:
            # Pick a point at least min_distance away, or the furthest point
            best_idx = 0
            best_dist = 0.0
            for i, cum_dist in enumerate(cumulative_distances):
                trip_dist = abs(cum_dist - spawn_distance_along_route)
                if trip_dist > best_dist:
                    best_dist = trip_dist
                    best_idx = i
            
            coord = route.geometry_coordinates[best_idx]
            return {'lat': coord[1], 'lon': coord[0]}
        
        # Randomly select from candidates (weighted towards longer trips)
        # Use trip_distance as weight to prefer longer journeys
        weights = [c['trip_distance'] for c in candidates]
        total_weight = sum(weights)
        
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
            selected = np.random.choice(len(candidates), p=weights)
            dest = candidates[selected]
        else:
            dest = random.choice(candidates)
        
        return {'lat': dest['lat'], 'lon': dest['lon']}
    
    def _find_random_destination(self, route: RouteData) -> Dict[str, float]:

        """Find random destination along route with better distribution"""
        if route.geometry_coordinates and len(route.geometry_coordinates) > 0:
            total_points = len(route.geometry_coordinates)
            
            # Randomly choose from beginning (0-33%), middle (33-66%), or end (66-100%)
            section = random.choice(['start', 'middle', 'end'])
            
            if total_points < 3:
                # If route has fewer than 3 points, just pick randomly
                index = random.randint(0, total_points - 1)
            elif section == 'start':
                # First third
                end_idx = max(1, total_points // 3)
                index = random.randint(0, end_idx - 1)
            elif section == 'middle':
                # Middle third
                start_idx = total_points // 3
                end_idx = max(start_idx + 1, 2 * total_points // 3)
                index = random.randint(start_idx, end_idx - 1)
            else:  # end
                # Last third
                start_idx = 2 * total_points // 3
                index = random.randint(start_idx, total_points - 1)
            
            coord = route.geometry_coordinates[index]
            return {'lat': coord[1], 'lon': coord[0]}
        
        return {'lat': 13.1939, 'lon': -59.5432}  # Default Barbados location
    
    def _is_zone_near_route(self, zone: PopulationZone, route: RouteData, max_distance_km: float = 2.0) -> bool:
        """Check if zone is near a route"""
        if not route.geometry_coordinates:
            return False
        
        zone_location = zone.center_point
        
        for coord in route.geometry_coordinates:
            route_point = (coord[1], coord[0])  # Convert to (lat, lon)
            distance = geodesic(zone_location, route_point).kilometers
            
            if distance <= max_distance_km:
                return True
        
        return False
    
    def _determine_trip_purpose(self, zone_type: str, current_time: datetime) -> str:
        """Determine trip purpose based on zone type and time"""
        hour = current_time.hour
        
        if zone_type in ['residential', 'suburban']:
            if 7 <= hour <= 9:
                return 'work'
            elif 15 <= hour <= 17:
                return 'school'
            elif 17 <= hour <= 19:
                return 'home'
            else:
                return 'social'
        
        elif zone_type in ['commercial', 'office']:
            return 'work'
        
        elif zone_type in ['school', 'university']:
            return 'education'
        
        elif zone_type in ['shopping', 'retail']:
            return 'shopping'
        
        elif zone_type in ['hospital', 'clinic']:
            return 'medical'
        
        else:
            return 'general'
    
    def _calculate_priority(self, zone_type: str, hour: int) -> float:
        """Calculate spawn priority based on zone type and hour"""
        base_priority = 0.5
        
        if zone_type in ['hospital', 'clinic']:
            base_priority = 0.9
        elif zone_type in ['school', 'university'] and hour in [7, 8, 15, 16]:
            base_priority = 0.8
        elif zone_type in ['commercial', 'office'] and 8 <= hour <= 18:
            base_priority = 0.7
        
        # Rush hour boost
        if hour in [7, 8, 17, 18]:
            base_priority += 0.2
        
        return min(1.0, base_priority)