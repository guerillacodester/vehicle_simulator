"""
Manifest API
------------

FastAPI service providing enriched passenger manifests for UI consumption.

Wraps the manifest_query to provide HTTP access to ordered, geocoded passenger data.

Usage:
    uvicorn commuter_simulator.interfaces.http.manifest_api:app --host 0.0.0.0 --port 4000

Endpoints:
    GET /api/manifest - Query passenger manifest with filters
    GET /api/manifest/visualization/barchart - Get barchart data
    GET /api/manifest/visualization/table - Get table data with geocoding
    GET /api/manifest/stats - Get summary statistics
    DELETE /api/manifest - Delete passengers by filters
    GET /health - Health check
"""
from __future__ import annotations

import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx

from commuter_simulator.application.queries import (
    enrich_manifest_rows,
    fetch_passengers,
    ManifestRow
)
from commuter_simulator.application.queries.manifest_visualization import (
    fetch_passengers_from_strapi,
    generate_barchart_data,
    enrich_passengers_with_geocoding,
    calculate_route_metrics
)
from commuter_simulator.infrastructure.config import get_config

try:
    from common.config_provider import get_config
    _config_available = True
except ImportError:
    _config_available = False

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


class BarchartResponse(BaseModel):
    """Response model for barchart visualization"""
    hourly_counts: List[int] = Field(..., description="Passenger count per hour (0-23)")
    total: int = Field(..., description="Total passengers")
    max_count: int = Field(..., description="Maximum count in any hour")
    peak_hour: int = Field(..., description="Hour with most passengers (0-23)")
    route_passengers: int = Field(..., description="Count of route passengers")
    depot_passengers: int = Field(..., description="Count of depot passengers")
    date: str = Field(..., description="Target date (YYYY-MM-DD)")
    route_name: Optional[str] = Field(None, description="Route name if filtered")


class RouteMetricsResponse(BaseModel):
    """Response model for route metrics"""
    total_passengers: int = Field(..., description="Total passengers")
    route_passengers: int = Field(..., description="Route passengers")
    depot_passengers: int = Field(..., description="Depot passengers")
    avg_commute_distance: float = Field(..., description="Average commute distance in km")
    avg_depot_distance: float = Field(..., description="Average distance from depot in km")
    total_route_distance: Optional[float] = Field(None, description="Total route distance in km")
    date: str = Field(..., description="Target date (YYYY-MM-DD)")
    route_name: Optional[str] = Field(None, description="Route name if filtered")


class TableResponse(BaseModel):
    """Response model for table visualization"""
    passengers: List[dict] = Field(..., description="Enriched passenger data with addresses and distances")
    metrics: RouteMetricsResponse = Field(..., description="Summary metrics")
    date: str = Field(..., description="Target date (YYYY-MM-DD)")
    route_name: Optional[str] = Field(None, description="Route name if filtered")


class DeleteResponse(BaseModel):
    """Response model for delete operation"""
    deleted_count: int = Field(..., description="Number of passengers deleted")
    filters_applied: Dict[str, Any] = Field(..., description="Filters used for deletion")
    message: str = Field(..., description="Success message")


# Load config on startup
try:
    config = get_config()
    STRAPI_URL = config.infrastructure.strapi_url
    GEOSPATIAL_URL = config.infrastructure.geospatial_url
except Exception:
    # Fallback for development
    STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337")
    GEOSPATIAL_URL = os.getenv("GEOSPATIAL_URL", "http://localhost:6000")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "manifest_api",
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
    # Load Strapi URL from config
    strapi_url = os.getenv("STRAPI_URL")
    if not strapi_url:
        if _config_available:
            try:
                config = get_config()
                strapi_url = config.infrastructure.strapi_url
            except Exception:
                strapi_url = "http://localhost:1337"  # Fallback default
        else:
            strapi_url = "http://localhost:1337"  # Fallback if config not available
    
    strapi_url = strapi_url.rstrip("/")
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


@app.get("/api/manifest/visualization/barchart", response_model=BarchartResponse)
async def get_barchart_visualization(
    date: str = Query(..., description="Target date (YYYY-MM-DD)"),
    route: Optional[str] = Query(None, description="Filter by route document ID"),
    start_hour: int = Query(0, ge=0, le=23, description="Start hour (0-23)"),
    end_hour: int = Query(23, ge=0, le=23, description="End hour (0-23)")
):
    """
    Get bar chart visualization data for passenger distribution.
    
    Returns hourly passenger counts for the specified date and time range.
    """
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if start_hour > end_hour:
        raise HTTPException(status_code=400, detail="start_hour cannot be greater than end_hour")
    
    try:
        # Fetch passengers
        passengers = await fetch_passengers_from_strapi(
            strapi_url=STRAPI_URL,
            route_id=route,
            target_date=target_date,
            start_hour=start_hour,
            end_hour=end_hour
        )
        
        # Generate barchart data
        barchart_data = generate_barchart_data(passengers)
        
        # Determine route name
        route_name = None
        if route:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{STRAPI_URL}/api/routes")
                routes = response.json().get('data', [])
                for r in routes:
                    if r.get('documentId') == route:
                        route_name = f"Route {r.get('short_name')}"
                        break
        
        return BarchartResponse(
            **barchart_data,
            date=date,
            route_name=route_name
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate barchart: {str(e)}"
        )


