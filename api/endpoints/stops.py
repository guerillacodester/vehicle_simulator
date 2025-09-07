"""
Stop API Endpoints
=================
CRUD operations for Stop model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..schemas.stop import StopCreate, StopUpdate, StopResponse
from models.gtfs import Stop

router = APIRouter()

@router.post("/", response_model=StopResponse)
def create_stop(
    stop: StopCreate,
    db: Session = Depends(get_db)
):
    """Create a new stop"""
    db_stop = Stop(**stop.model_dump())
    db.add(db_stop)
    db.commit()
    db.refresh(db_stop)
    return db_stop

@router.get("/", response_model=List[StopResponse])
def list_stops(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country_id: Optional[UUID] = Query(None),
    zone_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List stops with optional filtering"""
    query = db.query(Stop)
    
    if country_id:
        query = query.filter(Stop.country_id == country_id)
    if zone_id:
        query = query.filter(Stop.zone_id == zone_id)
    
    stops = query.offset(skip).limit(limit).all()
    return stops

@router.get("/{stop_id}", response_model=StopResponse)
def get_stop(
    stop_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific stop by ID"""
    stop = db.query(Stop).filter(Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop

@router.put("/{stop_id}", response_model=StopResponse)
def update_stop(
    stop_id: UUID,
    stop_update: StopUpdate,
    db: Session = Depends(get_db)
):
    """Update a stop"""
    stop = db.query(Stop).filter(Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    for field, value in stop_update.model_dump(exclude_unset=True).items():
        setattr(stop, field, value)
    
    db.commit()
    db.refresh(stop)
    return stop

@router.delete("/{stop_id}")
def delete_stop(
    stop_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a stop"""
    stop = db.query(Stop).filter(Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    db.delete(stop)
    db.commit()
    return {"message": "Stop deleted successfully"}
