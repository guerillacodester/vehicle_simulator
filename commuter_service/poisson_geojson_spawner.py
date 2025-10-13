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
            logging.info(f"🌍 Loading geographic data for {country_data['name']} (ID: {self.country_id})")
            
            # Load different types of GeoJSON data from API
            await self._load_landuse_data_from_api()
            await self._load_amenities_data_from_api()
            await self._load_places_data_from_api()
            await self._load_regions_data_from_api()
            
            logging.info(f"✅ Loaded GeoJSON data from API: {len(self.population_zones)} population zones, "
                        f"{len(self.amenity_zones)} amenity zones, {len(self.transport_hubs)} transport hubs")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to load GeoJSON data from API: {e}")
            return False
    
    async def _load_landuse_data_from_api(self):
        """Load land use data from Strapi API for population estimation"""
        if not self.country_id:
            logging.warning("No country ID set for landuse data loading")
            return
            
        landuse_zones = await self.api_client.get_landuse_zones_by_country(self.country_id)
        logging.info(f"📊 Loading {len(landuse_zones)} landuse zones from API")
        
        for zone_data in landuse_zones:
            try:
                # Extract geometry from Strapi format
                geometry_data = zone_data.get('geometry')
                if not geometry_data:
                    continue
                
                geometry = shape(geometry_data)
                
                # Extract landuse type
                landuse_type = zone_data.get('landuse_type', 'unknown')
                
                # Calculate population density based on land use
                population_density = self._estimate_population_density(landuse_type, zone_data)
                
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
        logging.info(f"🎯 Loading {len(pois)} POIs from API")
        
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
        logging.info(f"📍 Loading {len(places)} places from API")
        
        # Use places data to enhance existing zones with better identification
        for place_data in places:
            try:
                # Create point geometry from lat/lon or use geometry if available
                geometry_data = place_data.get('geometry')
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
        logging.info(f"🗺️ Loading {len(regions)} regions from API")
        
        for region_data in regions:
            try:
                # Extract geometry from Strapi format
                geometry_data = region_data.get('geometry')
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
    
    def __init__(self, api_client: StrapiApiClient):
        self.api_client = api_client
        self.geojson_loader = GeoJSONDataLoader(self.api_client)
        self.routes: List[RouteData] = []
        self.depots: List[DepotData] = []
        self._initialized = False
    
    async def initialize(self, country_code: str = "barbados") -> bool:
        """Initialize with GeoJSON and API data"""
        try:
            # Load GeoJSON population data
            if not await self.geojson_loader.load_geojson_data(country_code):
                return False
            
            # Load API data
            self.routes = await self.api_client.get_all_routes()
            self.depots = await self.api_client.get_all_depots()
            
            self._initialized = True
            logging.info(f"✅ Poisson GeoJSON spawner initialized for {country_code}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize Poisson spawner: {e}")
            return False
    
    async def generate_poisson_spawn_requests(self, current_time: datetime, 
                                            time_window_minutes: int = 5) -> List[Dict[str, Any]]:
        """Generate spawn requests using Poisson distribution"""
        if not self._initialized:
            raise RuntimeError("Spawner not initialized")
        
        spawn_requests = []
        current_hour = current_time.hour
        
        logging.debug(f"🎲 Spawning for hour {current_hour}: {len(self.geojson_loader.population_zones)} population zones, {len(self.geojson_loader.amenity_zones)} amenity zones")
        
        # Process population zones
        for zone in self.geojson_loader.population_zones:
            spawn_rate = self._calculate_poisson_rate(zone, current_hour, time_window_minutes)
            
            if spawn_rate > 0:
                # Use Poisson distribution for passenger count
                passenger_count = np.random.poisson(spawn_rate)
                
                if passenger_count > 0:
                    requests = await self._create_zone_spawn_requests(
                        zone, passenger_count, current_time
                    )
                    spawn_requests.extend(requests)
        
        # Process amenity zones
        amenity_spawn_count = 0
        for zone in self.geojson_loader.amenity_zones:
            spawn_rate = self._calculate_poisson_rate(zone, current_hour, time_window_minutes)
            
            if spawn_rate > 0:
                passenger_count = np.random.poisson(spawn_rate)
                
                if passenger_count > 0:
                    amenity_spawn_count += 1
                    if amenity_spawn_count <= 3:
                        logging.debug(f"  🎯 Amenity spawn: {zone.zone_type} (rate={spawn_rate:.3f}, count={passenger_count})")
                    requests = await self._create_zone_spawn_requests(
                        zone, passenger_count, current_time
                    )
                    spawn_requests.extend(requests)
        
        if amenity_spawn_count > 0:
            logging.info(f"🎲 Generated {len(spawn_requests)} Poisson-based spawn requests ({amenity_spawn_count} from amenities)")
        else:
            logging.info(f"🎲 Generated {len(spawn_requests)} Poisson-based spawn requests")
        return spawn_requests
    
    def _calculate_poisson_rate(self, zone: PopulationZone, hour: int, time_window_minutes: int) -> float:
        """Calculate Poisson lambda (mean) rate for a zone"""
        base_rate = zone.spawn_rate_per_hour
        
        # Apply peak hour multiplier
        if hour in zone.peak_hours:
            peak_multiplier = 2.5
        else:
            peak_multiplier = 1.0
        
        # Apply zone type modifiers
        zone_modifier = self._get_zone_modifier(zone.zone_type, hour)
        
        # Convert to time window rate
        hourly_rate = base_rate * peak_multiplier * zone_modifier
        time_window_rate = hourly_rate * (time_window_minutes / 60.0)
        
        return max(0.0, time_window_rate)
    
    def _get_zone_modifier(self, zone_type: str, hour: int) -> float:
        """Get zone-specific modifier based on time of day
        
        TEMPORAL MULTIPLIERS (2024-10-13): Applied to base spawn rates for realistic patterns.
        These multipliers reflect actual transit usage patterns throughout the day.
        """
        if zone_type in ['residential', 'urban', 'suburban']:
            if 7 <= hour <= 9:  # Morning commute peak
                return 3.0
            elif 17 <= hour <= 19:  # Evening commute peak
                return 2.5
            elif 20 <= hour <= 21:  # Evening (current test time ~8 PM)
                return 0.8  # Reduced evening activity
            elif 22 <= hour or hour <= 6:  # Night
                return 0.1  # Minimal night activity
            else:
                return 1.0
        
        elif zone_type in ['commercial', 'retail', 'office']:
            if 9 <= hour <= 17:  # Business hours
                return 2.0
            elif hour in [8, 18]:  # Start/end of business
                return 1.5
            elif 19 <= hour <= 21:  # Evening shopping
                return 1.2  # Some retail stays open
            elif 22 <= hour or hour <= 7:  # Closed
                return 0.05  # Nearly zero activity
            else:
                return 1.0
        
        elif zone_type in ['school', 'university']:
            if hour in [7, 8, 15, 16]:  # School commute hours
                return 4.0
            elif 9 <= hour <= 14:  # During classes
                return 0.3  # Minimal spawning during classes
            elif 17 <= hour <= 23:  # After school hours - universities may have evening classes
                return 0.1 if zone_type == 'school' else 0.5  # Schools closed, universities minimal
            else:
                return 0.05  # Nearly zero overnight
        
        elif zone_type in ['restaurant', 'cafe']:
            if 12 <= hour <= 13:  # Lunch peak
                return 3.0
            elif 18 <= hour <= 21:  # Dinner peak
                return 2.5
            elif 7 <= hour <= 9:  # Breakfast
                return 1.5
            elif 22 <= hour or hour <= 6:  # Closed/very quiet
                return 0.1
            else:
                return 1.0
        
        elif zone_type in ['shopping', 'mall', 'market']:
            if 10 <= hour <= 13:  # Midday shopping
                return 2.0
            elif 17 <= hour <= 20:  # Evening shopping
                return 2.5
            elif 21 <= hour or hour <= 8:  # Closed
                return 0.05
            else:
                return 1.0
        
        elif zone_type in ['hospital', 'clinic']:
            if 8 <= hour <= 17:  # Regular hours
                return 2.0
            elif 18 <= hour <= 22:  # Evening reduced
                return 0.8
            else:
                return 0.5  # Emergency only overnight
        
        elif zone_type in ['beach', 'park', 'tourist']:
            if 10 <= hour <= 16:  # Daytime leisure
                return 2.0
            elif 17 <= hour <= 19:  # Evening visits
                return 1.0
            elif 20 <= hour or hour <= 7:  # Closed/dark
                return 0.1
            else:
                return 0.8
        
        else:
            # Default pattern for unknown types
            if 8 <= hour <= 18:
                return 1.5
            elif 19 <= hour <= 21:
                return 0.8
            else:
                return 0.3
    
    async def _create_zone_spawn_requests(self, zone: PopulationZone, 
                                        passenger_count: int, 
                                        current_time: datetime) -> List[Dict[str, Any]]:
        """Create spawn requests for a population zone"""
        requests = []
        
        for _ in range(passenger_count):
            # Find nearest route for spawning
            nearest_route = self._find_nearest_route(zone.center_point)
            
            if nearest_route:
                # Generate spawn location within zone
                spawn_location = self._generate_spawn_location_in_zone(zone)
                
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
    
    def _generate_spawn_location_in_zone(self, zone: PopulationZone) -> Dict[str, float]:
        """Generate random spawn location within zone geometry"""
        # Use zone center for simplicity, but could be enhanced to sample within polygon
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
        """Find destination in commercial/business areas"""
        # Look for commercial zones along route
        for amenity_zone in self.geojson_loader.amenity_zones:
            if amenity_zone.zone_type in ['commercial', 'office', 'shopping']:
                if self._is_zone_near_route(amenity_zone, route):
                    return {
                        'lat': amenity_zone.center_point[0],
                        'lon': amenity_zone.center_point[1]
                    }
        
        # Fallback to random point along route
        return self._find_random_destination(route)
    
    def _find_residential_destination(self, route: RouteData) -> Dict[str, float]:
        """Find destination in residential areas"""
        for pop_zone in self.geojson_loader.population_zones:
            if pop_zone.zone_type in ['residential', 'suburban']:
                if self._is_zone_near_route(pop_zone, route):
                    return {
                        'lat': pop_zone.center_point[0],
                        'lon': pop_zone.center_point[1]
                    }
        
        return self._find_random_destination(route)
    
    def _find_mixed_destination(self, route: RouteData) -> Dict[str, float]:
        """Find mixed destination (residential or commercial)"""
        all_zones = self.geojson_loader.population_zones + self.geojson_loader.amenity_zones
        nearby_zones = [z for z in all_zones if self._is_zone_near_route(z, route)]
        
        if nearby_zones:
            chosen_zone = random.choice(nearby_zones)
            return {
                'lat': chosen_zone.center_point[0],
                'lon': chosen_zone.center_point[1]
            }
        
        return self._find_random_destination(route)
    
    def _find_random_destination(self, route: RouteData) -> Dict[str, float]:
        """Find random destination along route"""
        if route.geometry_coordinates:
            coord = random.choice(route.geometry_coordinates)
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