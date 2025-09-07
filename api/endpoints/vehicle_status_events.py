"""
VehicleStatusEvent API Endpoints
===============================
CRUD operations for VehicleStatusEvent model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ...models.gtfs import VehicleStatusEvent
from ...models.gtfs.enums import VehicleStatusEnum

router = APIRouter()

@router.post("/", response_model=dict)
def create_vehicle_status_event(event_data: dict, db: Session = Depends(get_db)):
    """Create a new vehicle status event"""
    db_event = VehicleStatusEvent(**event_data)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {"message": "Vehicle status event created successfully", "event_id": str(db_event.event_id)}

@router.get("/", response_model=List[dict])
def list_vehicle_status_events(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
    vehicle_id: Optional[UUID] = Query(None), status: Optional[VehicleStatusEnum] = Query(None),
    db: Session = Depends(get_db)
):
    """List vehicle status events with optional filtering"""
    query = db.query(VehicleStatusEvent)
    if vehicle_id: query = query.filter(VehicleStatusEvent.vehicle_id == vehicle_id)
    if status: query = query.filter(VehicleStatusEvent.status == status)
    events = query.order_by(VehicleStatusEvent.event_time.desc()).offset(skip).limit(limit).all()
    return [{"event_id": str(e.event_id), "vehicle_id": str(e.vehicle_id), "status": e.status.value, "event_time": e.event_time.isoformat() if e.event_time else None, "notes": e.notes} for e in events]

@router.get("/{event_id}", response_model=dict)
def get_vehicle_status_event(event_id: UUID, db: Session = Depends(get_db)):
    """Get a specific vehicle status event by ID"""
    event = db.query(VehicleStatusEvent).filter(VehicleStatusEvent.event_id == event_id).first()
    if not event: raise HTTPException(status_code=404, detail="Vehicle status event not found")
    return {"event_id": str(event.event_id), "vehicle_id": str(event.vehicle_id), "status": event.status.value, "event_time": event.event_time.isoformat() if event.event_time else None, "notes": event.notes}

@router.delete("/{event_id}")
def delete_vehicle_status_event(event_id: UUID, db: Session = Depends(get_db)):
    """Delete a vehicle status event"""
    event = db.query(VehicleStatusEvent).filter(VehicleStatusEvent.event_id == event_id).first()
    if not event: raise HTTPException(status_code=404, detail="Vehicle status event not found")
    db.delete(event)
    db.commit()
    return {"message": "Vehicle status event deleted successfully"}