@app.get("/api/manifest/visualization/table", response_model=TableResponse)
async def get_table_visualization(
    date: str = Query(..., description="Target date (YYYY-MM-DD)"),
    route: Optional[str] = Query(None, description="Filter by route document ID"),
    start_hour: int = Query(0, ge=0, le=23, description="Start hour (0-23)"),
    end_hour: int = Query(23, ge=0, le=23, description="End hour (0-23)")
):
    """
    Get table visualization data with enriched passenger information.
    
    Returns detailed passenger data with geocoded addresses, distances, and metrics.
    """
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if start_hour > end_hour:
        raise HTTPException(status_code=400, detail="start_hour cannot be greater than end_hour")
    
    try:
        # Fetch passengers
        passengers = await fetch_passengers_from_strapi(
            strapi_url=STRAPI_URL,
            route_id=route,
            target_date=target_date,
            start_hour=start_hour,
            end_hour=end_hour
        )
        
        if not passengers:
            raise HTTPException(status_code=404, detail="No passengers found for the specified criteria")
        
        # Enrich with geocoding
        enriched_passengers = await enrich_passengers_with_geocoding(passengers, GEOSPATIAL_URL)
        
        # Calculate metrics
        metrics = calculate_route_metrics(enriched_passengers)
        
        # Determine route name
        route_name = None
        if route:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{STRAPI_URL}/api/routes")
                routes = response.json().get('data', [])
                for r in routes:
                    if r.get('documentId') == route:
                        route_name = f"Route {r.get('short_name')}"
                        break
        
        # Sort by depot distance
        sorted_passengers = sorted(enriched_passengers, key=lambda x: x['depot_distance'])
        
        # Format passenger data for JSON response
        passengers_data = []
        for item in sorted_passengers:
            p = item['passenger']
            passengers_data.append({
                'index': item['index'],
                'passenger_id': p.get('id'),
                'spawned_at': p.get('spawned_at'),
                'route_id': p.get('route_id'),
                'depot_id': p.get('depot_id'),
                'status': p.get('status'),
                'start_lat': p.get('latitude'),
                'start_lon': p.get('longitude'),
                'dest_lat': p.get('destination_lat'),
                'dest_lon': p.get('destination_lon'),
                'start_address': item['start_address'],
                'dest_address': item['dest_address'],
                'commute_distance': item['commute_distance'],
                'depot_distance': item['depot_distance']
            })
        
        metrics_response = RouteMetricsResponse(
            **metrics,
            date=date,
            route_name=route_name
        )
        
        return TableResponse(
            passengers=passengers_data,
            metrics=metrics_response,
            date=date,
            route_name=route_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate table: {str(e)}"
        )


@app.get("/api/manifest/stats", response_model=RouteMetricsResponse)
async def get_manifest_stats(
    date: str = Query(..., description="Target date (YYYY-MM-DD)"),
    route: Optional[str] = Query(None, description="Filter by route document ID"),
    start_hour: int = Query(0, ge=0, le=23, description="Start hour (0-23)"),
    end_hour: int = Query(23, ge=0, le=23, description="End hour (0-23)")
):
    """
    Get summary statistics for passenger manifest.
    
    Returns aggregated metrics including passenger counts, average distances, and total route distance.
    """
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if start_hour > end_hour:
        raise HTTPException(status_code=400, detail="start_hour cannot be greater than end_hour")
    
    try:
        # Fetch passengers
        passengers = await fetch_passengers_from_strapi(
            strapi_url=STRAPI_URL,
            route_id=route,
            target_date=target_date,
            start_hour=start_hour,
            end_hour=end_hour
        )
        
        if not passengers:
            raise HTTPException(status_code=404, detail="No passengers found for the specified criteria")
        
        # Enrich with geocoding
        enriched_passengers = await enrich_passengers_with_geocoding(passengers, GEOSPATIAL_URL)
        
        # Calculate metrics
        metrics = calculate_route_metrics(enriched_passengers)
        
        # Determine route name
        route_name = None
        if route:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{STRAPI_URL}/api/routes")
                routes = response.json().get('data', [])
                for r in routes:
                    if r.get('documentId') == route:
                        route_name = f"Route {r.get('short_name')}"
                        break
        
        return RouteMetricsResponse(
            **metrics,
            date=date,
            route_name=route_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate stats: {str(e)}"
        )


