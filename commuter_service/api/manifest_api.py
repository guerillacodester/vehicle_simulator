"""
DEPRECATED: Commuter Manifest API (Old Location)
-------------------------------------------------

⚠️ This file is deprecated. Use the new location instead:
   commuter_service.interfaces.http.commuter_manifest

FastAPI service providing enriched passenger manifests for UI consumption.

Usage (DEPRECATED):
    uvicorn commuter_service.api.manifest_api:app --host 0.0.0.0 --port 4000

New Usage:
    uvicorn commuter_service.interfaces.http.commuter_manifest:app --host 0.0.0.0 --port 4000

Endpoints:
    GET /api/manifest - Query passenger manifest with filters
    GET /health - Health check
"""
from __future__ import annotations

import os
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx

from commuter_service.services.manifest_builder import (
    enrich_manifest_rows,
    fetch_passengers,
    ManifestRow
)

app = FastAPI(
    title="Passenger Manifest API",
    description="Enriched passenger manifest with route positions and geocoded addresses",
    version="1.0.0"
)

# CORS for UI consumption
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ManifestResponse(BaseModel):
    """Response model for manifest endpoint"""
    count: int = Field(..., description="Number of passengers returned")
    route_id: Optional[str] = Field(None, description="Route filter applied")
    depot_id: Optional[str] = Field(None, description="Depot filter applied")
    passengers: List[dict] = Field(..., description="Enriched passenger data")
    ordered_by_route_position: bool = Field(..., description="Whether sorted by route position")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "deprecated",
        "service": "commuter_manifest_old",
        "message": "Use commuter_service.interfaces.http.commuter_manifest instead",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/manifest", response_model=ManifestResponse)
async def get_manifest(
    route: Optional[str] = Query(None, description="Filter by route_id"),
    depot: Optional[str] = Query(None, description="Filter by depot_id"),
    status: Optional[str] = Query(None, description="Filter by status (e.g., WAITING, BOARDED)"),
    start: Optional[str] = Query(None, description="Filter spawned_at >= ISO8601 timestamp"),
    end: Optional[str] = Query(None, description="Filter spawned_at <= ISO8601 timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max passengers to return"),
    sort: str = Query("spawned_at:asc", description="Sort order (default: spawned_at:asc)")
):
    """
    Get enriched passenger manifest with route positions and geocoded addresses.
    
    When a route_id is provided, passengers are ordered by distance from route start.
    Includes reverse geocoded start/stop addresses and travel distance.
    
    Returns enriched ManifestRow data with:
    - index (position in sorted list)
    - route_position_m (distance from route start)
    - travel_distance_km
    - start_address, stop_address (reverse geocoded)
    - trip_summary ("Start → Stop | km")
    """
    strapi_url = os.getenv("STRAPI_URL", "http://localhost:1337").rstrip("/")
    token = os.getenv("STRAPI_TOKEN")
    
    # Build Strapi query params
    params = {
        "pagination[pageSize]": limit,
        "sort": sort,
    }
    if route:
        params["filters[route_id][$eq]"] = route
    if depot:
        params["filters[depot_id][$eq]"] = depot
    if start:
        params["filters[spawned_at][$gte]"] = start
    if end:
        params["filters[spawned_at][$lte]"] = end
    if status:
        params["filters[status][$eq]"] = status
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch raw passengers from Strapi
            rows = await fetch_passengers(client, strapi_url, token, params)
            
            # Enrich with positions, addresses, distances
            enriched = await enrich_manifest_rows(rows, route)
            
            # Convert to JSON-serializable dict
            passengers_data = [row.to_json() for row in enriched]
            
            return ManifestResponse(
                count=len(passengers_data),
                route_id=route,
                depot_id=depot,
                passengers=passengers_data,
                ordered_by_route_position=bool(route)
            )
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch passengers from Strapi: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Manifest enrichment failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
