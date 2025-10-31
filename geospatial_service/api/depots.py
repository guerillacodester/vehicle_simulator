"""
Depots API - Consolidated depot operations
All depot-related queries in one place (Single Responsibility Principle)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import configparser
from pathlib import Path
import httpx

from services.postgis_client import postgis_client

router = APIRouter(prefix="/depots", tags=["Depots"])

# Load Strapi URL from config
config = configparser.ConfigParser()
config_path = Path(__file__).parent.parent.parent / "config.ini"
config.read(config_path, encoding='utf-8')
STRAPI_URL = config.get('infrastructure', 'strapi_url', fallback='http://localhost:1337')


class DepotSummary(BaseModel):
    """Depot summary for listings"""
    depot_id: int
    document_id: Optional[str]
    name: str
    latitude: Optional[float]
    longitude: Optional[float]
    capacity: Optional[int]


class DepotDetail(BaseModel):
    """Detailed depot information"""
    depot_id: int
    document_id: Optional[str]
    name: str
    latitude: Optional[float]
    longitude: Optional[float]
    capacity: Optional[int]
    building_count_500m: Optional[int]
    building_count_1000m: Optional[int]
    routes: Optional[List[Dict[str, Any]]]


@router.get("/all", summary="List all depots")
async def list_all_depots(
    include_buildings: bool = Query(False, description="Include building counts (slower)"),
    include_routes: bool = Query(False, description="Include associated routes (slower)")
) -> Dict[str, Any]:
    """
    Get list of all depots in the system.
    
    Returns basic depot information by default.
    Use query params to include building counts and routes.
    """
    start_time = time.time()
    
    # Get depots from Strapi
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{STRAPI_URL}/api/depots",
                params={"pagination[pageSize]": 1000}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail=f"Strapi service unavailable. This endpoint requires Strapi CMS to be running."
                )
            
            data = response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Strapi CMS is not running. This endpoint requires Strapi to fetch depot data."
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
    
    depots = data.get('data', [])
    
    # Build depot list
    depot_list = []
    for depot in depots:
        depot_id = depot.get('id')
        if not depot_id:
            continue
        
        # Strapi v5 uses flat structure (no 'attributes' nesting)
        depot_info = {
            'depot_id': depot_id,
            'document_id': depot.get('documentId'),
            'name': depot.get('name'),
            'capacity': depot.get('capacity'),
            'latitude': depot.get('latitude'),
            'longitude': depot.get('longitude'),
        }
        
        # Include building counts if requested
        if include_buildings and depot_info['latitude'] and depot_info['longitude']:
            try:
                buildings_500m = await postgis_client.get_buildings_near_depot(
                    latitude=depot_info['latitude'],
                    longitude=depot_info['longitude'],
                    radius_meters=500,
                    limit=10000
                )
                buildings_1000m = await postgis_client.get_buildings_near_depot(
                    latitude=depot_info['latitude'],
                    longitude=depot_info['longitude'],
                    radius_meters=1000,
                    limit=10000
                )
                depot_info['building_count_500m'] = len(buildings_500m)
                depot_info['building_count_1000m'] = len(buildings_1000m)
            except:
                depot_info['building_count_500m'] = None
                depot_info['building_count_1000m'] = None
        
        # Include routes if requested
        if include_routes:
            try:
                routes_response = await client.get(
                    f"{STRAPI_URL}/api/routes",
                    params={
                        "filters[depot][id][$eq]": depot_id,
                        "pagination[pageSize]": 100
                    }
                )
                routes_data = routes_response.json()
                routes = routes_data.get('data', []) or []
                
                # Strapi v5 flat structure
                depot_info['routes'] = [
                    {
                        'route_id': r['id'],
                        'short_name': r.get('short_name'),
                        'long_name': r.get('long_name')
                    }
                    for r in routes
                ]
                depot_info['route_count'] = len(routes)
            except:
                depot_info['routes'] = []
                depot_info['route_count'] = 0
        
        depot_list.append(depot_info)
    
    latency_ms = (time.time() - start_time) * 1000
    
    return {
        'depots': depot_list,
        'count': len(depot_list),
        'includes': {
            'buildings': include_buildings,
            'routes': include_routes
        },
        'latency_ms': round(latency_ms, 2)
    }


@router.get("/{depot_id}/catchment", summary="Get depot catchment area buildings")
async def get_depot_catchment(
    depot_id: int,
    radius_meters: int = Query(1000, ge=100, le=5000, description="Catchment radius in meters"),
    limit: int = Query(5000, ge=1, le=10000, description="Maximum buildings to return")
) -> Dict[str, Any]:
    """
    Get all buildings within catchment area of depot.
    
    Essential for depot-based passenger spawning.
    """
    start_time = time.time()
    
    # Get depot location from Strapi
    # Strapi v5 requires filtering by ID, not direct ID in URL
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{STRAPI_URL}/api/depots",
            params={"filters[id][$eq]": depot_id}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="Strapi service unavailable")
        
        data = response.json()
        depots = data.get('data', [])
        
        if not depots:
            raise HTTPException(status_code=404, detail=f"Depot {depot_id} not found")
        
        depot_data = depots[0]
        
        # Strapi v5 flat structure
        latitude = depot_data.get('latitude')
        longitude = depot_data.get('longitude')
        depot_name = depot_data.get('name', 'Unknown')
        
        if not latitude or not longitude:
            raise HTTPException(status_code=400, detail="Depot has no location")
    
    # Query buildings
    try:
        buildings_data = await postgis_client.get_buildings_near_depot(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            limit=limit
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'depot': {
                'id': depot_id,
                'name': depot_name,
                'latitude': latitude,
                'longitude': longitude
            },
            'radius_meters': radius_meters,
            'buildings': buildings_data,
            'count': len(buildings_data),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Depot catchment query failed: {str(e)}")


@router.get("/{depot_id}/routes", summary="Get routes servicing depot")
async def get_depot_routes(depot_id: int) -> Dict[str, Any]:
    """
    Get all routes that service this depot.
    
    Shows which routes start/end at or pass through this depot.
    """
    start_time = time.time()
    
    # Get depot info
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Strapi v5 requires filtering by ID
        depot_response = await client.get(
            f"{STRAPI_URL}/api/depots",
            params={"filters[id][$eq]": depot_id}
        )
        
        if depot_response.status_code != 200:
            raise HTTPException(status_code=503, detail="Strapi service unavailable")
        
        depot_data = depot_response.json()
        depots = depot_data.get('data', [])
        
        if not depots:
            raise HTTPException(status_code=404, detail=f"Depot {depot_id} not found")
        
        depot_name = depots[0].get('name', 'Unknown')
        
        # Try both 'depot' and 'depots' relations
        routes_response = await client.get(
            f"{STRAPI_URL}/api/routes",
            params={
                "filters[depot][id][$eq]": depot_id,
                "populate": "*",
                "pagination[pageSize]": 100
            }
        )
        
        routes_data = routes_response.json()
        routes = routes_data.get('data', []) or []
        
        # If no routes found, try 'depots' plural
        if len(routes) == 0:
            routes_response = await client.get(
                f"{STRAPI_URL}/api/routes",
                params={
                    "filters[depots][id][$eq]": depot_id,
                    "populate": "*",
                    "pagination[pageSize]": 100
                }
            )
            routes_data = routes_response.json()
            routes = routes_data.get('data', []) or []
    
    # Build route list (Strapi v5 flat structure)
    route_list = []
    for route in routes:
        route_list.append({
            'route_id': route['id'],
            'document_id': route.get('documentId'),
            'short_name': route.get('short_name'),
            'long_name': route.get('long_name'),
            'distance_km': route.get('shape_dist_traveled')
        })
    
    latency_ms = (time.time() - start_time) * 1000
    
    return {
        'depot': {
            'id': depot_id,
            'name': depot_name
        },
        'routes': route_list,
        'count': len(route_list),
        'latency_ms': round(latency_ms, 2)
    }


@router.get("/{depot_id}/coverage", summary="Get depot coverage area")
async def get_depot_coverage(
    depot_id: int,
    radius_meters: int = Query(1000, ge=100, le=5000, description="Coverage radius in meters")
) -> Dict[str, Any]:
    """
    Get the service coverage area (circle polygon) for a depot.
    
    Returns GeoJSON polygon representing the area served by this depot.
    """
    start_time = time.time()
    
    # Get depot location
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Strapi v5 requires filtering by ID
        response = await client.get(
            f"{STRAPI_URL}/api/depots",
            params={"filters[id][$eq]": depot_id}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="Strapi service unavailable")
        
        data = response.json()
        depots = data.get('data', [])
        
        if not depots:
            raise HTTPException(status_code=404, detail=f"Depot {depot_id} not found")
        
        depot_data = depots[0]
        
        # Strapi v5 flat structure
        latitude = depot_data.get('latitude')
        longitude = depot_data.get('longitude')
        depot_name = depot_data.get('name', 'Unknown')
        
        if not latitude or not longitude:
            raise HTTPException(status_code=400, detail="Depot has no location")
    
    try:
        # Calculate coverage area using PostGIS
        query = """
            WITH depot_point AS (
                SELECT ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography AS geom
            )
            SELECT 
                ST_AsGeoJSON(ST_Buffer(geom, $3))::json AS coverage_polygon,
                ST_Area(ST_Buffer(geom, $3)) AS area_square_meters
            FROM depot_point
        """
        
        result = await postgis_client.execute_query(query, latitude, longitude, radius_meters)
        
        if not result:
            raise HTTPException(status_code=500, detail="Coverage calculation failed")
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'depot': {
                'id': depot_id,
                'name': depot_name,
                'latitude': latitude,
                'longitude': longitude
            },
            'radius_meters': radius_meters,
            'coverage_polygon': result[0]['coverage_polygon'],
            'area_square_meters': result[0]['area_square_meters'],
            'area_square_km': round(result[0]['area_square_meters'] / 1_000_000, 2),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Coverage calculation failed: {str(e)}")


@router.post("/nearest", summary="Find nearest depot to point")
async def find_nearest_depot(
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Find the nearest depot to a given point.
    
    Request body: {"latitude": 13.1, "longitude": -59.6, "max_distance_meters": 10000}
    
    Useful for determining which depot services a location.
    """
    start_time = time.time()
    
    latitude = request_data.get('latitude')
    longitude = request_data.get('longitude')
    max_distance_meters = request_data.get('max_distance_meters', 10000)
    
    if latitude is None or longitude is None:
        raise HTTPException(status_code=400, detail="latitude and longitude are required")
    if not (-90 <= latitude <= 90):
        raise HTTPException(status_code=400, detail="latitude must be between -90 and 90")
    if not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="longitude must be between -180 and 180")
    
    # Get all depots from Strapi
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{STRAPI_URL}/api/depots",
                params={"pagination[pageSize]": 1000}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=503, 
                    detail=f"Strapi service unavailable or returned {response.status_code}. This endpoint requires Strapi CMS to be running."
                )
            
            data = response.json()
            depots = data.get('data', [])
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Strapi CMS is not running. This endpoint requires Strapi to fetch depot data."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Strapi CMS request timed out. Please check if Strapi is running properly."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Strapi CMS: {str(e)}"
        )
    
    # Calculate distances
    from math import radians, sin, cos, sqrt, atan2
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth radius in meters
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    nearest_depot = None
    min_distance = float('inf')
    
    if not depots:
        return {
            'found': False,
            'message': 'No depots available in the system',
            'query_point': {
                'latitude': latitude,
                'longitude': longitude
            },
            'latency_ms': round((time.time() - start_time) * 1000, 2)
        }
    
    for depot in depots:
        # Strapi v5 flat structure
        latitude_depot = depot.get('latitude')
        longitude_depot = depot.get('longitude')
        
        if not latitude_depot or not longitude_depot:
            continue
        
        distance = haversine_distance(latitude, longitude, latitude_depot, longitude_depot)
        
        if distance < min_distance and distance <= max_distance_meters:
            min_distance = distance
            nearest_depot = {
                'depot_id': depot['id'],
                'document_id': depot.get('documentId'),
                'name': depot.get('name'),
                'latitude': latitude_depot,
                'longitude': longitude_depot,
                'distance_meters': round(distance, 2)
            }
    
    latency_ms = (time.time() - start_time) * 1000
    
    if nearest_depot:
        return {
            'found': True,
            'depot': nearest_depot,
            'query_point': {
                'latitude': latitude,
                'longitude': longitude
            },
            'latency_ms': round(latency_ms, 2)
        }
    else:
        return {
            'found': False,
            'message': f'No depots within {max_distance_meters}m',
            'query_point': {
                'latitude': latitude,
                'longitude': longitude
            },
            'max_distance_meters': max_distance_meters,
            'latency_ms': round(latency_ms, 2)
        }


