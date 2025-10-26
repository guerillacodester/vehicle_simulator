"""
Geofencing API Endpoints
Check if coordinates are inside geofenced regions/zones
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import time

from services.postgis_client import postgis_client

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
        
        return GeofenceCheckResponse(
            latitude=request.latitude,
            longitude=request.longitude,
            inside_region=region is not None,
            region=region,
            inside_landuse=landuse is not None,
            landuse=landuse,
            latency_ms=round(latency_ms, 2)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geofence check failed: {str(e)}"
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
