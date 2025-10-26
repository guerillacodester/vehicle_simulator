"""
Reverse Geocoding API Endpoints
Convert lat/lon coordinates to human-readable addresses
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import time

from services.postgis_client import postgis_client

router = APIRouter(prefix="/geocode", tags=["Reverse Geocoding"])


class ReverseGeocodeRequest(BaseModel):
    """Request model for reverse geocoding"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    highway_radius_meters: int = Field(500, ge=50, le=5000, description="Search radius for highways")
    poi_radius_meters: int = Field(1000, ge=50, le=10000, description="Search radius for POIs")


class ReverseGeocodeResponse(BaseModel):
    """Response model for reverse geocoding"""
    address: str
    latitude: float
    longitude: float
    highway: Optional[dict] = None
    poi: Optional[dict] = None
    source: str
    latency_ms: float


@router.post("/reverse", response_model=ReverseGeocodeResponse)
async def reverse_geocode(request: ReverseGeocodeRequest):
    """
    Convert latitude/longitude to human-readable address
    
    Uses PostGIS spatial queries to find:
    1. Nearest highway within radius (default 500m)
    2. Nearest POI within radius (default 1000m)
    
    Returns formatted address based on available data.
    
    Performance target: <50ms
    """
    start_time = time.time()
    
    try:
        # Query nearest highway and POI in parallel
        highway = await postgis_client.find_nearest_highway(
            request.latitude, 
            request.longitude, 
            request.highway_radius_meters
        )
        
        poi = await postgis_client.find_nearest_poi(
            request.latitude, 
            request.longitude, 
            request.poi_radius_meters
        )
        
        # Format address based on available data
        if highway and poi:
            address = f"{highway['name']}, near {poi['name']}"
        elif highway:
            highway_type = highway.get('highway_type', 'road')
            name = highway.get('name', f'{highway_type.title()} road')
            address = name
        elif poi:
            address = f"Near {poi['name']}"
        else:
            address = "Unknown location"
        
        latency_ms = (time.time() - start_time) * 1000
        
        return ReverseGeocodeResponse(
            address=address,
            latitude=request.latitude,
            longitude=request.longitude,
            highway=highway,
            poi=poi,
            source="computed",
            latency_ms=round(latency_ms, 2)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reverse geocoding failed: {str(e)}"
        )


@router.get("/reverse", response_model=ReverseGeocodeResponse)
async def reverse_geocode_get(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    highway_radius: int = Query(500, ge=50, le=5000, description="Highway search radius (meters)"),
    poi_radius: int = Query(1000, ge=50, le=10000, description="POI search radius (meters)")
):
    """
    GET version of reverse geocode endpoint
    Useful for quick browser testing
    """
    request = ReverseGeocodeRequest(
        latitude=lat,
        longitude=lon,
        highway_radius_meters=highway_radius,
        poi_radius_meters=poi_radius
    )
    
    return await reverse_geocode(request)
