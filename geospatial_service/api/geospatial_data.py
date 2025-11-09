from fastapi import HTTPException
from redis import Redis
import httpx
from typing import Any, Dict, List
from geopy.distance import geodesic
import configparser

# Initialize Redis client
redis_client = Redis(host='localhost', port=6379, decode_responses=True)

# Load configuration
config = configparser.ConfigParser()
config.read("e:\\projects\\github\\vehicle_simulator\\config.ini")

class GeospatialData:
    """
    A single source of truth for geospatial data, consolidating APIs and caching results.
    """

    @staticmethod
    async def fetch_from_cache_or_api(cache_key: str, api_url_key: str, params: Dict[str, Any] = None) -> Any:
        """
        Fetch data from Redis cache if available, otherwise fetch from API and cache the result.
        """
        # Resolve API URL from config or accept a full URL directly
        if isinstance(api_url_key, str) and api_url_key.lower().startswith("http"):
            api_url = api_url_key
        else:
            api_url = config.get("strapi", api_url_key, fallback=None)
        if not api_url:
            raise ValueError(f"API URL for key '{api_url_key}' not found in config.ini")
        if not api_url:
            raise ValueError(f"API URL for key '{api_url_key}' not found in config.ini")

        # Check Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return cached_data
        # Fetch from API
        try:
            async with httpx.AsyncClient() as client:
                # Remove any None-valued params to avoid invalid query keys
                cleaned_params = {k: v for k, v in (params or {}).items() if v is not None}
                response = await client.get(api_url, params=cleaned_params)
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                data = response.json()

                # Cache the result
                redis_client.set(cache_key, data, ex=3600)  # Cache for 1 hour
                return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")

    @staticmethod
    async def get_all_routes(include_geometry: bool = False, include_metrics: bool = False) -> List[Dict[str, Any]]:
        """
        Get all routes, optionally including geometry and metrics.
        """
        cache_key = f"routes:geometry={include_geometry}:metrics={include_metrics}"
        # Build the full Strapi API endpoint for routes. If `url` in config is just the base,
        # append the Strapi collection endpoint for routes.
        base_url = config.get("strapi", "url", fallback=None)
        if not base_url:
            raise ValueError("Strapi base url not found in config.ini")
        api_url = base_url.rstrip('/') + '/api/routes'
        params = {
            "populate": "*" if include_geometry else None,
            "include_metrics": include_metrics
        }
        return await GeospatialData.fetch_from_cache_or_api(cache_key, api_url, params)

    @staticmethod
    async def get_all_depots(include_buildings: bool = False, include_routes: bool = False) -> List[Dict[str, Any]]:
        """
        Get all depots, optionally including building counts and associated routes.
        """
        cache_key = f"depots:buildings={include_buildings}:routes={include_routes}"
        base_url = config.get("strapi", "url", fallback=None)
        if not base_url:
            raise ValueError("Strapi base url not found in config.ini")
        api_url = base_url.rstrip('/') + '/api/depots'
        params = {
            "include_buildings": include_buildings,
            "include_routes": include_routes
        }
        return await GeospatialData.fetch_from_cache_or_api(cache_key, api_url, params)

    @staticmethod
    async def reverse_geocode(lat: float, lon: float, highway_radius: int = 500, poi_radius: int = 1000) -> Dict[str, Any]:
        """
        Reverse geocode latitude/longitude to a human-readable address.
        """
        cache_key = f"reverse_geocode:lat={lat}:lon={lon}:highway_radius={highway_radius}:poi_radius={poi_radius}"
        api_url = "http://geospatial-service/api/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "highway_radius_meters": highway_radius,
            "poi_radius_meters": poi_radius
        }
        return await GeospatialData.fetch_from_cache_or_api(cache_key, api_url, params)

    @staticmethod
    async def get_route_geometry(route_id: str) -> Dict[str, Any]:
        """
        Get the geometry of a specific route.
        """
        cache_key = f"route_geometry:{route_id}"
        api_url = f"http://geospatial-service/api/route-geometry/{route_id}"
        return await GeospatialData.fetch_from_cache_or_api(cache_key, api_url)

    @staticmethod
    async def get_depot_analysis(depot_id: int, depot_radius: int = 800, route_buffer: int = 100, passengers_per_building: float = 0.05) -> Dict[str, Any]:
        """
        Perform a comprehensive spawn analysis for a depot.
        """
        cache_key = f"depot_analysis:{depot_id}:radius={depot_radius}:buffer={route_buffer}:passengers={passengers_per_building}"
        api_url = f"http://geospatial-service/api/depot-analysis/{depot_id}"
        params = {
            "depot_radius": depot_radius,
            "route_buffer": route_buffer,
            "passengers_per_building": passengers_per_building
        }
        return await GeospatialData.fetch_from_cache_or_api(cache_key, api_url, params)

    @staticmethod
    async def compute_distance_between_termini(route_id: str) -> float:
        """
        Compute the distance between the termini of a route using its geometry.
        
        Args:
            route_id (str): The ID of the route.
        
        Returns:
            float: The distance between the termini in kilometers.
        """
        route_geometry = await GeospatialData.get_route_geometry(route_id)
        coordinates = route_geometry.get("coordinates", [])

        if len(coordinates) < 2:
            raise ValueError("Route geometry must have at least two points to compute termini distance.")

        start_point = coordinates[0]  # First point (latitude, longitude)
        end_point = coordinates[-1]  # Last point (latitude, longitude)

        # Compute geodesic distance
        distance_km = geodesic(start_point, end_point).kilometers
        return distance_km