@app.delete("/api/manifest", response_model=DeleteResponse)
async def delete_passengers(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    day: Optional[str] = Query(None, description="Filter by day of week (monday-sunday)"),
    route: Optional[str] = Query(None, description="Filter by route document ID"),
    depot: Optional[str] = Query(None, description="Filter by depot document ID"),
    status: Optional[str] = Query(None, description="Filter by status (WAITING, BOARDED, etc.)"),
    start_hour: Optional[int] = Query(None, ge=0, le=23, description="Filter by start hour (0-23)"),
    end_hour: Optional[int] = Query(None, ge=0, le=23, description="Filter by end hour (0-23)"),
    start_time: Optional[str] = Query(None, description="Filter spawned_at >= ISO8601 timestamp"),
    end_time: Optional[str] = Query(None, description="Filter spawned_at <= ISO8601 timestamp"),
    confirm: bool = Query(False, description="Must be true to actually delete (safety check)")
):
    """
    Delete passengers matching the specified filters.
    
    Safety features:
    - Requires confirm=true to actually delete
    - Returns count of passengers that would be/were deleted
    - Supports flexible filtering by date, time, route, depot, status
    
    Examples:
    - Delete all passengers for Monday Route 1:
      DELETE /api/manifest?day=monday&route=gg3pv3z19hhm117v9xth5ezq&confirm=true
    
    - Delete passengers from specific hour:
      DELETE /api/manifest?date=2024-11-04&start_hour=17&end_hour=17&confirm=true
    
    - Delete all waiting passengers:
      DELETE /api/manifest?status=WAITING&confirm=true
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to delete passengers. This is a safety check."
        )
    
    # Parse date if provided
    target_date = None
    if date:
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Parse day if provided (convert to date)
    if day:
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        if day.lower() not in day_map:
            raise HTTPException(status_code=400, detail="Invalid day. Use monday-sunday")
        
        from datetime import timedelta
        base_date = datetime(2024, 11, 4)  # Monday, Nov 4, 2024
        day_offset = day_map[day.lower()]
        target_date = base_date + timedelta(days=day_offset)
    
    # Validate hour range
    if start_hour is not None and end_hour is not None:
        if start_hour > end_hour:
            raise HTTPException(status_code=400, detail="start_hour cannot be greater than end_hour")
    
    try:
        # Fetch passengers matching filters (don't geocode, just get raw data)
        passengers = await fetch_passengers_from_strapi(
            strapi_url=STRAPI_URL,
            route_id=route,
            target_date=target_date,
            start_hour=start_hour or 0,
            end_hour=end_hour or 23
        )
        
        # Further filter by depot and status if provided
        filtered_passengers = []
        for p in passengers:
            # Filter by depot
            if depot and p.get('depot_id') != depot:
                continue
            
            # Filter by status
            if status and p.get('status') != status:
                continue
            
            # Filter by start_time/end_time if provided
            if start_time or end_time:
                spawn_time_str = p.get('spawned_at')
                if spawn_time_str:
                    spawn_time = datetime.fromisoformat(spawn_time_str.replace('Z', '+00:00'))
                    
                    if start_time:
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        if spawn_time < start_dt:
                            continue
                    
                    if end_time:
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        if spawn_time > end_dt:
                            continue
            
            filtered_passengers.append(p)
        
        if not filtered_passengers:
            return DeleteResponse(
                deleted_count=0,
                filters_applied={
                    "date": date,
                    "day": day,
                    "route": route,
                    "depot": depot,
                    "status": status,
                    "start_hour": start_hour,
                    "end_hour": end_hour,
                    "start_time": start_time,
                    "end_time": end_time
                },
                message="No passengers found matching the specified filters"
            )
        
        # Delete passengers via Strapi API
        deleted_count = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for p in filtered_passengers:
                passenger_id = p.get('id')
                if passenger_id:
                    delete_url = f"{STRAPI_URL}/api/active-passengers/{passenger_id}"
                    response = await client.delete(delete_url)
                    if response.status_code in [200, 204]:
                        deleted_count += 1
        
        return DeleteResponse(
            deleted_count=deleted_count,
            filters_applied={
                "date": date,
                "day": day,
                "route": route,
                "depot": depot,
                "status": status,
                "start_hour": start_hour,
                "end_hour": end_hour,
                "start_time": start_time,
                "end_time": end_time
            },
            message=f"Successfully deleted {deleted_count} passenger(s)"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete passengers: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    import configparser
    from pathlib import Path
    
    # Load port from config.ini
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent.parent.parent.parent / "config.ini"
    config.read(config_path, encoding='utf-8')
    
    # Extract port from manifest_url (e.g., "http://localhost:4000" -> 4000)
    manifest_url = config.get('infrastructure', 'manifest_url', fallback='http://localhost:4000')
    port = int(manifest_url.split(':')[-1])
    
    uvicorn.run(app, host="0.0.0.0", port=port)
