"""
Geofencing API Endpoints
Check if coordinates are inside geofenced regions/zones
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import time

from ..services.postgis_client import postgis_client

router = APIRouter(prefix="/geofence", tags=["Geofencing"])


class GeofenceCheckRequest(BaseModel):
    """Request model for geofence check"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")


class GeofenceCheckResponse(BaseModel):
    """Response model for geofence check"""
    latitude: float
    longitude: float
    inside_region: bool
    region: Optional[dict] = None
    inside_landuse: bool
    landuse: Optional[dict] = None
    latency_ms: float


@router.post("/check", response_model=GeofenceCheckResponse)
async def check_geofence(request: GeofenceCheckRequest):
    """
    Check if coordinate is inside any geofenced region or landuse zone
    
    Uses PostGIS ST_Contains to check:
    1. Administrative regions (parish, town, suburb, neighbourhood)
    2. Landuse zones (farmland, residential, industrial, etc.)
    
    Returns which zones contain the point.
    
    Performance target: <30ms
    """
    start_time = time.time()

    # In-memory cache for repeated geofence checks (TTL: 5s)
    if not hasattr(check_geofence, "_cache"):
        check_geofence._cache = {}
    cache_key = (round(request.latitude, 6), round(request.longitude, 6))
    cached = check_geofence._cache.get(cache_key)
    if cached and (time.time() - cached[0]) < 5.0:
        resp = cached[1]
        resp.latency_ms = round((time.time() - start_time) * 1000, 2)
        return resp

    try:
        # Check both region and landuse in parallel
        region = await postgis_client.check_geofence_region(
            request.latitude, 
            request.longitude
        )
        
        landuse = await postgis_client.check_geofence_landuse(
            request.latitude, 
            request.longitude
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        response = GeofenceCheckResponse(
            latitude=request.latitude,
            longitude=request.longitude,
            inside_region=region is not None,
            region=region,
            inside_landuse=landuse is not None,
            landuse=landuse,
            latency_ms=round(latency_ms, 2)
        )

        try:
            check_geofence._cache[cache_key] = (time.time(), response)
        except Exception:
            pass

        return response
    
    except Exception as e:
        import traceback
        error_detail = f"Geofence check failed: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ ERROR: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


class BatchGeofenceRequest(BaseModel):
    """Request model for batch geofence checks"""
    coordinates: List[GeofenceCheckRequest] = Field(
        ..., 
        max_items=100,
        description="List of coordinates to check (max 100)"
    )


class BatchGeofenceResponse(BaseModel):
    """Response model for batch geofence checks"""
    results: List[GeofenceCheckResponse]
    total_count: int
    latency_ms: float


@router.post("/check-batch", response_model=BatchGeofenceResponse)
async def check_geofence_batch(request: BatchGeofenceRequest):
    """
    Batch geofence checking for multiple coordinates
    
    Useful for processing multiple vehicle positions efficiently.
    Maximum 100 coordinates per request.
    
    Performance target: <200ms for 100 coordinates
    """
    start_time = time.time()
    
    try:
        results = []
        
        for coord in request.coordinates:
            result = await check_geofence(coord)
            results.append(result)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return BatchGeofenceResponse(
            results=results,
            total_count=len(results),
            latency_ms=round(latency_ms, 2)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch geofence check failed: {str(e)}"
        )


@router.post("/batch")
async def batch_geofence_check(request_data: dict):
    """
    Simplified batch geofence endpoint.
    
    Request body: {"points": [{"lat": 13.1, "lon": -59.6}, ...], "polygon": [[lat, lon], ...]}
    
    Checks if points are inside the provided polygon.
    """
    points = request_data.get('points', [])
    polygon = request_data.get('polygon', [])
    
    if not points:
        raise HTTPException(status_code=400, detail="No points provided")
    if not polygon or len(polygon) < 3:
        raise HTTPException(status_code=400, detail="Invalid polygon (need at least 3 coordinates)")
    
    start_time = time.time()
    
    try:
        from shapely.geometry import Point, Polygon
        
        poly = Polygon(polygon)
        results = []
        
        for point in points:
            lat = point.get('lat')
            lon = point.get('lon')
            
            if lat is None or lon is None:
                results.append({'error': 'Missing lat or lon'})
                continue
            
            pt = Point(lon, lat)  # Note: Shapely uses (lon, lat) order
            inside = poly.contains(pt)
            
            results.append({
                'latitude': lat,
                'longitude': lon,
                'inside': inside
            })
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'results': results,
            'total_count': len(results),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch geofence failed: {str(e)}")

