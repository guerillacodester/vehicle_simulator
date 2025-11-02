"""
Geospatial Service Client
=========================

Pure business logic client with no UI dependencies.
Can be used from any interface (CLI, GUI, web, .NET via pythonnet).
"""

import requests
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urljoin

from .models import Address, RouteGeometry, Building, DepotInfo, SpawnPoint, HealthResponse

try:
    from common.config_provider import get_config
    _config_available = True
except ImportError:
    _config_available = False


class GeospatialClient:
    """
    Interface-agnostic geospatial service client.
    
    Provides access to spatial queries, geocoding, and route geometry.
    
    Example (Basic):
        client = GeospatialClient("http://localhost:6000")
        address = client.reverse_geocode(13.0969, -59.6137)
        print(address.formatted)
    
    Example (Route Geometry):
        geometry = client.get_route_geometry("route_id_123")
        print(f"Route length: {geometry.total_distance_meters}m")
    
    Example (Auto-config):
        client = GeospatialClient()  # Loads URL from config.ini
        address = client.reverse_geocode(13.0, -59.6)
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize geospatial client.
        
        Args:
            base_url: Base URL of geospatial service. If None, loads from config.ini.
                     Defaults to "http://localhost:6000" if config unavailable.
        """
        if base_url is None:
            if _config_available:
                try:
                    config = get_config()
                    base_url = config.infrastructure.geospatial_url
                except Exception:
                    base_url = "http://localhost:6000"  # Fallback
            else:
                base_url = "http://localhost:6000"  # Fallback
        
        self.base_url = base_url.rstrip('/')
    
    # ==================== Health ====================
    
    def health_check(self) -> HealthResponse:
        """
        Check service health.
        
        Returns:
            HealthResponse with status and latency
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/health")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return HealthResponse.model_validate(response.json())
    
    # ==================== Geocoding ====================
    
    def reverse_geocode(self, lat: float, lon: float) -> Address:
        """
        Reverse geocode coordinates to address.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Address object with formatted address
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/geocode/reverse")
        response = requests.post(
            url,
            json={"lat": lat, "lon": lon},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return Address(
            formatted=data.get("display_name", "Unknown"),
            street=data.get("address", {}).get("road"),
            amenity=data.get("address", {}).get("amenity"),
            lat=lat,
            lon=lon
        )
    
    # ==================== Route Geometry ====================
    
    def get_route_geometry(self, route_id: str) -> RouteGeometry:
        """
        Get route geometry as GeoJSON LineString.
        
        Args:
            route_id: Route document ID
        
        Returns:
            RouteGeometry with LineString and distance
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, f"/spatial/route-geometry/{route_id}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return RouteGeometry.model_validate(data)
    
    def get_route_geometry_by_short_name(self, short_name: str) -> RouteGeometry:
        """
        Get route geometry by route short name (e.g., "1", "5").
        
        Args:
            short_name: Route short name
        
        Returns:
            RouteGeometry with LineString and distance
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, f"/routes/by-short-name/{short_name}/geometry")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return RouteGeometry.model_validate(data)
    
    # ==================== Buildings ====================
    
    def get_buildings_near_route(
        self,
        route_id: str,
        buffer_meters: int = 100,
        amenity_filter: Optional[str] = None
    ) -> List[Building]:
        """
        Get buildings near a route.
        
        Args:
            route_id: Route document ID
            buffer_meters: Buffer distance from route
            amenity_filter: Filter by amenity type (e.g., "school", "hospital")
        
        Returns:
            List of Building objects
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/spatial/route-buildings")
        params = {
            "route_id": route_id,
            "buffer_meters": buffer_meters
        }
        if amenity_filter:
            params["amenity"] = amenity_filter
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return [Building.model_validate(b) for b in data.get("buildings", [])]
    
    # ==================== Depots ====================
    
    def get_depot_by_route(self, route_id: str) -> DepotInfo:
        """
        Get depot information for a route.
        
        Args:
            route_id: Route document ID
        
        Returns:
            DepotInfo object
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, f"/routes/by-document-id/{route_id}/depot")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return DepotInfo.model_validate(data["depot"])
    
    # ==================== Spawn Points ====================
    
    def get_spawn_points(
        self,
        route_id: str,
        num_points: int = 50
    ) -> List[SpawnPoint]:
        """
        Get potential spawn points along a route.
        
        Args:
            route_id: Route document ID
            num_points: Number of spawn points to generate
        
        Returns:
            List of SpawnPoint objects
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, f"/spawn/route/{route_id}/points")
        params = {"num_points": num_points}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [SpawnPoint.model_validate(p) for p in data.get("spawn_points", [])]
    
    def calculate_route_distance(self, coords: List[Tuple[float, float]]) -> float:
        """
        Calculate distance along a route path.
        
        Args:
            coords: List of (lat, lon) tuples
        
        Returns:
            Distance in meters
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/spatial/calculate-distance")
        response = requests.post(
            url,
            json={"coordinates": [[lon, lat] for lat, lon in coords]},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("distance_meters", 0.0)
