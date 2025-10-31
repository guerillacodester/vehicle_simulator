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


@router.get("/reverse", response_model=ReverseGeocodeResponse)
async def reverse_geocode_get(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    highway_radius_meters: int = Query(500, ge=50, le=5000),
    poi_radius_meters: int = Query(1000, ge=50, le=10000)
):
    """
    Convert latitude/longitude to human-readable address (GET version).
    
    Uses PostGIS spatial queries to find nearest highway and POI.
    """
    request = ReverseGeocodeRequest(
        latitude=lat,
        longitude=lon,
        highway_radius_meters=highway_radius_meters,
        poi_radius_meters=poi_radius_meters
    )
    return await reverse_geocode_post(request)


@router.post("/reverse", response_model=ReverseGeocodeResponse)
async def reverse_geocode_post(request: ReverseGeocodeRequest):
    """
    Convert latitude/longitude to human-readable address
    
    Uses PostGIS spatial queries to find:
    1. Nearest highway within radius (default 500m)
    2. Nearest POI within radius (default 1000m)
    
    Returns formatted address based on available data.
    
    Performance target: <50ms
    """
    start_time = time.time()

    # Simple in-memory cache to speed repeated identical requests (TTL: 5s)
    if not hasattr(reverse_geocode_post, "_cache"):
        reverse_geocode_post._cache = {}
    cache_key = (round(request.latitude, 6), round(request.longitude, 6), request.highway_radius_meters, request.poi_radius_meters)
    cached = reverse_geocode_post._cache.get(cache_key)
    if cached and (time.time() - cached[0]) < 5.0:
        # return cached response quickly
        cached_response = cached[1]
        cached_response.latency_ms = round((time.time() - start_time) * 1000, 2)
        return cached_response
    
    try:
        # Query nearest highway, POI, and parish in parallel
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
        
        region = await postgis_client.check_geofence_region(
            request.latitude,
            request.longitude
        )
        
        # Format address: build best human-readable location from available data
        address_parts = []
        
        # Add highway/road info
        if highway:
            hw_name = highway.get('name')
            hw_type = highway.get('highway_type', 'road')
            hw_dist = highway.get('distance_meters', 0)
            
            if hw_name and hw_name.strip() and hw_name not in ['unnamed', 'Unknown']:
                address_parts.append(hw_name)
            elif hw_dist < 100:  # Very close unnamed road
                address_parts.append(f"{hw_type.title()} road")
        
        # Add POI info
        if poi:
            poi_name = poi.get('name')
            poi_type = poi.get('poi_type') or poi.get('amenity', 'location')
            poi_dist = poi.get('distance_meters', 0)
            
            if poi_name and poi_name.strip() and poi_name not in ['unnamed', 'Unknown']:
                if address_parts:
                    address_parts.append(f"near {poi_name}")
                else:
                    address_parts.append(f"Near {poi_name}")
            elif poi_dist < 200 and poi_type:  # Close unnamed POI
                if address_parts:
                    address_parts.append(f"near {poi_type}")
                else:
                    address_parts.append(f"Near {poi_type}")
        
        # Add parish/region
        if region:
            parish_name = region.get('name')
            if parish_name:
                address_parts.append(parish_name)
        
        # Build final address or fallback
        if address_parts:
            address = ", ".join(address_parts)
        else:
            # Last resort: just report approximate distance to nearest feature
            if highway:
                dist = int(highway.get('distance_meters', 0))
                address = f"Approximately {dist}m from nearest road"
            elif poi:
                dist = int(poi.get('distance_meters', 0))
                address = f"Approximately {dist}m from nearest location"
            else:
                address = f"Lat: {request.latitude:.4f}, Lon: {request.longitude:.4f}"
        
        latency_ms = (time.time() - start_time) * 1000
        response = ReverseGeocodeResponse(
            address=address,
            latitude=request.latitude,
            longitude=request.longitude,
            highway=highway,
            poi=poi,
            source="computed",
            latency_ms=round(latency_ms, 2)
        )

        # store in cache
        try:
            reverse_geocode_post._cache[cache_key] = (time.time(), response)
        except Exception:
            pass

        return response
    
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


@router.post("/batch")
async def batch_reverse_geocode(request_data: dict):
    """
    Batch reverse geocode multiple locations.
    
    Request body: {"locations": [{"lat": 13.1, "lon": -59.6}, ...]}
    """
    locations = request_data.get('locations', [])
    
    if not locations:
        raise HTTPException(status_code=400, detail="No locations provided")
    
    results = []
    for loc in locations:
        lat = loc.get('lat')
        lon = loc.get('lon')
        
        if lat is None or lon is None:
            results.append({'error': 'Missing lat or lon'})
            continue
        
        try:
            req = ReverseGeocodeRequest(latitude=lat, longitude=lon)
            result = await reverse_geocode(req)
            results.append(result.dict())
        except Exception as e:
            results.append({'error': str(e), 'lat': lat, 'lon': lon})
    
    return {'results': results, 'count': len(results)}

