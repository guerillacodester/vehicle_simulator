"""
Frequency API Endpoints
======================
CRUD operations for Frequency model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ...models.gtfs import Frequency

router = APIRouter()

@router.post("/", response_model=dict)
def create_frequency(frequency_data: dict, db: Session = Depends(get_db)):
    """Create a new frequency"""
    db_frequency = Frequency(**frequency_data)
    db.add(db_frequency)
    db.commit()
    db.refresh(db_frequency)
    return {"message": "Frequency created successfully", "frequency_id": str(db_frequency.frequency_id)}

@router.get("/", response_model=List[dict])
def list_frequencies(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
    service_id: Optional[UUID] = Query(None), route_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List frequencies with optional filtering"""
    query = db.query(Frequency)
    if service_id: query = query.filter(Frequency.service_id == service_id)
    if route_id: query = query.filter(Frequency.route_id == route_id)
    frequencies = query.offset(skip).limit(limit).all()
    return [{"frequency_id": str(f.frequency_id), "service_id": str(f.service_id), "route_id": str(f.route_id), "start_time": str(f.start_time), "end_time": str(f.end_time), "headway_s": f.headway_s} for f in frequencies]

@router.get("/{frequency_id}", response_model=dict)
def get_frequency(frequency_id: UUID, db: Session = Depends(get_db)):
    """Get a specific frequency by ID"""
    frequency = db.query(Frequency).filter(Frequency.frequency_id == frequency_id).first()
    if not frequency: raise HTTPException(status_code=404, detail="Frequency not found")
    return {"frequency_id": str(frequency.frequency_id), "service_id": str(frequency.service_id), "route_id": str(frequency.route_id), "start_time": str(frequency.start_time), "end_time": str(frequency.end_time), "headway_s": frequency.headway_s}

@router.delete("/{frequency_id}")
def delete_frequency(frequency_id: UUID, db: Session = Depends(get_db)):
    """Delete a frequency"""
    frequency = db.query(Frequency).filter(Frequency.frequency_id == frequency_id).first()
    if not frequency: raise HTTPException(status_code=404, detail="Frequency not found")
    db.delete(frequency)
    db.commit()
    return {"message": "Frequency deleted successfully"}
