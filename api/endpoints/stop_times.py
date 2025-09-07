"""
StopTime API Endpoints
=====================
CRUD operations for StopTime model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ...models.gtfs import StopTime

router = APIRouter()

@router.post("/", response_model=dict)
def create_stop_time(
    stop_time_data: dict,
    db: Session = Depends(get_db)
):
    """Create a new stop time"""
    db_stop_time = StopTime(**stop_time_data)
    db.add(db_stop_time)
    db.commit()
    db.refresh(db_stop_time)
    return {"message": "Stop time created successfully"}

@router.get("/", response_model=List[dict])
def list_stop_times(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    trip_id: Optional[UUID] = Query(None),
    stop_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List stop times with optional filtering"""
    query = db.query(StopTime)
    
    if trip_id:
        query = query.filter(StopTime.trip_id == trip_id)
    if stop_id:
        query = query.filter(StopTime.stop_id == stop_id)
    
    stop_times = query.offset(skip).limit(limit).all()
    return [
        {
            "trip_id": str(st.trip_id),
            "stop_id": str(st.stop_id),
            "stop_sequence": st.stop_sequence,
            "arrival_time": str(st.arrival_time),
            "departure_time": str(st.departure_time)
        } for st in stop_times
    ]

@router.get("/trip/{trip_id}", response_model=List[dict])
def get_trip_stop_times(
    trip_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all stop times for a specific trip, ordered by sequence"""
    stop_times = db.query(StopTime).filter(
        StopTime.trip_id == trip_id
    ).order_by(StopTime.stop_sequence).all()
    
    return [
        {
            "trip_id": str(st.trip_id),
            "stop_id": str(st.stop_id),
            "stop_sequence": st.stop_sequence,
            "arrival_time": str(st.arrival_time),
            "departure_time": str(st.departure_time)
        } for st in stop_times
    ]

@router.get("/{trip_id}/{stop_id}/{stop_sequence}", response_model=dict)
def get_stop_time(
    trip_id: UUID,
    stop_id: UUID,
    stop_sequence: int,
    db: Session = Depends(get_db)
):
    """Get a specific stop time by composite key"""
    stop_time = db.query(StopTime).filter(
        StopTime.trip_id == trip_id,
        StopTime.stop_id == stop_id,
        StopTime.stop_sequence == stop_sequence
    ).first()
    
    if not stop_time:
        raise HTTPException(status_code=404, detail="Stop time not found")
    
    return {
        "trip_id": str(stop_time.trip_id),
        "stop_id": str(stop_time.stop_id),
        "stop_sequence": stop_time.stop_sequence,
        "arrival_time": str(stop_time.arrival_time),
        "departure_time": str(stop_time.departure_time)
    }

@router.put("/{trip_id}/{stop_id}/{stop_sequence}", response_model=dict)
def update_stop_time(
    trip_id: UUID,
    stop_id: UUID,
    stop_sequence: int,
    stop_time_update: dict,
    db: Session = Depends(get_db)
):
    """Update a stop time"""
    stop_time = db.query(StopTime).filter(
        StopTime.trip_id == trip_id,
        StopTime.stop_id == stop_id,
        StopTime.stop_sequence == stop_sequence
    ).first()
    
    if not stop_time:
        raise HTTPException(status_code=404, detail="Stop time not found")
    
    for field, value in stop_time_update.items():
        if hasattr(stop_time, field):
            setattr(stop_time, field, value)
    
    db.commit()
    db.refresh(stop_time)
    return {"message": "Stop time updated successfully"}

@router.delete("/{trip_id}/{stop_id}/{stop_sequence}")
def delete_stop_time(
    trip_id: UUID,
    stop_id: UUID,
    stop_sequence: int,
    db: Session = Depends(get_db)
):
    """Delete a stop time"""
    stop_time = db.query(StopTime).filter(
        StopTime.trip_id == trip_id,
        StopTime.stop_id == stop_id,
        StopTime.stop_sequence == stop_sequence
    ).first()
    
    if not stop_time:
        raise HTTPException(status_code=404, detail="Stop time not found")
    
    db.delete(stop_time)
    db.commit()
    return {"message": "Stop time deleted successfully"}
