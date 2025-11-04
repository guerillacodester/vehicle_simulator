"""
Passenger CRUD API - Production Grade

Full CRUD operations for passenger management:
- GET /api/passengers - List/search passengers
- GET /api/passengers/{id} - Get single passenger
- POST /api/passengers - Create passenger
- PUT /api/passengers/{id} - Update passenger
- PATCH /api/passengers/{id}/board - Board passenger
- PATCH /api/passengers/{id}/alight - Alight passenger
- PATCH /api/passengers/{id}/cancel - Cancel passenger
- DELETE /api/passengers/{id} - Delete passenger
"""

from typing import Optional, List
import sys
import os

# Add project root to path for shared utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from arknet_transit_simulator.utils.geospatial import haversine
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import httpx

from commuter_service.domain.models.passenger_state import (
    PassengerStatus,
    calculate_passenger_state,
    validate_state_transition
)

router = APIRouter(prefix="/api/passengers", tags=["passengers"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PassengerCreate(BaseModel):
    """Request to create a new passenger"""
    passenger_id: Optional[str] = None
    route_id: str
    depot_id: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lon: float = Field(..., ge=-180, le=180)
    destination_name: str = "Stop"
    spawned_at: Optional[datetime] = None
    status: str = "WAITING"


class PassengerUpdate(BaseModel):
    """Request to update passenger fields"""
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    destination_lat: Optional[float] = Field(None, ge=-90, le=90)
    destination_lon: Optional[float] = Field(None, ge=-180, le=180)
    destination_name: Optional[str] = None
    route_id: Optional[str] = None
    depot_id: Optional[str] = None


class PassengerBoardRequest(BaseModel):
    """Request to board a passenger"""
    vehicle_id: str
    boarded_at: Optional[datetime] = None


class PassengerAlightRequest(BaseModel):
    """Request to alight a passenger"""
    alighted_at: Optional[datetime] = None


class PassengerResponse(BaseModel):
    """Passenger response with computed state"""
    id: int
    documentId: str
    passenger_id: str
    route_id: Optional[str]
    depot_id: Optional[str]
    latitude: float
    longitude: float
    destination_lat: float
    destination_lon: float
    destination_name: str
    spawned_at: datetime
    boarded_at: Optional[datetime]
    alighted_at: Optional[datetime]
    vehicle_id: Optional[str]
    status: PassengerStatus
    computed_state: PassengerStatus
    createdAt: datetime
    updatedAt: datetime


class PassengerListResponse(BaseModel):
    """List of passengers with pagination"""
    data: List[PassengerResponse]
    meta: dict


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=PassengerListResponse)
async def list_passengers(
    route: Optional[str] = Query(None, description="Filter by route ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    date: Optional[str] = Query(None, description="Filter by spawn date (YYYY-MM-DD)"),
    start_time: Optional[str] = Query(None, description="Filter spawned_at >= ISO8601"),
    end_time: Optional[str] = Query(None, description="Filter spawned_at <= ISO8601"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sort: str = Query("spawned_at:desc", description="Sort field:direction")
):
    """
    List and filter passengers with pagination.
    
    Examples:
    - All waiting passengers: ?status=WAITING
    - Route 1 passengers: ?route=gg3pv3z19hhm117v9xth5ezq
    - Passengers on vehicle: ?vehicle_id=BUS_001
    - Spawned today: ?date=2024-11-04
    """
    from commuter_service.infrastructure.config import get_config
    import os
    
    config = get_config()
    strapi_url = config.infrastructure.strapi_url.rstrip("/")
    
    # Build Strapi query
    params = {
        "pagination[page]": page,
        "pagination[pageSize]": page_size,
        "sort": sort
    }
    
    if route:
        params["filters[route_id][$eq]"] = route
    if status:
        params["filters[status][$eq]"] = status
    if vehicle_id:
        params["filters[vehicle_id][$eq]"] = vehicle_id
    if start_time:
        params["filters[spawned_at][$gte]"] = start_time
    if end_time:
        params["filters[spawned_at][$lte]"] = end_time
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{strapi_url}/api/active-passengers", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Enrich with computed state
        passengers = []
        for item in data.get("data", []):
            p = item
            
            # Calculate actual state from timestamps
            computed_state = calculate_passenger_state(
                spawned_at=p.get("spawned_at"),
                boarded_at=p.get("boarded_at"),
                alighted_at=p.get("alighted_at"),
                status=p.get("status")
            )
            
            passengers.append(PassengerResponse(
                id=p.get("id"),
                documentId=p.get("documentId"),
                passenger_id=p.get("passenger_id"),
                route_id=p.get("route_id"),
                depot_id=p.get("depot_id"),
                latitude=p.get("latitude"),
                longitude=p.get("longitude"),
                destination_lat=p.get("destination_lat"),
                destination_lon=p.get("destination_lon"),
                destination_name=p.get("destination_name", "Stop"),
                spawned_at=p.get("spawned_at"),
                boarded_at=p.get("boarded_at"),
                alighted_at=p.get("alighted_at"),
                vehicle_id=p.get("vehicle_id"),
                status=PassengerStatus(p.get("status", "WAITING")),
                computed_state=computed_state,
                createdAt=p.get("createdAt"),
                updatedAt=p.get("updatedAt")
            ))
        
        return PassengerListResponse(
            data=passengers,
            meta=data.get("meta", {})
        )


@router.get("/nearby", response_model=PassengerListResponse)
async def query_passengers_nearby(
    latitude: float = Query(..., ge=-90, le=90, description="Vehicle latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Vehicle longitude"),
    route_id: str = Query(..., description="Route ID to filter"),
    radius_km: float = Query(0.2, ge=0.001, le=10.0, description="Search radius in kilometers"),
    max_results: int = Query(50, ge=1, le=100, description="Maximum passengers to return"),
    status: Optional[str] = Query("WAITING", description="Filter by status")
):
    """
    Query passengers near a location (for conductor visibility).
    
    This endpoint is used by vehicle conductors to find eligible passengers
    within pickup radius of their current position.
    
    Example:
    - GET /api/passengers/nearby?latitude=13.0975&longitude=-59.6139&route_id=gg3pv3z19hhm117v9xth5ezq&radius_km=0.2
    
    Returns passengers sorted by distance (closest first).
    """
    from commuter_service.infrastructure.config import get_config
    from math import radians, cos, sin, asin, sqrt
    
    config = get_config()
    strapi_url = config.infrastructure.strapi_url.rstrip("/")
    
    # Query Strapi for passengers on this route with matching status
    params = {
        "filters[route_id][$eq]": route_id,
        "pagination[limit]": 100  # Get more than needed, filter by distance
    }
    
    if status:
        params["filters[status][$eq]"] = status
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{strapi_url}/api/active-passengers", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Calculate distances and filter by radius
        passengers_with_distance = []
        for item in data.get("data", []):
            p = item
            p_lat = p.get("latitude")
            p_lon = p.get("longitude")
            
            if p_lat is not None and p_lon is not None:
                distance_km = haversine(latitude, longitude, p_lat, p_lon)
                
                if distance_km <= radius_km:
                    # Calculate computed state
                    computed_state = calculate_passenger_state(
                        spawned_at=p.get("spawned_at"),
                        boarded_at=p.get("boarded_at"),
                        alighted_at=p.get("alighted_at"),
                        status=p.get("status")
                    )
                    
                    passenger_response = PassengerResponse(
                        id=p.get("id"),
                        documentId=p.get("documentId"),
                        passenger_id=p.get("passenger_id"),
                        route_id=p.get("route_id"),
                        depot_id=p.get("depot_id"),
                        latitude=p_lat,
                        longitude=p_lon,
                        destination_lat=p.get("destination_lat"),
                        destination_lon=p.get("destination_lon"),
                        destination_name=p.get("destination_name", "Stop"),
                        spawned_at=p.get("spawned_at"),
                        boarded_at=p.get("boarded_at"),
                        alighted_at=p.get("alighted_at"),
                        vehicle_id=p.get("vehicle_id"),
                        status=PassengerStatus(p.get("status", "WAITING")),
                        computed_state=computed_state,
                        createdAt=p.get("createdAt"),
                        updatedAt=p.get("updatedAt")
                    )
                    
                    passengers_with_distance.append((distance_km, passenger_response))
        
        # Sort by distance (closest first) and limit results
        passengers_with_distance.sort(key=lambda x: x[0])
        nearby_passengers = [p for _, p in passengers_with_distance[:max_results]]
        
        return PassengerListResponse(
            data=nearby_passengers,
            meta={
                "pagination": {
                    "total": len(nearby_passengers),
                    "page": 1,
                    "pageSize": len(nearby_passengers)
                },
                "query": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "route_id": route_id,
                    "radius_km": radius_km
                }
            }
        )


@router.get("/{passenger_id}", response_model=PassengerResponse)
async def get_passenger(passenger_id: str):
    """
    Get a single passenger by ID.
    
    Args:
        passenger_id: Passenger document ID or passenger_id field
    """
    from commuter_service.infrastructure.config import get_config
    
    config = get_config()
    strapi_url = config.infrastructure.strapi_url.rstrip("/")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Try as document ID first
        response = await client.get(f"{strapi_url}/api/active-passengers/{passenger_id}")
        
        if response.status_code == 404:
            # Try filtering by passenger_id field
            params = {"filters[passenger_id][$eq]": passenger_id}
            response = await client.get(f"{strapi_url}/api/active-passengers", params=params)
            response.raise_for_status()
            
            data = response.json().get("data", [])
            if not data:
                raise HTTPException(status_code=404, detail=f"Passenger {passenger_id} not found")
            
            p = data[0]
        else:
            response.raise_for_status()
            p = response.json().get("data", {})
        
        # Calculate state
        computed_state = calculate_passenger_state(
            spawned_at=p.get("spawned_at"),
            boarded_at=p.get("boarded_at"),
            alighted_at=p.get("alighted_at"),
            status=p.get("status")
        )
        
        return PassengerResponse(
            id=p.get("id"),
            documentId=p.get("documentId"),
            passenger_id=p.get("passenger_id"),
            route_id=p.get("route_id"),
            depot_id=p.get("depot_id"),
            latitude=p.get("latitude"),
            longitude=p.get("longitude"),
            destination_lat=p.get("destination_lat"),
            destination_lon=p.get("destination_lon"),
            destination_name=p.get("destination_name", "Stop"),
            spawned_at=p.get("spawned_at"),
            boarded_at=p.get("boarded_at"),
            alighted_at=p.get("alighted_at"),
            vehicle_id=p.get("vehicle_id"),
            status=PassengerStatus(p.get("status", "WAITING")),
            computed_state=computed_state,
            createdAt=p.get("createdAt"),
            updatedAt=p.get("updatedAt")
        )


@router.post("", response_model=PassengerResponse, status_code=201)
async def create_passenger(passenger: PassengerCreate):
    """
    Create a new passenger.
    
    This manually creates a passenger (alternative to seeding).
    """
    from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
    from commuter_service.infrastructure.config import get_config
    import uuid
    
    config = get_config()
    repo = PassengerRepository(strapi_url=config.infrastructure.strapi_url)
    await repo.connect()
    
    try:
        # Generate ID if not provided
        if not passenger.passenger_id:
            passenger.passenger_id = f"PASS_{uuid.uuid4().hex[:8].upper()}"
        
        # Insert
        success = await repo.insert_passenger(
            passenger_id=passenger.passenger_id,
            route_id=passenger.route_id,
            latitude=passenger.latitude,
            longitude=passenger.longitude,
            destination_lat=passenger.destination_lat,
            destination_lon=passenger.destination_lon,
            destination_name=passenger.destination_name,
            spawned_at=passenger.spawned_at or datetime.utcnow()
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create passenger")
        
        # Fetch created passenger
        return await get_passenger(passenger.passenger_id)
    
    finally:
        await repo.disconnect()


@router.put("/{passenger_id}", response_model=PassengerResponse)
async def update_passenger(passenger_id: str, updates: PassengerUpdate):
    """
    Update passenger fields.
    
    Updates location, destination, or route assignment.
    Does NOT modify state timestamps - use board/alight endpoints.
    """
    from commuter_service.infrastructure.config import get_config
    
    config = get_config()
    strapi_url = config.infrastructure.strapi_url.rstrip("/")
    
    # Get current passenger
    current = await get_passenger(passenger_id)
    
    # Build update payload
    update_data = {}
    if updates.latitude is not None:
        update_data["latitude"] = updates.latitude
    if updates.longitude is not None:
        update_data["longitude"] = updates.longitude
    if updates.destination_lat is not None:
        update_data["destination_lat"] = updates.destination_lat
    if updates.destination_lon is not None:
        update_data["destination_lon"] = updates.destination_lon
    if updates.destination_name is not None:
        update_data["destination_name"] = updates.destination_name
    if updates.route_id is not None:
        update_data["route_id"] = updates.route_id
    if updates.depot_id is not None:
        update_data["depot_id"] = updates.depot_id
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.put(
            f"{strapi_url}/api/active-passengers/{current.documentId}",
            json={"data": update_data}
        )
        response.raise_for_status()
    
    return await get_passenger(passenger_id)


@router.patch("/{passenger_id}/board", response_model=PassengerResponse)
async def board_passenger(passenger_id: str, request: PassengerBoardRequest):
    """
    Mark passenger as boarded onto a vehicle.
    
    State transition: WAITING → BOARDED
    Uses RouteReservoir.mark_picked_up() for consistency.
    """
    from commuter_service.infrastructure.config import get_config
    from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
    from commuter_service.domain.services.reservoirs.route_reservoir import RouteReservoir
    
    config = get_config()
    
    # Get current passenger
    current = await get_passenger(passenger_id)
    
    # Validate state transition
    new_state = PassengerStatus.BOARDED
    if not validate_state_transition(current.computed_state, new_state):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state transition: {current.computed_state} → {new_state}"
        )
    
    # Use reservoir to ensure cache invalidation and event emission
    passenger_repo = PassengerRepository(strapi_url=config.infrastructure.strapi_url)
    await passenger_repo.connect()
    
    try:
        # Get or create reservoir for this route
        reservoir = RouteReservoir(
            passenger_repository=passenger_repo,
            enable_redis_cache=False
        )
        
        # Mark picked up through reservoir (handles cache + events)
        success = await reservoir.mark_picked_up(
            passenger_id=current.passenger_id,
            vehicle_id=request.vehicle_id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to board passenger")
        
        return await get_passenger(passenger_id)
    
    finally:
        await passenger_repo.disconnect()


@router.patch("/{passenger_id}/alight", response_model=PassengerResponse)
async def alight_passenger(passenger_id: str, request: PassengerAlightRequest):
    """
    Mark passenger as alighted from vehicle.
    
    State transition: BOARDED → ALIGHTED
    Uses RouteReservoir.mark_dropped_off() for consistency.
    """
    from commuter_service.infrastructure.config import get_config
    from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
    from commuter_service.domain.services.reservoirs.route_reservoir import RouteReservoir
    
    config = get_config()
    
    # Get current passenger
    current = await get_passenger(passenger_id)
    
    # Validate state transition
    new_state = PassengerStatus.ALIGHTED
    if not validate_state_transition(current.computed_state, new_state):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state transition: {current.computed_state} → {new_state}"
        )
    
    # Use reservoir to ensure cache invalidation and event emission
    passenger_repo = PassengerRepository(strapi_url=config.infrastructure.strapi_url)
    await passenger_repo.connect()
    
    try:
        reservoir = RouteReservoir(
            passenger_repository=passenger_repo,
            enable_redis_cache=False
        )
        
        # Mark dropped off through reservoir
        success = await reservoir.mark_dropped_off(passenger_id=current.passenger_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to alight passenger")
        
        return await get_passenger(passenger_id)
    
    finally:
        await passenger_repo.disconnect()


@router.patch("/{passenger_id}/cancel", response_model=PassengerResponse)
async def cancel_passenger(passenger_id: str):
    """
    Cancel a passenger.
    
    Allowed from WAITING or BOARDED states.
    """
    from commuter_service.infrastructure.config import get_config
    
    config = get_config()
    strapi_url = config.infrastructure.strapi_url.rstrip("/")
    
    # Get current passenger
    current = await get_passenger(passenger_id)
    
    # Validate
    if current.computed_state == PassengerStatus.ALIGHTED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel alighted passenger"
        )
    
    # Update
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.put(
            f"{strapi_url}/api/active-passengers/{current.documentId}",
            json={"data": {"status": "CANCELLED"}}
        )
        response.raise_for_status()
    
    return await get_passenger(passenger_id)


@router.delete("/{passenger_id}")
async def delete_passenger(passenger_id: str):
    """
    Delete a passenger permanently.
    
    Use with caution - this is irreversible.
    """
    from commuter_service.infrastructure.config import get_config
    
    config = get_config()
    strapi_url = config.infrastructure.strapi_url.rstrip("/")
    
    # Get passenger to get document ID
    current = await get_passenger(passenger_id)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.delete(
            f"{strapi_url}/api/active-passengers/{current.documentId}"
        )
        
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail="Failed to delete passenger")
    
    return {"deleted": True, "passenger_id": passenger_id}
