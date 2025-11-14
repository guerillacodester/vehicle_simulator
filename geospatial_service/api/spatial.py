"""
Spatial Query API Endpoints
Buildings, POIs, and routes for passenger spawning
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Tuple
import time
import httpx
import configparser
from pathlib import Path

from ..services.postgis_client import postgis_client

# Load config
config = configparser.ConfigParser()
config_path = Path(__file__).parent.parent / 'config' / 'config.ini'
config.read(config_path)

STRAPI_URL = config.get('infrastructure', 'strapi_url', fallback='http://localhost:1337')

router = APIRouter(prefix="/spatial", tags=["Spatial Queries"])


class RouteGeometry(BaseModel):
    """Route geometry with calculated metrics"""
    route_id: str
    short_name: str
    long_name: str
    coordinates: List[List[float]]  # [[lon, lat], [lon, lat], ...]
    num_segments: int
    num_points: int
    total_distance_meters: float
    latency_ms: float


@router.get("/route-geometry/{route_id}", response_model=RouteGeometry)
async def get_route_geometry(route_id: str):
    """
    Get complete route geometry with all segments concatenated.
    
    **SINGLE SOURCE OF TRUTH** for route geometry calculations.
    All services must use this endpoint instead of calculating locally.
    
    Returns:
    - Full route coordinates (all segments concatenated)
    - Total distance in meters (from segment cost fields)
    - Number of segments and points
    
    Performance target: <50ms
    """
    start_time = time.time()
    
    try:
        route_data = await postgis_client.get_route_geometry(route_id)
        
        if not route_data:
            raise HTTPException(
                status_code=404,
                detail=f"Route not found: {route_id}"
            )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return RouteGeometry(
            route_id=route_data['route_id'],
            short_name=route_data['short_name'],
            long_name=route_data['long_name'],
            coordinates=route_data['coordinates'],
            num_segments=route_data['num_segments'],
            num_points=route_data['num_points'],
            total_distance_meters=route_data['total_distance_meters'],
            latency_ms=round(latency_ms, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Route geometry query failed: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ ROUTE GEOMETRY ERROR: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


class RouteBuilding(BaseModel):
    """Building near a route"""
    building_id: int
    document_id: str
    latitude: float
    longitude: float
    distance_meters: float


class RouteBuildingsRequest(BaseModel):
    """Request model for route buildings query"""
    route_id: str = Field(..., description="Route document_id from highways table")
    buffer_meters: int = Field(500, ge=50, le=5000, description="Buffer distance around route")
    limit: int = Field(1000, ge=1, le=10000, description="Maximum buildings to return")


class RouteBuildingsResponse(BaseModel):
    """Response model for route buildings query"""
    route_id: str
    buffer_meters: int
    buildings: List[RouteBuilding]
    count: int
    latency_ms: float


@router.post("/route-buildings", response_model=RouteBuildingsResponse)
async def get_route_buildings(request: RouteBuildingsRequest):
    """
    Get all buildings within buffer distance of a route (highway)
    
    Uses PostGIS ST_DWithin to find buildings near transit routes.
    Essential for route-based passenger spawning.
    
    Performance target: <100ms for 500m buffer
    """
    start_time = time.time()
    
    try:
        buildings_data = await postgis_client.get_buildings_near_route(
            request.route_id,
            request.buffer_meters,
            request.limit
        )
        
        buildings = [RouteBuilding(**b) for b in buildings_data]
        
        latency_ms = (time.time() - start_time) * 1000
        
        return RouteBuildingsResponse(
            route_id=request.route_id,
            buffer_meters=request.buffer_meters,
            buildings=buildings,
            count=len(buildings),
            latency_ms=round(latency_ms, 2)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Route buildings query failed: {str(e)}"
        )


class DepotBuilding(BaseModel):
    """Building near a depot"""
    building_id: int
    document_id: str
    latitude: float
    longitude: float
    distance_meters: float


class DepotCatchmentRequest(BaseModel):
    """Request model for depot catchment query"""
    latitude: float = Field(..., ge=-90, le=90, description="Depot latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Depot longitude")
    radius_meters: int = Field(1000, ge=50, le=10000, description="Catchment radius")
    limit: int = Field(5000, ge=1, le=50000, description="Maximum buildings to return")


class DepotCatchmentResponse(BaseModel):
    """Response model for depot catchment query"""
    latitude: float
    longitude: float
    radius_meters: int
    buildings: List[DepotBuilding]
    count: int
    latency_ms: float


@router.post("/depot-catchment", response_model=DepotCatchmentResponse)
async def get_depot_catchment(request: DepotCatchmentRequest):
    """
    Get all buildings within radius of a depot point
    
    Uses PostGIS ST_DWithin to find buildings in depot catchment area.
    Essential for depot-based passenger spawning.
    
    Performance target: <150ms for 1000m radius
    """
    start_time = time.time()
    start_time = time.time()

    # Simple in-memory cache to accelerate repeated identical depot queries (TTL: 5s)
    if not hasattr(get_depot_catchment, "_cache"):
        get_depot_catchment._cache = {}
    cache_key = (round(request.latitude, 6), round(request.longitude, 6), request.radius_meters, request.limit)
    cached = get_depot_catchment._cache.get(cache_key)
    if cached and (time.time() - cached[0]) < 5.0:
        resp = cached[1]
        resp.latency_ms = round((time.time() - start_time) * 1000, 2)
        return resp

    try:
        buildings_data = await postgis_client.get_buildings_near_depot(
            request.latitude,
            request.longitude,
            request.radius_meters,
            request.limit
        )
        
        buildings = [DepotBuilding(**b) for b in buildings_data]
        
        latency_ms = (time.time() - start_time) * 1000
        
        response = DepotCatchmentResponse(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters,
            buildings=buildings,
            count=len(buildings),
            latency_ms=round(latency_ms, 2)
        )

        try:
            get_depot_catchment._cache[cache_key] = (time.time(), response)
        except Exception:
            pass

        return response
    
    except Exception as e:
        import traceback
        error_detail = f"Depot catchment query failed: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ ERROR: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


@router.get("/depot-catchment", response_model=DepotCatchmentResponse)
async def get_depot_catchment_get(
    lat: float = Query(..., ge=-90, le=90, description="Depot latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Depot longitude"),
    radius: int = Query(1000, ge=50, le=10000, description="Catchment radius (meters)"),
    limit: int = Query(5000, ge=1, le=50000, description="Maximum buildings")
):
    """
    GET version of depot catchment endpoint
    Useful for quick browser testing
    """
    request = DepotCatchmentRequest(
        latitude=lat,
        longitude=lon,
        radius_meters=radius,
        limit=limit
    )
    
    return await get_depot_catchment(request)


# Alias endpoint for generic "nearby buildings" queries
@router.get("/nearby-buildings", response_model=DepotCatchmentResponse)
async def get_nearby_buildings(
    lat: float = Query(..., ge=-90, le=90, description="Center latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Center longitude"),
    radius_meters: int = Query(500, ge=50, le=10000, description="Search radius (meters)"),
    limit: int = Query(5000, ge=1, le=10000, description="Maximum buildings")
):
    """
    Find buildings near a point (generic proximity search)
    
    This is an alias for depot-catchment but with different defaults
    optimized for general proximity queries rather than depot spawning.
    
    Performance target: <100ms for 500m radius
    """
    request = DepotCatchmentRequest(
        latitude=lat,
        longitude=lon,
        radius_meters=radius_meters,
        limit=limit
    )
    
    return await get_depot_catchment(request)


@router.get("/buildings/nearest")
async def get_nearest_buildings(
    latitude: float = Query(..., ge=-90, le=90, description="Center latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Center longitude"),
    radius_meters: int = Query(500, ge=50, le=10000, description="Search radius (meters)"),
    limit: int = Query(5000, ge=1, le=10000, description="Maximum buildings")
):
    """
    Find nearest buildings to a point.
    Legacy endpoint for compatibility.
    """
    request = DepotCatchmentRequest(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        limit=limit
    )
    
    return await get_depot_catchment(request)


@router.get("/pois/nearest")
async def get_nearest_pois(
    latitude: float = Query(..., ge=-90, le=90, description="Center latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Center longitude"),
    radius_meters: int = Query(1000, ge=50, le=10000, description="Search radius (meters)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum POIs")
):
    """
    Find nearest POIs (Points of Interest) to a location.
    """
    start_time = time.time()
    
    try:
        query = """
            SELECT 
                id,
                document_id,
                name,
                amenity,
                ST_Y(geom) AS latitude,
                ST_X(geom) AS longitude,
                ST_Distance(
                    ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                    geom::geography
                ) AS distance_meters
            FROM pois
            WHERE ST_DWithin(
                ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                geom::geography,
                $3
            )
            ORDER BY distance_meters ASC
            LIMIT $4
        """
        
        pois_data = await postgis_client.execute_query(
            query, latitude, longitude, radius_meters, limit
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'query_point': {
                'latitude': latitude,
                'longitude': longitude
            },
            'radius_meters': radius_meters,
            'pois': pois_data,
            'count': len(pois_data),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POIs query failed: {str(e)}")


class RouteSegmentDistance(BaseModel):
    """Distance calculation between two points on a route"""
    from_index: int
    to_index: int
    distance_meters: float
    distance_km: float
    latency_ms: float


@router.get("/route-segment-distance/{route_id}", response_model=RouteSegmentDistance)
async def calculate_route_segment_distance(
    route_id: str,
    from_index: int = Query(..., ge=0, description="Starting coordinate index"),
    to_index: int = Query(..., ge=0, description="Ending coordinate index")
):
    """
    Calculate distance between two points on a route by coordinate index.
    
    **SINGLE SOURCE OF TRUTH** for route segment distance calculations.
    
    This computes the actual distance traveled along the route between two stops,
    not the straight-line distance.
    
    Args:
        route_id: Route document ID
        from_index: Starting coordinate index (0-based)
        to_index: Ending coordinate index (0-based)
    
    Returns:
        Distance in meters and kilometers
    
    Example:
        /spatial/route-segment-distance/gg3pv3z19hhm117v9xth5ezq?from_index=0&to_index=5
    """
    start_time = time.time()
    
    try:
        # Get route geometry
        route_data = await postgis_client.get_route_geometry(route_id)
        
        if not route_data:
            raise HTTPException(
                status_code=404,
                detail=f"Route {route_id} not found"
            )
        
        coordinates = route_data['coordinates']
        
        # Validate indices
        if from_index >= len(coordinates) or to_index >= len(coordinates):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid indices. Route has {len(coordinates)} coordinates (0-{len(coordinates)-1})"
            )
        
        if from_index == to_index:
            raise HTTPException(
                status_code=400,
                detail="from_index and to_index must be different"
            )
        
        # Calculate distance along route segments
        distance_meters = 0.0
        start_idx = min(from_index, to_index)
        end_idx = max(from_index, to_index)
        
        for i in range(start_idx, end_idx):
            lon1, lat1 = coordinates[i]
            lon2, lat2 = coordinates[i + 1]
            
            # Use PostGIS to calculate great circle distance
            query = """
                SELECT ST_Distance(
                    ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
                    ST_SetSRID(ST_MakePoint($3, $4), 4326)::geography
                ) AS distance_meters
            """
            
            result = await postgis_client.execute_query(query, lon1, lat1, lon2, lat2)
            if result:
                distance_meters += result[0]['distance_meters']
        
        latency_ms = (time.time() - start_time) * 1000
        
        return RouteSegmentDistance(
            from_index=from_index,
            to_index=to_index,
            distance_meters=round(distance_meters, 2),
            distance_km=round(distance_meters / 1000, 2),
            latency_ms=round(latency_ms, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Distance calculation failed: {str(e)}"
        )


class MinimumCommuteDistance(BaseModel):
    """Minimum commute distance configuration"""
    min_distance_meters: int
    min_distance_km: float
    min_stops: int
    description: str


@router.get("/minimum-commute-distance", response_model=MinimumCommuteDistance)
async def get_minimum_commute_distance():
    """
    Get minimum realistic commute distance for passenger spawning.
    
    **SINGLE SOURCE OF TRUTH** for minimum commute distance policy.
    
    Reads from operational-configurations database:
    - passenger_spawning.geographic.minimum_commute_distance_meters
    
    Returns:
        Minimum distance that passengers should travel (greater than walking distance)
    
    Business rule: Passengers should travel far enough that taking the bus makes sense
    compared to walking. Distances below this threshold are considered walking distance.
    """
    # Fetch from operational-configurations in Strapi
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{STRAPI_URL}/api/operational-configurations",
                params={
                    "filters[section][$eq]": "passenger_spawning.geographic",
                    "filters[parameter][$eq]": "minimum_commute_distance_meters",
                    "pagination[pageSize]": 1
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to Strapi database: {str(e)}"
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Strapi returned error: {response.text}"
            )
        
        data = response.json()
        configs = data.get('data', [])
        
        if not configs or len(configs) == 0:
            raise HTTPException(
                status_code=500,
                detail="Configuration 'minimum_commute_distance_meters' not found in database. Run seed script: python arknet_fleet_manager/seed_operational_config.py"
            )
        
        config = configs[0]
        min_distance_meters = int(float(config.get('value')))
        
        return MinimumCommuteDistance(
            min_distance_meters=min_distance_meters,
            min_distance_km=round(min_distance_meters / 1000, 2),
            min_stops=max(1, min_distance_meters // 200),  # Approximate stops (200m per stop)
            description=config.get('description', 'Minimum distance to make bus travel worthwhile vs walking')
        )