@router.get("/{depot_id}", summary="Get detailed depot information")
async def get_depot_detail(
    depot_id: int,
    include_buildings: bool = Query(True, description="Include building counts"),
    include_routes: bool = Query(True, description="Include associated routes")
) -> Dict[str, Any]:
    """
    Get comprehensive depot details.
    
    Single endpoint for all depot information.
    """
    start_time = time.time()
    
    # Get from Strapi
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Strapi v5 requires filtering by ID
        response = await client.get(
            f"{STRAPI_URL}/api/depots",
            params={"filters[id][$eq]": depot_id}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="Strapi service unavailable")
        
        data = response.json()
        depots = data.get('data', [])
        
        if not depots:
            raise HTTPException(status_code=404, detail=f"Depot {depot_id} not found")
        
        depot_data = depots[0]
    
    # Strapi v5 flat structure
    depot_detail = {
        'depot_id': depot_id,
        'document_id': depot_data.get('documentId'),
        'name': depot_data.get('name'),
        'capacity': depot_data.get('capacity'),
        'latitude': depot_data.get('latitude'),
        'longitude': depot_data.get('longitude'),
    }
    
    if depot_detail['latitude'] and depot_detail['longitude']:
        # Include building counts if requested
        if include_buildings:
            try:
                buildings_500m = await postgis_client.get_buildings_near_depot(
                    latitude=depot_detail['latitude'],
                    longitude=depot_detail['longitude'],
                    radius_meters=500,
                    limit=10000
                )
                buildings_1000m = await postgis_client.get_buildings_near_depot(
                    latitude=depot_detail['latitude'],
                    longitude=depot_detail['longitude'],
                    radius_meters=1000,
                    limit=10000
                )
                depot_detail['building_count_500m'] = len(buildings_500m)
                depot_detail['building_count_1000m'] = len(buildings_1000m)
            except:
                depot_detail['building_count_500m'] = None
                depot_detail['building_count_1000m'] = None
    
    # Include routes if requested
    if include_routes:
        route_info = await get_depot_routes(depot_id)
        depot_detail['routes'] = route_info['routes']
        depot_detail['route_count'] = route_info['count']
    
    latency_ms = (time.time() - start_time) * 1000
    depot_detail['latency_ms'] = round(latency_ms, 2)
    
    return depot_detail
