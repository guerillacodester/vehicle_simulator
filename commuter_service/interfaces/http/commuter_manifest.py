"""
Commuter Manifest API
---------------------

FastAPI service providing enriched passenger manifests for UI consumption.

Wraps the manifest_query to provide HTTP access to ordered, geocoded passenger data.

Usage:
    uvicorn commuter_service.interfaces.http.commuter_manifest:app --host 0.0.0.0 --port 4000

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
import logging
import traceback
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Query, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import json
import asyncio
from typing import Set


logger = logging.getLogger(__name__)

from commuter_service.application.queries import (
    enrich_manifest_rows,
    fetch_passengers,
    ManifestRow
)
from commuter_service.application.queries.manifest_visualization import (
    fetch_passengers_from_strapi,
    generate_barchart_data,
    enrich_passengers_with_geocoding,
    calculate_route_metrics
)
from commuter_service.infrastructure.config import get_config
from commuter_service.interfaces.http.passenger_crud import router as passenger_router

try:
    from common.config_provider import get_config
    _config_available = True
except ImportError:
    _config_available = False

app = FastAPI(
    title="Commuter Manifest API",
    description="Enriched passenger manifest with route positions and geocoded addresses",
    version="1.0.0"
)

# Include CRUD router
app.include_router(passenger_router)

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


class SeedRequest(BaseModel):
    """Request model for seeding passengers"""
    route: str = Field(..., description="Route short name (e.g., '1', '5')")
    day: Optional[str] = Field(None, description="Day of week (monday-sunday)")
    date: Optional[str] = Field(None, description="Specific date (YYYY-MM-DD)")
    type: str = Field("route", description="Spawn type: 'route', 'depot', or 'both'")
    start_hour: int = Field(0, ge=0, le=23, description="Start hour (0-23)")
    end_hour: int = Field(23, ge=0, le=23, description="End hour (0-23)")


class SeedResponse(BaseModel):
    """Response model for seed operation"""
    status: str = Field(..., description="Status: 'started', 'completed', 'error'")
    message: str = Field(..., description="Status message")
    route: str = Field(..., description="Route being seeded")
    date: str = Field(..., description="Target date")
    spawn_type: str = Field(..., description="Type of spawning")
    time_range: str = Field(..., description="Hour range")
    total_spawned: Optional[int] = Field(None, description="Total passengers spawned")


# Load config on startup
try:
    config = get_config()
    STRAPI_URL = config.infrastructure.strapi_url
    GEOSPATIAL_URL = config.infrastructure.geospatial_url
except Exception:
    # Fallback for development
    STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337")
    GEOSPATIAL_URL = os.getenv("GEOSPATIAL_URL", "http://localhost:6000")


async def get_route_document_id(route_short_name: str) -> Optional[str]:
    """Convert route short name (e.g., '1') to document ID"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{STRAPI_URL}/api/routes")
            routes = response.json().get('data', [])
            
            for r in routes:
                if r.get('short_name') == route_short_name:
                    return r.get('documentId')
        except Exception as e:
            logger.warning(f"Failed to lookup route '{route_short_name}': {e}")
    
    return None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "commuter_manifest",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/query")
