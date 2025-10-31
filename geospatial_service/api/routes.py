"""
Routes API - Consolidated route operations
All route-related queries in one place (Single Responsibility Principle)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import configparser
from pathlib import Path
import httpx

from services.postgis_client import postgis_client

router = APIRouter(prefix="/routes", tags=["Routes"])

# Load Strapi URL from config
config = configparser.ConfigParser()
config_path = Path(__file__).parent.parent.parent / "config.ini"
config.read(config_path, encoding='utf-8')
STRAPI_URL = config.get('infrastructure', 'strapi_url', fallback='http://localhost:1337')


class RouteGeometry(BaseModel):
    """Route geometry with metrics"""
    route_id: str
    short_name: str
    long_name: str
    coordinates: List[List[float]]
    num_segments: int
    num_points: int
    total_distance_meters: float


class RouteBuilding(BaseModel):
    """Building near a route"""
    building_id: int
    document_id: str
    latitude: float
    longitude: float
    distance_meters: float


class RouteMetrics(BaseModel):
    """Route performance metrics"""
    route_id: str
    short_name: str
    long_name: str
    total_distance_meters: float
    num_segments: int
    num_points: int
    estimated_travel_time_minutes: float
    buildings_within_100m: int
    buildings_within_500m: int


class RouteSummary(BaseModel):
    """Route summary for listings"""
    route_id: int
    document_id: Optional[str]
    short_name: Optional[str]
    long_name: Optional[str]
    distance_km: Optional[float]
    num_stops: Optional[int]


class RouteDetail(BaseModel):
    """Detailed route information"""
    route_id: int
    document_id: Optional[str]
    short_name: Optional[str]
    long_name: Optional[str]
    route_type: Optional[str]
    distance_km: Optional[float]
    geometry: Optional[Dict[str, Any]]
    depots: Optional[List[Dict[str, Any]]]
    building_count_100m: Optional[int]
    building_count_500m: Optional[int]


@router.get("/all", summary="List all routes")
async def list_all_routes(
    include_geometry: bool = Query(False, description="Include route geometry (slower)"),
    include_metrics: bool = Query(False, description="Include building counts (slower)"),
) -> Dict[str, Any]:
    """
    Get list of all routes in the system.
    
    Returns basic route information by default.
    Use query params to include geometry and metrics.
    """
    start_time = time.time()
    
    # Get routes from Strapi
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{STRAPI_URL}/api/routes",
                params={
                    "pagination[pageSize]": 1000,
                    "populate": "*" if include_geometry else "basic"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail="Strapi service unavailable. This endpoint requires Strapi CMS to be running."
                )
            
            data = response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Strapi CMS is not running. This endpoint requires Strapi to fetch route data."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Strapi CMS request timed out."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Strapi CMS: {str(e)}"
        )
    
    routes = data.get('data', [])
    
    # Build route list
    route_list = []
    for route in routes:
        route_id = route['id']
        attrs = route['attributes']
        
        route_info = {
            'route_id': route_id,
            'document_id': attrs.get('documentId') or attrs.get('document_id'),
            'short_name': attrs.get('route_short_name'),
            'long_name': attrs.get('route_long_name'),
            'distance_km': attrs.get('shape_dist_traveled'),
        }
        
        if include_geometry:
            route_info['geometry'] = attrs.get('route_geometry')
        
        if include_metrics and route_info.get('document_id'):
            # Query building counts
            try:
                buildings_100m = await postgis_client.get_buildings_near_route(
                    route_id=route_info['document_id'],
                    buffer_meters=100,
                    limit=10000
                )
                buildings_500m = await postgis_client.get_buildings_near_route(
                    route_id=route_info['document_id'],
                    buffer_meters=500,
                    limit=10000
                )
                route_info['building_count_100m'] = len(buildings_100m)
                route_info['building_count_500m'] = len(buildings_500m)
            except:
                route_info['building_count_100m'] = None
                route_info['building_count_500m'] = None
        
        route_list.append(route_info)
    
    latency_ms = (time.time() - start_time) * 1000
    
    return {
        'routes': route_list,
        'count': len(route_list),
        'includes': {
            'geometry': include_geometry,
            'metrics': include_metrics
        },
        'latency_ms': round(latency_ms, 2)
    }


@router.get("/{route_id}/geometry", summary="Get route geometry")
async def get_route_geometry(route_id: str) -> Dict[str, Any]:
    """
    Get complete route geometry with all segments concatenated.
    
    Single source of truth for route geometry.
    Returns full route coordinates and metrics.
    """
    start_time = time.time()
    
    try:
        route_data = await postgis_client.get_route_geometry(route_id)
        
        if not route_data:
            raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'route_id': route_id,
            'short_name': route_data.get('short_name', 'Unknown'),
            'long_name': route_data.get('long_name', 'Unknown'),
            'coordinates': route_data.get('coordinates', []),
            'num_segments': route_data.get('num_segments', 0),
            'num_points': len(route_data.get('coordinates', [])),
            'total_distance_meters': route_data.get('total_distance_meters', 0),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route geometry query failed: {str(e)}")


@router.get("/{route_id}/buildings", summary="Get buildings along route")
async def get_route_buildings(
    route_id: str,
    buffer_meters: int = Query(100, ge=10, le=1000, description="Buffer around route in meters"),
    limit: int = Query(5000, ge=1, le=10000, description="Maximum buildings to return")
) -> Dict[str, Any]:
    """
    Get all buildings within buffer distance of route.
    
    Essential for route-based passenger spawning.
    """
    start_time = time.time()
    
    try:
        buildings_data = await postgis_client.get_buildings_near_route(
            route_id=route_id,
            buffer_meters=buffer_meters,
            limit=limit
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'route_id': route_id,
            'buffer_meters': buffer_meters,
            'buildings': buildings_data,
            'count': len(buildings_data),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route buildings query failed: {str(e)}")


@router.get("/{route_id}/metrics", summary="Get route metrics")
async def get_route_metrics(route_id: str) -> RouteMetrics:
    """
    Get comprehensive route metrics including:
    - Distance and segments
    - Building density
    - Estimated travel time
    """
    start_time = time.time()
    
    # Get geometry
    route_data = await postgis_client.get_route_geometry(route_id)
    if not route_data:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
    
    # Get building counts at different buffers
    buildings_100m = await postgis_client.get_buildings_near_route(route_id, 100, 10000)
    buildings_500m = await postgis_client.get_buildings_near_route(route_id, 500, 10000)
    
    # Calculate estimated travel time (assuming 30 km/h average)
    distance_meters = route_data.get('total_distance_meters', 0)
    travel_time_minutes = (distance_meters / 1000) / 30 * 60
    
    return RouteMetrics(
        route_id=route_id,
        short_name=route_data.get('short_name', 'Unknown'),
        long_name=route_data.get('long_name', 'Unknown'),
        total_distance_meters=distance_meters,
        num_segments=route_data.get('num_segments', 0),
        num_points=len(route_data.get('coordinates', [])),
        estimated_travel_time_minutes=round(travel_time_minutes, 1),
        buildings_within_100m=len(buildings_100m),
        buildings_within_500m=len(buildings_500m)
    )


@router.get("/{route_id}/coverage", summary="Get route coverage area")
async def get_route_coverage(
    route_id: str,
    buffer_meters: int = Query(500, ge=100, le=2000, description="Coverage buffer in meters")
) -> Dict[str, Any]:
    """
    Get the service coverage area (buffer polygon) for a route.
    
    Returns GeoJSON polygon representing the area served by this route.
    """
    start_time = time.time()
    
    try:
        # Get route geometry
        route_data = await postgis_client.get_route_geometry(route_id)
        if not route_data:
            raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
        
        coordinates = route_data.get('coordinates', [])
        
        # Calculate coverage area using PostGIS
        # This creates a buffer polygon around the route
        query = """
            WITH route_line AS (
                SELECT ST_MakeLine(
                    ARRAY(
                        SELECT ST_SetSRID(ST_MakePoint(coord[1], coord[2]), 4326)::geography
                        FROM unnest($1::float[][]) AS coord
                    )
                ) AS geom
            )
            SELECT 
                ST_AsGeoJSON(ST_Buffer(geom, $2))::json AS coverage_polygon,
                ST_Area(ST_Buffer(geom, $2)) AS area_square_meters
            FROM route_line
        """
        
        result = await postgis_client.execute_query(query, coordinates, buffer_meters)
        
        if not result:
            raise HTTPException(status_code=500, detail="Coverage calculation failed")
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'route_id': route_id,
            'buffer_meters': buffer_meters,
            'coverage_polygon': result[0]['coverage_polygon'],
            'area_square_meters': result[0]['area_square_meters'],
            'area_square_km': round(result[0]['area_square_meters'] / 1_000_000, 2),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Coverage calculation failed: {str(e)}")


@router.post("/nearest", summary="Find nearest route to point")
async def find_nearest_route(
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Find the nearest route to a given point.
    
    Request body: {"latitude": 13.1, "longitude": -59.6, "max_distance_meters": 5000}
    
    Useful for determining which route services a location.
    """
    start_time = time.time()
    
    latitude = request_data.get('latitude')
    longitude = request_data.get('longitude')
    max_distance_meters = request_data.get('max_distance_meters', 5000)
    
    if latitude is None or longitude is None:
        raise HTTPException(status_code=400, detail="latitude and longitude are required")
    if not (-90 <= latitude <= 90):
        raise HTTPException(status_code=400, detail="latitude must be between -90 and 90")
    if not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="longitude must be between -180 and 180")
    
    try:
        # Query nearest highway (route) from PostGIS
        query = """
            SELECT 
                document_id,
                name,
                highway_type,
                ST_Distance(
                    ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                    geom::geography
                ) AS distance_meters
            FROM highways
            WHERE ST_DWithin(
                ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                geom::geography,
                $3
            )
            ORDER BY distance_meters ASC
            LIMIT 1
        """
        
        result = await postgis_client.execute_query(
            query, latitude, longitude, max_distance_meters
        )
        
        if not result:
            return {
                'found': False,
                'message': f'No routes within {max_distance_meters}m',
                'latitude': latitude,
                'longitude': longitude,
                'max_distance_meters': max_distance_meters
            }
        
        route = result[0]
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'found': True,
            'route': {
                'document_id': route['document_id'],
                'name': route['name'],
                'highway_type': route['highway_type'],
                'distance_meters': round(route['distance_meters'], 2)
            },
            'query_point': {
                'latitude': latitude,
                'longitude': longitude
            },
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nearest route query failed: {str(e)}")


