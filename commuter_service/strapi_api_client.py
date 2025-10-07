"""
Strapi API Client for Passenger Microservice
============================================

Single source of truth for all Strapi API access in the passenger system.
Provides a clean interface for accessing depots, routes, route-shapes, and shapes data.
"""

import asyncio
import logging
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class DepotData:
    """Depot information from Strapi API"""
    id: int
    depot_id: str
    name: str
    address: Optional[str]
    location: Optional[Dict[str, float]]  # {lat: float, lon: float}
    capacity: int
    is_active: bool


@dataclass
class RouteData:
    """Route information from Strapi API"""
    id: int
    short_name: str
    long_name: str
    parishes: Optional[List[str]]
    description: Optional[str]
    color: Optional[str]
    is_active: bool
    geometry_coordinates: List[List[float]]  # GPS coordinates from GTFS shapes
    route_length_km: float
    coordinate_count: int


class StrapiApiClient:
    """
    Centralized API client for accessing Strapi data in passenger microservice.
    
    This is the SINGLE SOURCE OF TRUTH for all API access in the passenger system.
    All other components should use this client instead of making direct HTTP requests.
    """
    
    def __init__(self, base_url: str = "http://localhost:1337"):
        self.base_url = base_url
        self.session: Optional[httpx.AsyncClient] = None
        self._connection_tested = False
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self) -> bool:
        """Initialize the HTTP session and test connectivity"""
        try:
            if not self.session:
                self.session = httpx.AsyncClient(timeout=30.0)
            
            # Test connection
            response = await self.session.get(f"{self.base_url}/api/countries", timeout=5.0)
            if response.status_code == 200:
                self._connection_tested = True
                logging.info(f"✅ Strapi API client connected to {self.base_url}")
                return True
            else:
                logging.error(f"❌ Strapi API connection failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Failed to connect to Strapi API: {e}")
            return False
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
            self._connection_tested = False
    
    def _ensure_connected(self):
        """Ensure API client is connected"""
        if not self.session or not self._connection_tested:
            raise RuntimeError("API client not connected. Call connect() first or use as async context manager.")
    
    async def get_all_depots(self) -> List[DepotData]:
        """Get all active depots from Strapi"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/depots",
                params={
                    "filters[is_active][$eq]": True,
                    "pagination[pageSize]": 100
                }
            )
            response.raise_for_status()
            data = response.json()
            
            depots = []
            for depot_data in data.get('data', []):
                depot = DepotData(
                    id=depot_data['id'],
                    depot_id=depot_data['depot_id'],
                    name=depot_data['name'],
                    address=depot_data.get('address'),
                    location=depot_data.get('location'),
                    capacity=depot_data.get('capacity', 50),
                    is_active=depot_data.get('is_active', True)
                )
                depots.append(depot)
            
            logging.info(f"✅ Retrieved {len(depots)} depots from Strapi")
            return depots
            
        except Exception as e:
            logging.error(f"❌ Failed to get depots: {e}")
            return []
    
    async def get_all_routes(self) -> List[RouteData]:
        """Get all active routes with geometry from Strapi using GTFS structure"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/routes",
                params={
                    "filters[is_active][$eq]": True,
                    "pagination[pageSize]": 100
                }
            )
            response.raise_for_status()
            data = response.json()
            
            routes = []
            for route_data in data.get('data', []):
                # Load geometry using GTFS structure
                coordinates, route_length = await self._load_route_geometry(route_data['short_name'])
                
                route = RouteData(
                    id=route_data['id'],
                    short_name=route_data['short_name'],
                    long_name=route_data['long_name'],
                    parishes=route_data.get('parishes'),
                    description=route_data.get('description'),
                    color=route_data.get('color'),
                    is_active=route_data.get('is_active', True),
                    geometry_coordinates=coordinates,
                    route_length_km=route_length,
                    coordinate_count=len(coordinates)
                )
                routes.append(route)
            
            logging.info(f"✅ Retrieved {len(routes)} routes with geometry from Strapi")
            return routes
            
        except Exception as e:
            logging.error(f"❌ Failed to get routes: {e}")
            return []
    
    async def _load_route_geometry(self, route_code: str) -> tuple[List[List[float]], float]:
        """Load route geometry using GTFS routes → route-shapes → shapes structure"""
        try:
            # Step 1: Get default route-shape for this route
            shape_link_response = await self.session.get(
                f"{self.base_url}/api/route-shapes",
                params={
                    "filters[route_id][$eq]": route_code,
                    "filters[is_default][$eq]": True
                }
            )
            
            if shape_link_response.status_code != 200:
                logging.warning(f"No route-shapes found for route {route_code}")
                return [], 0.0
                
            shape_link_data = shape_link_response.json()
            route_shapes = shape_link_data.get('data', [])
            
            if not route_shapes:
                logging.warning(f"No default route-shape found for route {route_code}")
                return [], 0.0
            
            shape_id = route_shapes[0].get('shape_id')
            
            # Step 2: Get actual GPS coordinates from shapes table ordered by sequence
            shapes_response = await self.session.get(
                f"{self.base_url}/api/shapes",
                params={
                    "filters[shape_id][$eq]": shape_id,
                    "sort": "shape_pt_sequence",
                    "pagination[pageSize]": 1000
                }
            )
            
            if shapes_response.status_code != 200:
                logging.warning(f"No shapes found for shape_id {shape_id}")
                return [], 0.0
                
            shapes_data = shapes_response.json()
            shape_points = shapes_data.get('data', [])
            
            if not shape_points:
                logging.warning(f"No shape points found for shape_id {shape_id}")
                return [], 0.0
            
            # Convert shape points to coordinate array
            coordinates = []
            for point in shape_points:
                lon = point.get('shape_pt_lon')
                lat = point.get('shape_pt_lat')
                if lon is not None and lat is not None:
                    coordinates.append([lon, lat])  # GeoJSON format: [longitude, latitude]
            
            # Calculate route length
            route_length = self._calculate_route_length(coordinates) if coordinates else 0.0
            
            logging.debug(f"✅ Loaded {len(coordinates)} coordinates for route {route_code}, length: {route_length:.1f}km")
            return coordinates, route_length
            
        except Exception as e:
            logging.error(f"❌ Failed to load geometry for route {route_code}: {e}")
            return [], 0.0
    
    def _calculate_route_length(self, coordinates: List[List[float]]) -> float:
        """Calculate total route length from coordinates using Haversine formula"""
        if len(coordinates) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(len(coordinates) - 1):
            lon1, lat1 = coordinates[i]
            lon2, lat2 = coordinates[i + 1]
            distance = self._haversine_distance(lat1, lon1, lat2, lon2)
            total_length += distance
        
        return total_length
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula (km)"""
        import math
        
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
    
    async def get_countries(self) -> List[Dict[str, Any]]:
        """Get all countries for plugin configuration"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(f"{self.base_url}/api/countries")
            response.raise_for_status()
            data = response.json()
            
            logging.debug(f"✅ Retrieved {len(data.get('data', []))} countries")
            return data.get('data', [])
            
        except Exception as e:
            logging.error(f"❌ Failed to get countries: {e}")
            return []
    
    async def get_passenger_plugin_config(self, country_code: str) -> Optional[Dict[str, Any]]:
        """Get passenger plugin configuration for a specific country"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/passenger-plugin-configs",
                params={
                    "filters[country_code][$eq]": country_code,
                    "filters[is_active][$eq]": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                configs = data.get('data', [])
                if configs:
                    logging.info(f"✅ Retrieved plugin config for country {country_code}")
                    return configs[0]
                else:
                    logging.warning(f"No plugin config found for country {country_code}")
                    return None
            else:
                logging.warning(f"Plugin config endpoint not found (HTTP {response.status_code})")
                return None
                
        except Exception as e:
            logging.warning(f"Plugin config not available for {country_code}: {e}")
            return None
    
    # ==================== GEOGRAPHIC DATA ACCESS METHODS ====================
    
    async def get_pois_by_country(self, country_id: int) -> List[Dict[str, Any]]:
        """Get all POIs for a specific country"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/pois",
                params={
                    "filters[country][id][$eq]": country_id,
                    "pagination[pageSize]": 2000,  # Large limit for geographic data
                    "sort": "name:asc"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            pois = data.get('data', [])
            logging.info(f"✅ Retrieved {len(pois)} POIs for country {country_id}")
            return pois
            
        except Exception as e:
            logging.error(f"❌ Failed to get POIs for country {country_id}: {e}")
            return []
    
    async def get_places_by_country(self, country_id: int) -> List[Dict[str, Any]]:
        """Get all Places (place names) for a specific country"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/places",
                params={
                    "filters[country][id][$eq]": country_id,
                    "pagination[pageSize]": 10000,  # Very large limit for place names
                    "sort": "name:asc"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            places = data.get('data', [])
            logging.info(f"✅ Retrieved {len(places)} Places for country {country_id}")
            return places
            
        except Exception as e:
            logging.error(f"❌ Failed to get Places for country {country_id}: {e}")
            return []
    
    async def get_landuse_zones_by_country(self, country_id: int) -> List[Dict[str, Any]]:
        """Get all Landuse zones for a specific country"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/landuse-zones",
                params={
                    "filters[country][id][$eq]": country_id,
                    "pagination[pageSize]": 5000,  # Large limit for landuse zones
                    "sort": "zone_type:asc"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            zones = data.get('data', [])
            logging.info(f"✅ Retrieved {len(zones)} Landuse zones for country {country_id}")
            return zones
            
        except Exception as e:
            logging.error(f"❌ Failed to get Landuse zones for country {country_id}: {e}")
            return []
    
    async def get_regions_by_country(self, country_id: int) -> List[Dict[str, Any]]:
        """Get all Regions for a specific country"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/regions",
                params={
                    "filters[country][id][$eq]": country_id,
                    "pagination[pageSize]": 1000,  # Moderate limit for regions
                    "sort": "name:asc"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            regions = data.get('data', [])
            logging.info(f"✅ Retrieved {len(regions)} Regions for country {country_id}")
            return regions
            
        except Exception as e:
            logging.error(f"❌ Failed to get Regions for country {country_id}: {e}")
            return []
    
    async def get_country_by_code(self, country_code: str) -> Optional[Dict[str, Any]]:
        """Get country information by country code"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/countries",
                params={
                    "filters[code][$eq]": country_code.upper(),
                    "pagination[pageSize]": 1
                }
            )
            response.raise_for_status()
            data = response.json()
            
            countries = data.get('data', [])
            if countries:
                logging.info(f"✅ Retrieved country info for {country_code}")
                return countries[0]
            else:
                logging.warning(f"No country found with code {country_code}")
                return None
            
        except Exception as e:
            logging.error(f"❌ Failed to get country {country_code}: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the API connection"""
        try:
            if not self.session:
                return {"status": "disconnected", "message": "No active session"}
            
            response = await self.session.get(f"{self.base_url}/api/countries", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "base_url": self.base_url,
                    "countries_count": len(data.get('data', [])),
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "status": "unhealthy",
                    "base_url": self.base_url,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "base_url": self.base_url,
                "error": str(e)
            }