async def flexible_query(
    # Filters
    route: Optional[str] = Query(None, description="Filter by route ID or short name"),
    depot: Optional[str] = Query(None, description="Filter by depot ID"),
    status: Optional[str] = Query(None, description="Filter by status (WAITING, BOARDED, etc.)"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    hour_start: Optional[int] = Query(None, ge=0, le=23, description="Filter hour >= (0-23)"),
    hour_end: Optional[int] = Query(None, ge=0, le=23, description="Filter hour <= (0-23)"),
    vehicle: Optional[str] = Query(None, description="Filter by vehicle ID"),
    
    # Grouping and aggregation
    group_by: Optional[str] = Query(None, description="Group by field (hour, route, depot, status, date)"),
    aggregate: Optional[str] = Query(None, description="Aggregate function (count, avg, sum, min, max)"),
    
    # Sorting and limiting
    sort_by: Optional[str] = Query(None, description="Sort by field"),
    limit: Optional[int] = Query(None, gt=0, description="Limit number of results"),
    
    # Output format
    format: str = Query("json", description="Output format (json, table, barchart, csv)"),
    geocode: bool = Query(False, description="Include geocoded addresses"),
):
    """
    Flexible query endpoint supporting dynamic filters, grouping, and formats.
    
    Examples:
        - /api/query?route=1&status=WAITING - All waiting passengers on route 1
        - /api/query?depot=DEPOT_001&group_by=hour&aggregate=count - Hourly counts by depot
        - /api/query?date=2024-11-04&group_by=route&aggregate=count - Passenger counts by route
        - /api/query?route=1&geocode=true&format=table - Geocoded table for route 1
        - /api/query?hour_start=7&hour_end=9&group_by=depot&format=barchart - Morning rush by depot
    """
    from commuter_service.application.queries.flexible_query import execute_flexible_query
    
    # Translate route short name to document ID if needed
    route_id = None
    if route:
        route_id = await get_route_document_id(route)
        if not route_id:
            route_id = route
    
    # Build filters dict
    filters = {}
    if route_id:
        filters['route'] = route_id
    if depot:
        filters['depot'] = depot
    if status:
        filters['status'] = status
    if date:
        filters['date'] = date
    if hour_start is not None:
        filters['hour_start'] = hour_start
    if hour_end is not None:
        filters['hour_end'] = hour_end
    if vehicle:
        filters['vehicle'] = vehicle
    
    try:
        result = await execute_flexible_query(
            strapi_url=STRAPI_URL,
            filters=filters,
            group_by=group_by,
            aggregate=aggregate,
            sort_by=sort_by,
            limit=limit,
            format=format,
            geocode=geocode,
            geo_url=GEOSPATIAL_URL if geocode else None
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/manifest", response_model=ManifestResponse)
async def get_manifest(
    route: Optional[str] = Query(None, description="Filter by route_id"),
    depot: Optional[str] = Query(None, description="Filter by depot_id"),
    status: Optional[str] = Query(None, description="Filter by status (e.g., WAITING, BOARDED)"),
    start: Optional[str] = Query(None, description="Filter spawned_at >= ISO8601 timestamp"),
    end: Optional[str] = Query(None, description="Filter spawned_at <= ISO8601 timestamp"),
    sort: str = Query("spawned_at:asc", description="Sort order (default: spawned_at:asc)")
):
    """
    Get enriched passenger manifest with route positions and geocoded addresses.
    
    Returns ALL passengers matching the filters (no pagination limit).
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
    
    # Convert route short name to document ID
    route_id = None
    if route:
        route_id = await get_route_document_id(route)
        if not route_id:
            raise HTTPException(
                status_code=404,
                detail=f"Route '{route}' not found"
            )
    
    # Build Strapi query params - NO FILTERS because Strapi pagination breaks with filters
    # We'll filter in Python after fetching all passengers
    # Strapi max pageSize is 100, not 1000
    params = {
        "pagination[pageSize]": 100,
        "sort": sort,
    }
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes for geocoding 300+ passengers
            # Fetch ALL passengers from Strapi (no filters - Strapi pagination bug)
            all_rows = await fetch_passengers(client, strapi_url, token, params)
            
            # Broadcast total count
            await manager.broadcast({
                "type": "manifest:start",
                "data": {"total_passengers": len(all_rows), "route_id": route_id}
            })
            
            # Filter in Python (Strapi pagination doesn't work with filters)
            rows = []
            for idx, row in enumerate(all_rows, 1):
                # Apply filters
                if route_id and row.get("route_id") != route_id:
                    continue
                if depot and row.get("depot_id") != depot:
                    continue
                if status and row.get("status") != status:
                    continue
                if start:
                    spawned = row.get("spawned_at", "")
                    if spawned < start:
                        continue
                if end:
                    spawned = row.get("spawned_at", "")
                    if spawned > end:
                        continue
                rows.append(row)
                
                # Broadcast progress every 50 passengers
                if idx % 50 == 0:
                    await manager.broadcast({
                        "type": "manifest:filter_progress",
                        "data": {"processed": idx, "total": len(all_rows), "matched": len(rows)}
                    })
            
            # Broadcast filtered count
            await manager.broadcast({
                "type": "manifest:filtered",
                "data": {"total_filtered": len(rows), "route_id": route_id}
            })
            
            # Progress callback for streaming enriched passengers
            async def on_passenger_enriched(row, index, total):
                await manager.broadcast({
                    "type": "manifest:passenger",
                    "data": {
                        "passenger": row.to_json(),
                        "index": index,
                        "total": total,
                        "progress_percent": round((index / total) * 100, 1)
                    }
                })
            
            # Enrich with positions, addresses, distances (streams via callback)
            enriched = await enrich_manifest_rows(rows, route_id, progress_callback=on_passenger_enriched)
            
            # Broadcast completion
            await manager.broadcast({
                "type": "manifest:complete",
                "data": {"total_passengers": len(enriched), "route_id": route_id}
            })
            
            # Convert to JSON-serializable dict
            passengers_data = [row.to_json() for row in enriched]
            
            return ManifestResponse(
                count=len(passengers_data),
                route_id=route_id,
                depot_id=depot,
                passengers=passengers_data,
                ordered_by_route_position=bool(route_id)
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
    route: Optional[str] = Query(None, description="Filter by route short name or document ID"),
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
    
    # Translate route short name to document ID if needed
    route_id = None
    if route:
        route_id = await get_route_document_id(route)
        if not route_id:
            route_id = route  # Fallback if already document ID
    
    try:
        # Fetch passengers
        passengers = await fetch_passengers_from_strapi(
            strapi_url=STRAPI_URL,
            route_id=route_id,
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
    route: Optional[str] = Query(None, description="Filter by route short name or document ID"),
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
    
    # Translate route short name to document ID if needed
    route_id = None
    if route:
        route_id = await get_route_document_id(route)
        if not route_id:
            route_id = route  # Fallback if already document ID
    
    try:
        # Fetch passengers
        passengers = await fetch_passengers_from_strapi(
            strapi_url=STRAPI_URL,
            route_id=route_id,
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


class SeedRequest(BaseModel):
    """Request model for seeding passengers"""
    route: str = Field(..., description="Route short name (e.g., '1', '5')")
    day: Optional[str] = Field(None, description="Day of week (monday-sunday)")
    date: Optional[str] = Field(None, description="Specific date (YYYY-MM-DD)")
    spawn_type: str = Field("route", description="Type: 'route', 'depot', or 'both'")
    start_hour: int = Field(0, ge=0, le=23, description="Start hour (0-23)")
    end_hour: int = Field(23, ge=0, le=23, description="End hour (0-23)")


class SeedResponse(BaseModel):
    """Response model for seed operation"""
    success: bool = Field(..., description="Whether seeding completed successfully")
    route: str = Field(..., description="Route short name")
    date: str = Field(..., description="Target date")
    spawn_type: str = Field(..., description="Spawn type used")
    route_passengers: int = Field(0, description="Route passengers created")
    depot_passengers: int = Field(0, description="Depot passengers created")
    total_created: int = Field(..., description="Total passengers created")
    message: str = Field(..., description="Status message")


@app.post("/api/seed", response_model=SeedResponse)
async def seed_passengers(request: SeedRequest):
    """
    Seed passengers for a route (remote seeding trigger).
    
    This endpoint triggers the seeding process on the server, allowing
    remote clients to seed passengers without direct access to seed.py.
    
    Examples:
    - POST /api/seed with body:
      {
        "route": "1",
        "day": "monday",
        "spawn_type": "route",
        "start_hour": 7,
        "end_hour": 9
      }
    """
    try:
        # Import seeding components
        from commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawner
        from commuter_service.core.domain.spawner_engine.depot_spawner import DepotSpawner
        from commuter_service.domain.services.reservoirs.route_reservoir import RouteReservoir
        from commuter_service.domain.services.reservoirs.depot_reservoir import DepotReservoir
        from commuter_service.infrastructure.spawn.config_loader import SpawnConfigLoader
        from commuter_service.infrastructure.geospatial.client import GeospatialClient
        from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
        from datetime import timedelta
        
        # Validate date or day
        if not request.day and not request.date:
            raise HTTPException(status_code=400, detail="Either 'day' or 'date' must be specified")
        
        if request.day and request.date:
            raise HTTPException(status_code=400, detail="Cannot specify both 'day' and 'date'")
        
        # Determine target date
        if request.date:
            try:
                target_date = datetime.strptime(request.date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            # Map day to date
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            if request.day.lower() not in day_map:
                raise HTTPException(status_code=400, detail="Invalid day. Use monday-sunday")
            
            base_date = datetime(2024, 11, 4)  # Monday, Nov 4, 2024
            day_offset = day_map[request.day.lower()]
            target_date = base_date + timedelta(days=day_offset)
        
        # Get route documentId
        route_doc_id = await get_route_document_id(request.route)
        if not route_doc_id:
            raise HTTPException(status_code=404, detail=f"Route '{request.route}' not found")
        
        # Initialize components
        passenger_repo = PassengerRepository(strapi_url=STRAPI_URL)
        await passenger_repo.connect()
        
        config_loader = SpawnConfigLoader(api_base_url=f"{STRAPI_URL}/api")
        geo_client = GeospatialClient(base_url=GEOSPATIAL_URL)
        
        total_route = 0
        total_depot = 0
        
        try:
            # Create spawners based on type
            if request.spawn_type in ['route', 'both']:
                route_reservoir = RouteReservoir(
                    passenger_repository=passenger_repo,
                    enable_redis_cache=False
                )
                
                route_spawner = RouteSpawner(
                    reservoir=route_reservoir,
                    config={},
                    route_id=route_doc_id,
                    config_loader=config_loader,
                    geo_client=geo_client
                )
                
                # Spawn for each hour
                total_hours = request.end_hour - request.start_hour + 1
                logger.info(f"Spawning route passengers for {total_hours} hours ({request.start_hour}-{request.end_hour})...")
                
                for idx, hour in enumerate(range(request.start_hour, request.end_hour + 1), 1):
                    spawn_time = target_date.replace(hour=hour, minute=0, second=0)
                    route_requests = await route_spawner.spawn(current_time=spawn_time, time_window_minutes=60)
                    
                    successful = 0
                    if route_requests:
                        successful, failed = await route_reservoir.push_batch(route_requests)
                        total_route += successful
                        
                        # Emit WebSocket event for each passenger spawned
                        for passenger in route_requests[:successful]:  # Only successful ones
                            spawn_lat, spawn_lon = passenger.spawn_location
                            dest_lat, dest_lon = passenger.destination_location
                            await manager.broadcast({
                                "type": "seed:progress",
                                "data": {
                                    "passenger_id": passenger.passenger_id,
                                    "route": request.route,
                                    "hour": hour,
                                    "spawn_time": passenger.spawn_time.isoformat(),
                                    "spawn_location": {"lat": spawn_lat, "lon": spawn_lon},
                                    "destination": {"lat": dest_lat, "lon": dest_lon},
                                    "total_so_far": total_route
                                },
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            })
                    
                    # Emit hour completion event
                    percent = (idx / total_hours) * 100
                    await manager.broadcast({
                        "type": "seed:hour_complete",
                        "data": {
                            "route": request.route,
                            "hour": hour,
                            "passengers_this_hour": successful,
                            "total_so_far": total_route,
                            "progress_percent": percent,
                            "hours_completed": idx,
                            "total_hours": total_hours
                        },
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                    
                    # Log progress
                    logger.info(f"Route spawn progress: Hour {hour} ({idx}/{total_hours}, {percent:.1f}%) - {successful} passengers")
                    
                    await asyncio.sleep(0.1)
            
            if request.spawn_type in ['depot', 'both']:
                # Fetch depot info
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{GEOSPATIAL_URL}/routes/by-document-id/{route_doc_id}/depot")
                    depot_info = response.json().get('depot')
                    depot_doc_id = depot_info['documentId']
                    depot_lat = depot_info['latitude']
                    depot_lon = depot_info['longitude']
                
                depot_reservoir = DepotReservoir(
                    depot_id=depot_doc_id,
                    passenger_repository=passenger_repo,
                    enable_redis_cache=False
                )
                
                depot_spawner = DepotSpawner(
                    reservoir=depot_reservoir,
                    config={},
                    depot_id=depot_doc_id,
                    depot_location=(depot_lat, depot_lon),
                    available_routes=[route_doc_id],
                    depot_document_id=depot_doc_id,
                    config_loader=config_loader,
                    geo_client=geo_client
                )
                
                # Spawn for each hour
                for hour in range(request.start_hour, request.end_hour + 1):
                    spawn_time = target_date.replace(hour=hour, minute=0, second=0)
                    depot_requests = await depot_spawner.spawn(current_time=spawn_time, time_window_minutes=60)
                    
                    if depot_requests:
                        successful, failed = await depot_reservoir.push_batch(depot_requests)
                        total_depot += successful
                    
                    await asyncio.sleep(0.1)
            
            total_created = total_route + total_depot
            
            return SeedResponse(
                success=True,
                route=request.route,
                date=target_date.strftime('%Y-%m-%d'),
                spawn_type=request.spawn_type,
                route_passengers=total_route,
                depot_passengers=total_depot,
                total_created=total_created,
                message=f"Successfully seeded {total_created} passengers for route {request.route}"
            )
        
        finally:
            await passenger_repo.disconnect()
    
    except HTTPException:
        raise
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"Seeding failed: {e}\n{error_traceback}")
        raise HTTPException(
            status_code=500,
            detail=f"Seeding failed: {str(e)}"
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
    # Convert route short name to document ID (e.g., "1" -> "gg3pv3z19hhm117v9xth5ezq")
    route_id = None
    if route:
        route_id = await get_route_document_id(route)
        if not route_id:
            # Maybe it's already a document ID, try using it as-is
            route_id = route
    
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
            route_id=route_id,  # Use translated route_id instead of route
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
        
        # If confirm not set, return count only (dry-run)
        if not confirm:
            return DeleteResponse(
                deleted_count=len(filtered_passengers),
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
                message=f"Dry run: Would delete {len(filtered_passengers)} passenger(s). Use confirm=true to proceed."
            )
        
        # Delete passengers via Strapi API
        total_to_delete = len(filtered_passengers)
        deleted_count = 0
        logger.info(f"Starting deletion of {total_to_delete} passengers...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, p in enumerate(filtered_passengers, 1):
                # Strapi 5 uses document_id, not sequential id
                document_id = p.get('documentId')  # Note: Strapi returns camelCase
                if document_id:
                    delete_url = f"{STRAPI_URL}/api/active-passengers/{document_id}"
                    response = await client.delete(delete_url)
                    if response.status_code in [200, 204]:
                        deleted_count += 1
                        
                        # Emit WebSocket progress event every 10 deletions
                        if idx % 10 == 0 or idx == total_to_delete:
                            percent = (idx / total_to_delete) * 100
                            await manager.broadcast({
                                "type": "delete:progress",
                                "data": {
                                    "deleted_so_far": deleted_count,
                                    "total": total_to_delete,
                                    "progress_percent": percent,
                                    "passenger_id": p.get('passenger_id', 'unknown')
                                },
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            })
                        
                        # Log progress every 10% or every 50 passengers
                        if idx % 50 == 0 or idx % (total_to_delete // 10) == 0 and total_to_delete > 10:
                            percent = (idx / total_to_delete) * 100
                            logger.info(f"Delete progress: {idx}/{total_to_delete} ({percent:.1f}%)")
        
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


# ============================================================================
# WEBSOCKET STREAMING
# ============================================================================

# Global event queue for spawner → WebSocket communication
_event_queue: asyncio.Queue = None

def get_event_queue() -> asyncio.Queue:
    """Get or create the global event queue"""
    global _event_queue
    if _event_queue is None:
        _event_queue = asyncio.Queue()
    return _event_queue


async def emit_passenger_event(event_type: str, passenger_data: dict, route_id: str = None):
    """
    Emit passenger lifecycle event to WebSocket clients.
    
    Called by spawners when passengers spawn/board/alight.
    
    Args:
        event_type: "spawned", "boarded", "alighted"
        passenger_data: Passenger information
        route_id: Route ID for targeted broadcast (optional)
    """
    message = {
        "type": f"passenger:{event_type}",
        "data": passenger_data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if route_id:
        await manager.broadcast_to_route(route_id, message)
    else:
        await manager.broadcast(message)


class ConnectionManager:
    """Manages WebSocket connections for real-time streaming"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.route_subscriptions: Dict[str, Set[WebSocket]] = {}
        logger.info("🔌 WebSocket ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ WebSocket connected | Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        
        # Remove from route subscriptions
        for route_id, subscribers in list(self.route_subscriptions.items()):
            subscribers.discard(websocket)
            if not subscribers:
                del self.route_subscriptions[route_id]
        
        logger.info(f"⚫ WebSocket disconnected | Total: {len(self.active_connections)}")
    
    async def subscribe_to_route(self, websocket: WebSocket, route_id: str):
        """Subscribe connection to specific route events"""
        if route_id not in self.route_subscriptions:
            self.route_subscriptions[route_id] = set()
        
        self.route_subscriptions[route_id].add(websocket)
        logger.info(f"📡 Client subscribed to route: {route_id}")
    
    async def unsubscribe_from_route(self, websocket: WebSocket, route_id: str):
        """Unsubscribe connection from route events"""
        if route_id in self.route_subscriptions:
            self.route_subscriptions[route_id].discard(websocket)
            if not self.route_subscriptions[route_id]:
                del self.route_subscriptions[route_id]
        
        logger.info(f"🔕 Client unsubscribed from route: {route_id}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        dead_connections = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                dead_connections.add(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            await self.disconnect(conn)
    
    async def broadcast_to_route(self, route_id: str, message: dict):
        """Broadcast message to clients subscribed to specific route"""
        if route_id not in self.route_subscriptions:
            return
        
        dead_connections = set()
        subscribers = self.route_subscriptions[route_id].copy()
        
        for connection in subscribers:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                dead_connections.add(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            await self.disconnect(conn)


# Global connection manager
manager = ConnectionManager()


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time passenger event streaming.
    
    Client → Server messages:
        {"type": "subscribe", "route": "1"}
        {"type": "unsubscribe", "route": "1"}
        {"type": "ping"}
    
    Server → Client messages:
        {"type": "passenger:spawned", "data": {...}}
        {"type": "passenger:boarded", "data": {...}}
        {"type": "passenger:alighted", "data": {...}}
        {"type": "pong"}
        {"type": "error", "message": "..."}
    """
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Commuter Service WebSocket",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Listen for client messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "subscribe":
                route = data.get("route")
                if route:
                    await manager.subscribe_to_route(websocket, route)
                    
                    # Start monitoring this route
                    try:
                        from commuter_service.services.passenger_monitor import get_monitor
                        monitor = get_monitor()
                        monitor.add_monitored_route(route)
                    except:
                        pass
                    
                    await websocket.send_json({
                        "type": "subscribed",
                        "route": route,
                        "message": f"Subscribed to route {route}"
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing 'route' parameter"
                    })
            
            elif message_type == "unsubscribe":
                route = data.get("route")
                if route:
                    await manager.unsubscribe_from_route(websocket, route)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "route": route,
                        "message": f"Unsubscribed from route {route}"
                    })
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


@app.get("/api/query")
async def flexible_query(
    route: Optional[str] = Query(None, description="Filter by route short name or document ID"),
    depot: Optional[str] = Query(None, description="Filter by depot ID"),
    status: Optional[str] = Query(None, description="Filter by status (WAITING, BOARDING, etc.)"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    start_hour: Optional[int] = Query(None, ge=0, le=23, description="Start hour (0-23)"),
    end_hour: Optional[int] = Query(None, ge=0, le=23, description="End hour (0-23)"),
    vehicle: Optional[str] = Query(None, description="Filter by vehicle ID"),
    format: str = Query("json", description="Output format: json, table, barchart, csv, summary"),
    groupby: Optional[str] = Query(None, description="Group by: hour, depot, route, status"),
    geocode: bool = Query(False, description="Include geocoded addresses (slower)"),
    limit: Optional[int] = Query(None, description="Limit results"),
    sort: Optional[str] = Query(None, description="Sort by field")
):
    """
    Flexible query endpoint for passenger data with dynamic filtering and output formats.
    
    Examples:
        /api/query?route=1&status=WAITING&format=table
        /api/query?depot=DEPOT_001&format=barchart&groupby=hour
        /api/query?date=2024-11-04&start_hour=7&end_hour=9&format=summary
        /api/query?route=1&geocode=true&format=csv
    """
    strapi_url = STRAPI_URL
    token = os.getenv("STRAPI_TOKEN")
    
    # Translate route short name to document ID if needed
    route_id = None
    if route:
        route_id = await get_route_document_id(route)
        if not route_id:
            route_id = route  # Fallback if already document ID
    
    try:
        # Fetch all passengers
        params = {"pagination[pageSize]": 100}
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            all_rows = await fetch_passengers(client, strapi_url, token, params)
        
        # Apply filters
        filtered = []
        for row in all_rows:
            # Route filter
            if route_id and row.get("route_id") != route_id:
                continue
            
            # Depot filter
            if depot and row.get("depot_id") != depot:
                continue
            
            # Status filter
            if status and row.get("status") != status:
                continue
            
            # Vehicle filter
            if vehicle and row.get("vehicle_id") != vehicle:
                continue
            
            # Date/time filters
            if date or start_hour is not None or end_hour is not None:
                spawned = row.get("spawned_at")
                if spawned:
                    spawn_dt = datetime.fromisoformat(spawned.replace('Z', '+00:00'))
                    
                    if date:
                        target_date = datetime.strptime(date, '%Y-%m-%d')
                        if spawn_dt.date() != target_date.date():
                            continue
                    
                    if start_hour is not None and spawn_dt.hour < start_hour:
                        continue
                    
                    if end_hour is not None and spawn_dt.hour > end_hour:
                        continue
            
            filtered.append(row)
        
        # Apply limit
        if limit:
            filtered = filtered[:limit]
        
        # Apply sort
        if sort:
            filtered.sort(key=lambda x: x.get(sort, ""))
        
        # Format output
        if format == "summary":
            return {
                "total": len(filtered),
                "by_status": _group_by(filtered, "status"),
                "by_route": _group_by(filtered, "route_id"),
                "by_depot": _group_by(filtered, "depot_id"),
                "by_hour": _group_by_hour(filtered)
            }
        
        elif format == "barchart" or groupby == "hour":
            hourly = _group_by_hour(filtered)
            total = len(filtered)
            peak_hour = max(hourly.items(), key=lambda x: x[1])[0] if hourly else 0
            return {
                "hourly_counts": [hourly.get(h, 0) for h in range(24)],
                "total": total,
                "peak_hour": peak_hour
            }
        
        elif format == "table" and geocode:
            # Enrich with geocoding
            enriched = await enrich_passengers_with_geocoding(filtered, GEOSPATIAL_URL)
            return {"passengers": enriched, "total": len(enriched)}
        
        elif format == "csv":
            # Return CSV-friendly format
            csv_data = []
            for row in filtered:
                csv_data.append({
                    "passenger_id": row.get("passenger_id"),
                    "spawned_at": row.get("spawned_at"),
                    "route_id": row.get("route_id"),
                    "depot_id": row.get("depot_id"),
                    "status": row.get("status"),
                    "latitude": row.get("latitude"),
                    "longitude": row.get("longitude"),
                    "destination_lat": row.get("destination_lat"),
                    "destination_lon": row.get("destination_lon")
                })
            return {"data": csv_data, "total": len(csv_data)}
        
        else:  # default json format
            if groupby:
                return {
                    "grouped": _group_by(filtered, groupby),
                    "total": len(filtered)
                }
            return {"passengers": filtered, "total": len(filtered)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


def _group_by(data: List[Dict], field: str) -> Dict[str, int]:
    """Group data by field and count"""
    groups = {}
    for item in data:
        key = item.get(field, "unknown")
        groups[key] = groups.get(key, 0) + 1
    return groups


def _group_by_hour(data: List[Dict]) -> Dict[int, int]:
    """Group data by hour of spawned_at"""
    groups = {}
    for item in data:
        spawned = item.get("spawned_at")
        if spawned:
            try:
                spawn_dt = datetime.fromisoformat(spawned.replace('Z', '+00:00'))
                hour = spawn_dt.hour
                groups[hour] = groups.get(hour, 0) + 1
            except:
                pass
    return groups


@app.get("/api/monitor/stats")
async def get_monitor_stats():
    """
    Get passenger monitor statistics.
    
    Returns real-time monitoring stats including:
    - Number of state changes detected
    - External updates detected
    - Cached passengers
    - Monitored routes
    """
    try:
        from commuter_service.services.passenger_monitor import get_monitor
        monitor = get_monitor()
        return monitor.get_stats()
    except Exception as e:
        return {"error": str(e), "running": False}


if __name__ == "__main__":
    import uvicorn
    import configparser
    from pathlib import Path
    
    # Load port from config.ini
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent.parent.parent.parent / "config.ini"
    config.read(config_path, encoding='utf-8')
    
    # Extract port from commuter_service_url (e.g., "http://localhost:4000" -> 4000)
    commuter_service_url = config.get('infrastructure', 'commuter_service_url', fallback='http://localhost:4000')
    port = int(commuter_service_url.split(':')[-1])
    
    uvicorn.run(app, host="0.0.0.0", port=port)
