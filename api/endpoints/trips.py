"""
Trip API Endpoints
=================
CRUD operations for Trip model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..schemas.trip import TripCreate, TripUpdate, TripResponse
from ...models.gtfs import Trip

router = APIRouter()

@router.post("/", response_model=TripResponse)
def create_trip(
    trip: TripCreate,
    db: Session = Depends(get_db)
):
    """Create a new trip"""
    db_trip = Trip(**trip.model_dump())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.get("/", response_model=List[TripResponse])
def list_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    route_id: Optional[UUID] = Query(None),
    service_id: Optional[UUID] = Query(None),
    block_id: Optional[UUID] = Query(None),
    direction_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """List trips with optional filtering"""
    query = db.query(Trip)
    
    if route_id:
        query = query.filter(Trip.route_id == route_id)
    if service_id:
        query = query.filter(Trip.service_id == service_id)
    if block_id:
        query = query.filter(Trip.block_id == block_id)
    if direction_id is not None:
        query = query.filter(Trip.direction_id == direction_id)
    
    trips = query.offset(skip).limit(limit).all()
    return trips

@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific trip by ID"""
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.put("/{trip_id}", response_model=TripResponse)
def update_trip(
    trip_id: UUID,
    trip_update: TripUpdate,
    db: Session = Depends(get_db)
):
    """Update a trip"""
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    for field, value in trip_update.model_dump(exclude_unset=True).items():
        setattr(trip, field, value)
    
    db.commit()
    db.refresh(trip)
    return trip

@router.delete("/{trip_id}")
def delete_trip(
    trip_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a trip"""
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db.delete(trip)
    db.commit()
    return {"message": "Trip deleted successfully"}
