"""
Geographic Data Loader

Loads and processes geographic population and amenity data from Strapi API.
All data comes from PostGIS database via Strapi REST API (GTFS + custom tables).

NO local GeoJSON files - all data retrieved from API endpoints.

Data Sources (via Strapi API → PostGIS):
- GTFS stops, routes, shapes (standard GTFS tables)
- Custom landuse zones (population density)
- Custom POIs/amenities (activity centers)
- Custom places (named locations)
- Custom regions (administrative boundaries)

Ported from commuter_service/poisson_geojson_spawner.py
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from shapely.geometry import Point, shape
from geopy.distance import geodesic


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
    is_amenity: bool = False  # True for POI/amenity zones


class GeoJSONDataLoader:
    """
    Loads and processes geographic data from Strapi API (PostGIS backend).
    
    Data is stored in PostGIS database following GTFS structure plus custom tables.
    All queries go through Strapi REST API - NO local files.
    
    Data Sources (API endpoints):
    - /api/landuse-zones: Residential, commercial, industrial areas (PostGIS polygons)
    - /api/pois: Schools, hospitals, shopping centers (PostGIS points)
    - /api/places: Named locations and landmarks (PostGIS points/polygons)
    - /api/regions: Administrative boundaries (PostGIS polygons)
    - /api/stops: GTFS bus stops (PostGIS points)
    - /api/shapes: GTFS route shapes (PostGIS linestrings)
    
    Usage:
        loader = GeoJSONDataLoader(api_client)
        success = await loader.load_geojson_data(country_code="BB")
        
        population_zones = loader.population_zones
        amenity_zones = loader.amenity_zones
    """
    
    def __init__(self, api_client: Any, logger: Optional[logging.Logger] = None):
        self.api_client = api_client
        self.logger = logger or logging.getLogger(__name__)
        
        self.population_zones: List[PopulationZone] = []
        self.amenity_zones: List[PopulationZone] = []
        self.transport_hubs: List[Dict[str, Any]] = []
        self.country_id: Optional[int] = None
    
    async def load_geojson_data(self, country_code: str = "BB") -> bool:
        """
        Load all geographic data from Strapi API (PostGIS backend).
        
        All data retrieved via REST API from PostGIS database.
        Data includes GTFS stops/shapes and custom landuse/POI tables.
        """
        try:
            # Get country information from API
            country_data = await self.api_client.get_country_by_code(country_code.upper())
            if not country_data:
                self.logger.error(f"❌ Country {country_code} not found in database")
                return False
            
            self.country_id = country_data['id']
            self.logger.info(f"[INIT] Loading geographic data from API for {country_data['name']} (ID: {self.country_id})")
            
            # Load different types of geographic data from API endpoints
            # Each method makes HTTP calls to Strapi → PostGIS
            await self._load_landuse_data_from_api()
            await self._load_amenities_data_from_api()
            await self._load_places_data_from_api()
            await self._load_regions_data_from_api()
            
            self.logger.info(
                f"[OK] Loaded geographic data from API (PostGIS): "
                f"{len(self.population_zones)} population zones, "
                f"{len(self.amenity_zones)} amenity zones, "
                f"{len(self.transport_hubs)} transport hubs"
            )
            return True
        
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to load geographic data from API: {e}")
            return False
    
    async def _load_landuse_data_from_api(self):
        """
        Load land use data from Strapi API (PostGIS landuse_zones table).
        
        API endpoint: GET /api/landuse-zones?filters[country][id][$eq]={country_id}
        PostGIS table: landuse_zones (with geometry_geojson column)
        """
        if not self.country_id:
            self.logger.warning("No country ID set for landuse data loading")
            return
        
        landuse_zones = await self.api_client.get_landuse_zones_by_country(self.country_id)
        self.logger.info(f"[LANDUSE] Loading {len(landuse_zones)} landuse zones from API (PostGIS)")
        
        for zone_data in landuse_zones:
            try:
                # Extract geometry from Strapi format
                geometry_data = zone_data.get('geometry_geojson') or zone_data.get('geometry')
                if not geometry_data:
                    continue
                
                geometry = shape(geometry_data)
                
                # Extract landuse type
                landuse_type = zone_data.get('zone_type', 'unknown')
                
                # Calculate population density based on land use
                population_density = self._estimate_population_density(landuse_type)
                
                if population_density > 0:
                    # Create population zone
                    zone = PopulationZone(
                        zone_id=f"landuse_{zone_data['id']}",
                        center_point=self._get_geometry_center(geometry),
                        geometry=geometry,
                        base_population=int(geometry.area * 1000000 * population_density),
                        zone_type=landuse_type,
                        spawn_rate_per_hour=population_density * 0.1,
                        peak_hours=self._get_peak_hours(landuse_type),
                        is_amenity=False
                    )
                    self.population_zones.append(zone)
            
            except Exception as e:
                self.logger.debug(f"Skipping invalid landuse zone {zone_data.get('id', 'unknown')}: {e}")
    
    async def _load_amenities_data_from_api(self):
        """
        Load amenities/POI data from Strapi API (PostGIS pois table).
        
        API endpoint: GET /api/pois?filters[country][id][$eq]={country_id}
        PostGIS table: pois (with latitude/longitude columns)
        """
        if not self.country_id:
            self.logger.warning("No country ID set for amenities data loading")
            return
        
        pois = await self.api_client.get_pois_by_country(self.country_id)
        self.logger.info(f"[POI] Loading {len(pois)} POIs from API (PostGIS)")
        
        for poi_data in pois:
            try:
                # Create point geometry from lat/lon
                lat = poi_data.get('latitude')
                lon = poi_data.get('longitude')
                if lat is None or lon is None:
                    continue
                
                geometry = Point(lon, lat)
                
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
                        peak_hours=self._get_amenity_peak_hours(poi_type),
                        is_amenity=True
                    )
                    self.amenity_zones.append(zone)
            
            except Exception as e:
                self.logger.debug(f"Skipping invalid POI {poi_data.get('id', 'unknown')}: {e}")
    
    async def _load_places_data_from_api(self):
        """
        Load place names from Strapi API (PostGIS places table).
        
        API endpoint: GET /api/places?filters[country][id][$eq]={country_id}
        PostGIS table: places (with geometry_geojson or lat/lon columns)
        """
        if not self.country_id:
            self.logger.warning("No country ID set for places data loading")
            return
        
        places = await self.api_client.get_places_by_country(self.country_id)
        self.logger.info(f"[PLACE] Loading {len(places)} places from API (PostGIS)")
        
        for place_data in places:
            try:
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
                self.logger.debug(f"Skipping invalid place {place_data.get('id', 'unknown')}: {e}")
    
    async def _load_regions_data_from_api(self):
        """
        Load regions from Strapi API (PostGIS regions table).
        
        API endpoint: GET /api/regions?filters[country][id][$eq]={country_id}
        PostGIS table: regions (with geometry_geojson column for boundaries)
        """
        if not self.country_id:
            self.logger.warning("No country ID set for regions data loading")
            return
        
        regions = await self.api_client.get_regions_by_country(self.country_id)
        self.logger.info(f"[REGION] Loading {len(regions)} regions from API (PostGIS)")
        
        for region_data in regions:
            try:
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
                self.transport_hubs.append(region_info)
            
            except Exception as e:
                self.logger.debug(f"Skipping invalid region: {e}")
    
    def _estimate_population_density(self, landuse_type: str) -> float:
        """
        Estimate population density based on land use type.
        
        ADJUSTED DENSITIES: Reduced for realistic transit-using population.
        These represent effective transit-using population, not total population.
        """
        density_map = {
            'residential': 120.0,
            'urban': 170.0,
            'suburban': 60.0,
            'rural': 7.0,
            'village': 48.0,
            'town': 85.0,
            'city': 240.0,
            'commercial': 34.0,
            'industrial': 14.0,
            'mixed': 95.0,
            'retail': 50.0,
            'office': 75.0
        }
        return density_map.get(landuse_type.lower(), 3.0)
    
    def _estimate_activity_level(self, amenity_type: str, properties: Dict) -> float:
        """
        Estimate activity level (spawn rate) for amenities.
        
        ADJUSTED RATES: Reduced for realistic evening spawn rates.
        Base rates assume peak activity - multiplied by temporal modifiers.
        """
        activity_map = {
            'school': 0.17,
            'university': 0.27,
            'hospital': 0.17,
            'clinic': 0.10,
            'shopping': 0.23,
            'mall': 0.34,
            'market': 0.20,
            'restaurant': 0.13,
            'cafe': 0.07,
            'bank': 0.10,
            'post_office': 0.07,
            'government': 0.13,
            'church': 0.05,
            'mosque': 0.05,
            'temple': 0.05,
            'park': 0.03,
            'beach': 0.08,
            'tourist': 0.17,
            'hotel': 0.12,
            'fuel': 0.05
        }
        return activity_map.get(amenity_type.lower(), 0.03)
    
    def _get_peak_hours(self, zone_type: str) -> List[int]:
        """Get peak hours for different zone types"""
        peak_hours_map = {
            'residential': [7, 8, 17, 18, 19],
            'commercial': [9, 10, 11, 12, 13, 14, 15, 16],
            'industrial': [6, 7, 15, 16, 17],
            'retail': [10, 11, 12, 13, 17, 18, 19],
            'office': [8, 9, 12, 13, 17, 18],
            'mixed': [8, 9, 12, 13, 17, 18, 19]
        }
        return peak_hours_map.get(zone_type.lower(), [9, 12, 17])
    
    def _get_amenity_peak_hours(self, amenity_type: str) -> List[int]:
        """Get peak hours for different amenity types"""
        amenity_peaks = {
            'school': [7, 8, 15, 16],
            'university': [8, 9, 10, 11, 14, 15, 16],
            'hospital': list(range(8, 18)),
            'shopping': [10, 11, 12, 17, 18, 19],
            'restaurant': [12, 13, 18, 19, 20],
            'bank': [9, 10, 11, 12, 14, 15, 16],
            'church': [9, 10, 18, 19],
            'beach': [10, 11, 12, 13, 14, 15, 16],
            'tourist': [9, 10, 11, 12, 13, 14, 15, 16]
        }
        return amenity_peaks.get(amenity_type.lower(), [10, 14, 18])
    
    def _get_geometry_center(self, geometry) -> Tuple[float, float]:
        """Get center point of geometry as (lat, lon)"""
        centroid = geometry.centroid
        return (centroid.y, centroid.x)
    
    def _enhance_nearby_zones(self, center: Tuple[float, float], name: str, place_type: str):
        """Enhance nearby zones with place name information"""
        for zone in self.population_zones:
            zone_center = zone.center_point
            distance = geodesic(center, zone_center).kilometers
            
            if distance < 1.0:  # Within 1km
                if name and name not in zone.zone_id:
                    zone.zone_id = f"{zone.zone_id}_{name.replace(' ', '_')}"
    
    def filter_zones_near_route(
        self,
        route_coordinates: List[Tuple[float, float]],
        buffer_km: float = 2.0
    ) -> Tuple[List[PopulationZone], List[PopulationZone]]:
        """
        Filter zones to only those within buffer distance of route.
        
        Args:
            route_coordinates: List of (lat, lon) points along route
            buffer_km: Buffer distance in kilometers
        
        Returns:
            Tuple of (filtered_population_zones, filtered_amenity_zones)
        """
        filtered_population = []
        filtered_amenity = []
        
        # Filter population zones
        for zone in self.population_zones:
            if self._is_zone_near_route(zone, route_coordinates, buffer_km):
                filtered_population.append(zone)
        
        # Filter amenity zones
        for zone in self.amenity_zones:
            if self._is_zone_near_route(zone, route_coordinates, buffer_km):
                filtered_amenity.append(zone)
        
        self.logger.info(
            f"Filtered zones: {len(filtered_population)} population, "
            f"{len(filtered_amenity)} amenity (±{buffer_km}km buffer)"
        )
        
        return filtered_population, filtered_amenity
    
    def _is_zone_near_route(
        self,
        zone: PopulationZone,
        route_coordinates: List[Tuple[float, float]],
        buffer_km: float
    ) -> bool:
        """Check if zone is within buffer distance of any route point"""
        zone_center = zone.center_point
        
        for route_point in route_coordinates:
            distance = geodesic(zone_center, route_point).kilometers
            if distance <= buffer_km:
                return True
        
        return False
