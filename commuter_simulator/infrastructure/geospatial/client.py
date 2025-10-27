"""
Geospatial Services API Client

Simple wrapper for spatial queries used by passenger spawning logic.
Replaces direct PostGIS queries with HTTP API calls.
"""

import requests
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GeospatialClient:
    """
    Client for Geospatial Services API.
    
    Phase 1: Uses FastAPI service at http://localhost:8001
    Phase 2: Will support load balancing, retries, caching
    """
    
    def __init__(self, base_url: str = "http://localhost:8001", timeout: int = 5):
        """
        Initialize client.
        
        Args:
            base_url: Base URL of geospatial service (default: http://localhost:8001)
            timeout: Request timeout in seconds (default: 5)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify API is reachable on initialization."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Connected to Geospatial API: {data.get('status', 'unknown')}")
            else:
                logger.warning(f"⚠️ Geospatial API returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Cannot connect to Geospatial API at {self.base_url}: {e}")
            raise ConnectionError(f"Geospatial API unavailable at {self.base_url}")
    
    def reverse_geocode(
        self,
        latitude: float,
        longitude: float,
        highway_radius_meters: int = 500,
        poi_radius_meters: int = 1000
    ) -> Dict:
        """
        Get human-readable address for coordinates.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            highway_radius_meters: Search radius for highways (default: 500m)
            poi_radius_meters: Search radius for POIs (default: 1000m)
        
        Returns:
            {
                "address": str,
                "highway": {...} or None,
                "poi": {...} or None,
                "parish": {...} or None,
                "latency_ms": float
            }
        """
        try:
            response = requests.post(
                f"{self.base_url}/geocode/reverse",
                json={
                    "latitude": latitude,
                    "longitude": longitude,
                    "highway_radius_meters": highway_radius_meters,
                    "poi_radius_meters": poi_radius_meters
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Reverse geocode failed for ({latitude}, {longitude}): {e}")
            return {
                "address": "Unknown location",
                "highway": None,
                "poi": None,
                "parish": None,
                "error": str(e)
            }
    
    def check_geofence(self, latitude: float, longitude: float) -> Dict:
        """
        Check which administrative zones contain a point.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
        
        Returns:
            {
                "inside_region": bool,
                "region": {...} or None,
                "inside_landuse": bool,
                "landuse": {...} or None,
                "latency_ms": float
            }
        """
        try:
            response = requests.post(
                f"{self.base_url}/geofence/check",
                json={"latitude": latitude, "longitude": longitude},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Geofence check failed for ({latitude}, {longitude}): {e}")
            return {
                "inside_region": False,
                "region": None,
                "inside_landuse": False,
                "landuse": None,
                "error": str(e)
            }
    
    def find_nearby_buildings(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 1000,
        limit: int = 50
    ) -> Dict:
        """
        Find buildings within radius of a point.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            radius_meters: Search radius in meters (default: 1000)
            limit: Maximum results to return (default: 50)
        
        Returns:
            {
                "count": int,
                "buildings": [{...}],
                "latency_ms": float
            }
        """
        try:
            response = requests.get(
                f"{self.base_url}/spatial/nearby-buildings",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "radius_meters": radius_meters,
                    "limit": limit
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Nearby buildings search failed for ({latitude}, {longitude}): {e}")
            return {
                "count": 0,
                "buildings": [],
                "error": str(e)
            }
    
    # TODO: Implement when POI proximity queries are needed
    # def find_nearby_pois(
    #     self,
    #     latitude: float,
    #     longitude: float,
    #     radius_meters: int = 2000,
    #     poi_types: Optional[List[str]] = None,
    #     limit: int = 50
    # ) -> Dict:
    #     """Find POIs within radius of a point."""
    #     pass
    
    def buildings_along_route(
        self,
        route_coordinates: list,
        buffer_meters: int = 500,
        limit: int = 100
    ) -> Dict:
        """
        Find buildings within buffer of a route by querying multiple points.
        Used for route-based passenger spawning.
        
        Args:
            route_coordinates: List of [lon, lat] pairs representing the route
            buffer_meters: Buffer distance in meters (default: 500)
            limit: Maximum results to return (default: 100)
        
        Returns:
            {
                "count": int,
                "buildings": [{...}],
                "latency_ms": float
            }
        """
        try:
            # Sample points along the route to ensure good coverage
            # Use every Nth point to keep queries efficient
            sample_interval = max(1, len(route_coordinates) // 10)  # Sample ~10 points
            sampled_points = route_coordinates[::sample_interval]
            
            if not sampled_points:
                sampled_points = route_coordinates[:1]  # At least use start point
            
            # Track unique buildings by ID to avoid duplicates
            unique_buildings = {}
            total_latency = 0
            
            # Query buildings at each sampled point
            for lon, lat in sampled_points:
                response = requests.get(
                    f"{self.base_url}/spatial/nearby-buildings",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "radius_meters": buffer_meters,
                        "limit": limit
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                total_latency += data.get('latency_ms', 0)
                
                # Collect unique buildings
                for building in data.get('buildings', []):
                    bid = building.get('building_id')
                    if bid not in unique_buildings:
                        unique_buildings[bid] = building
            
            # Convert to list and truncate to limit
            buildings_list = list(unique_buildings.values())[:limit]
            
            return {
                "count": len(buildings_list),
                "buildings": buildings_list,
                "latency_ms": round(total_latency, 2)
            }
        except Exception as e:
            logger.error(f"Route buildings search failed: {e}")
            return {
                "count": 0,
                "buildings": [],
                "error": str(e)
            }
    
    def depot_catchment_area(
        self,
        depot_latitude: float,
        depot_longitude: float,
        catchment_radius_meters: int = 2000,
        limit: int = 200
    ) -> Dict:
        """
        Find buildings in depot catchment area.
        Used for depot-based passenger spawning.
        
        Args:
            depot_latitude: Depot latitude
            depot_longitude: Depot longitude
            catchment_radius_meters: Catchment radius in meters (default: 2000)
            limit: Maximum results to return (default: 200)
        
        Returns:
            {
                "count": int,
                "buildings": [{...}],
                "pois": [{...}],
                "latency_ms": float
            }
        """
        try:
            response = requests.get(
                f"{self.base_url}/spatial/depot-catchment",
                params={
                    "lat": depot_latitude,
                    "lon": depot_longitude,
                    "radius_meters": catchment_radius_meters,
                    "limit": limit
                },
                timeout=self.timeout * 2
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Depot catchment search failed for ({depot_latitude}, {depot_longitude}): {e}")
            return {
                "count": 0,
                "buildings": [],
                "pois": [],
                "error": str(e)
            }


# Module-level singleton for convenience
_default_client: Optional[GeospatialClient] = None


def get_client(base_url: str = "http://localhost:8001") -> GeospatialClient:
    """
    Get or create default geospatial client.
    
    Args:
        base_url: Base URL for geospatial service
    
    Returns:
        GeospatialClient instance
    """
    global _default_client
    if _default_client is None:
        _default_client = GeospatialClient(base_url=base_url)
    return _default_client