@router.get("/{route_id}", summary="Get detailed route information")
async def get_route_detail(
    route_id: int,
    include_geometry: bool = Query(True, description="Include route geometry"),
    include_buildings: bool = Query(False, description="Include building counts")
) -> Dict[str, Any]:
    """
    Get comprehensive route details.
    
    Single endpoint for all route information.
    """
    start_time = time.time()
    
    # Get from Strapi
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{STRAPI_URL}/api/routes/{route_id}?populate=*")
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
        
        data = response.json()
        attrs = data['data']['attributes']
    
    route_detail = {
        'route_id': route_id,
        'document_id': attrs.get('documentId') or attrs.get('document_id'),
        'short_name': attrs.get('route_short_name'),
        'long_name': attrs.get('route_long_name'),
        'route_type': attrs.get('route_type'),
        'distance_km': attrs.get('shape_dist_traveled'),
    }
    
    if include_geometry:
        route_detail['geometry'] = attrs.get('route_geometry')
    
    if include_buildings and route_detail.get('document_id'):
        try:
            buildings_100m = await postgis_client.get_buildings_near_route(
                route_id=route_detail['document_id'],
                buffer_meters=100,
                limit=10000
            )
            buildings_500m = await postgis_client.get_buildings_near_route(
                route_id=route_detail['document_id'],
                buffer_meters=500,
                limit=10000
            )
            route_detail['building_count_100m'] = len(buildings_100m)
            route_detail['building_count_500m'] = len(buildings_500m)
        except:
            route_detail['building_count_100m'] = None
            route_detail['building_count_500m'] = None
    
    # Get depot info
    route_detail['depots'] = attrs.get('depot') or attrs.get('depots')
    
    latency_ms = (time.time() - start_time) * 1000
    route_detail['latency_ms'] = round(latency_ms, 2)
    
    return route_detail
