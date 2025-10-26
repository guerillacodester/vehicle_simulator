"""
Spatial Query API Endpoints
Buildings, POIs, and routes for passenger spawning
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List
import time

from services.postgis_client import postgis_client

router = APIRouter(prefix="/spatial", tags=["Spatial Queries"])


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
