"""
Trip CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db
from ...models.trip import Trip as TripModel
from ..schemas.trip import Trip, TripCreate, TripUpdate

router = APIRouter(
    prefix="/trips",
    tags=["trips"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Trip)
def create_trip(
    trip: TripCreate,
    db: Session = Depends(get_db)
):
    """Create a new trip"""
    db_trip = TripModel(**trip.dict())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.get("/", response_model=List[Trip])
def read_trips(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all trips with pagination"""
    trips = db.query(TripModel).offset(skip).limit(limit).all()
    return trips

@router.get("/{trip_id}", response_model=Trip)
def read_trip(
    trip_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific trip by ID"""
    trip = db.query(TripModel).filter(TripModel.trip_id == trip_id).first()
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.get("/route/{route_id}", response_model=List[Trip])
def read_trips_by_route(
    route_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all trips for a specific route"""
    trips = db.query(TripModel).filter(TripModel.route_id == route_id).all()
    return trips

@router.get("/service/{service_id}", response_model=List[Trip])
def read_trips_by_service(
    service_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all trips for a specific service"""
    trips = db.query(TripModel).filter(TripModel.service_id == service_id).all()
    return trips

@router.get("/block/{block_id}", response_model=List[Trip])
def read_trips_by_block(
    block_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all trips for a specific block"""
    trips = db.query(TripModel).filter(TripModel.block_id == block_id).all()
    return trips

@router.put("/{trip_id}", response_model=Trip)
def update_trip(
    trip_id: UUID,
    trip: TripUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific trip"""
    db_trip = db.query(TripModel).filter(TripModel.trip_id == trip_id).first()
    if db_trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    update_data = trip.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_trip, field, value)
    
    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.delete("/{trip_id}")
def delete_trip(
    trip_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific trip"""
    trip = db.query(TripModel).filter(TripModel.trip_id == trip_id).first()
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db.delete(trip)
    db.commit()
    return {"message": "Trip deleted successfully"}
