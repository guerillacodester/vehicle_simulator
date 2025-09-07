"""
Timetable API Endpoints
======================
CRUD operations for Timetable model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from models.gtfs import Timetable

router = APIRouter()

@router.post("/", response_model=dict)
def create_timetable(
    timetable_data: dict,
    db: Session = Depends(get_db)
):
    """Create a new timetable entry"""
    db_timetable = Timetable(**timetable_data)
    db.add(db_timetable)
    db.commit()
    db.refresh(db_timetable)
    return {
        "message": "Timetable created successfully", 
        "timetable_id": str(db_timetable.timetable_id)
    }

@router.get("/", response_model=List[dict])
def list_timetables(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    vehicle_id: Optional[UUID] = Query(None),
    route_id: Optional[UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """List timetables with optional filtering"""
    query = db.query(Timetable)
    
    if vehicle_id:
        query = query.filter(Timetable.vehicle_id == vehicle_id)
    if route_id:
        query = query.filter(Timetable.route_id == route_id)
    if date_from:
        query = query.filter(Timetable.departure_time >= date_from)
    if date_to:
        query = query.filter(Timetable.departure_time <= date_to)
    
    timetables = query.offset(skip).limit(limit).all()
    return [
        {
            "timetable_id": str(t.timetable_id),
            "vehicle_id": str(t.vehicle_id),
            "route_id": str(t.route_id),
            "departure_time": t.departure_time.isoformat() if t.departure_time else None,
            "arrival_time": t.arrival_time.isoformat() if t.arrival_time else None,
            "notes": t.notes
        } for t in timetables
    ]

@router.get("/{timetable_id}", response_model=dict)
def get_timetable(
    timetable_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific timetable by ID"""
    timetable = db.query(Timetable).filter(Timetable.timetable_id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    return {
        "timetable_id": str(timetable.timetable_id),
        "vehicle_id": str(timetable.vehicle_id),
        "route_id": str(timetable.route_id),
        "departure_time": timetable.departure_time.isoformat() if timetable.departure_time else None,
        "arrival_time": timetable.arrival_time.isoformat() if timetable.arrival_time else None,
        "notes": timetable.notes,
        "created_at": timetable.created_at.isoformat() if timetable.created_at else None,
        "updated_at": timetable.updated_at.isoformat() if timetable.updated_at else None
    }

@router.put("/{timetable_id}", response_model=dict)
def update_timetable(
    timetable_id: UUID,
    timetable_update: dict,
    db: Session = Depends(get_db)
):
    """Update a timetable"""
    timetable = db.query(Timetable).filter(Timetable.timetable_id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    for field, value in timetable_update.items():
        if hasattr(timetable, field):
            setattr(timetable, field, value)
    
    db.commit()
    db.refresh(timetable)
    return {"message": "Timetable updated successfully"}

@router.delete("/{timetable_id}")
def delete_timetable(
    timetable_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a timetable"""
    timetable = db.query(Timetable).filter(Timetable.timetable_id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    db.delete(timetable)
    db.commit()
    return {"message": "Timetable deleted successfully"}

@router.get("/vehicle/{vehicle_id}/schedule", response_model=List[dict])
def get_vehicle_schedule(
    vehicle_id: UUID,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get schedule for a specific vehicle"""
    query = db.query(Timetable).filter(Timetable.vehicle_id == vehicle_id)
    
    if date_from:
        query = query.filter(Timetable.departure_time >= date_from)
    if date_to:
        query = query.filter(Timetable.departure_time <= date_to)
    
    schedule = query.order_by(Timetable.departure_time).all()
    return [
        {
            "timetable_id": str(s.timetable_id),
            "route_id": str(s.route_id),
            "departure_time": s.departure_time.isoformat() if s.departure_time else None,
            "arrival_time": s.arrival_time.isoformat() if s.arrival_time else None,
            "notes": s.notes
        } for s in schedule
    ]

@router.get("/route/{route_id}/schedule", response_model=List[dict])
def get_route_schedule(
    route_id: UUID,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get schedule for a specific route"""
    query = db.query(Timetable).filter(Timetable.route_id == route_id)
    
    if date_from:
        query = query.filter(Timetable.departure_time >= date_from)
    if date_to:
        query = query.filter(Timetable.departure_time <= date_to)
    
    schedule = query.order_by(Timetable.departure_time).all()
    return [
        {
            "timetable_id": str(s.timetable_id),
            "vehicle_id": str(s.vehicle_id),
            "departure_time": s.departure_time.isoformat() if s.departure_time else None,
            "arrival_time": s.arrival_time.isoformat() if s.arrival_time else None,
            "notes": s.notes
        } for s in schedule
    ]
