"""
Vehicle API Endpoints
====================
CRUD operations for Vehicle model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from ...models.gtfs import Vehicle
from ...models.gtfs.enums import VehicleStatusEnum

router = APIRouter()

@router.post("/", response_model=VehicleResponse)
def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db)
):
    """Create a new vehicle"""
    db_vehicle = Vehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.get("/", response_model=List[VehicleResponse])
def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country_id: Optional[UUID] = Query(None),
    depot_id: Optional[UUID] = Query(None),
    status: Optional[VehicleStatusEnum] = Query(None),
    db: Session = Depends(get_db)
):
    """List vehicles with optional filtering"""
    query = db.query(Vehicle)
    
    if country_id:
        query = query.filter(Vehicle.country_id == country_id)
    if depot_id:
        query = query.filter(Vehicle.home_depot_id == depot_id)
    if status:
        query = query.filter(Vehicle.status == status)
    
    vehicles = query.offset(skip).limit(limit).all()
    return vehicles

@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific vehicle by ID"""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: UUID,
    vehicle_update: VehicleUpdate,
    db: Session = Depends(get_db)
):
    """Update a vehicle"""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    for field, value in vehicle_update.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    
    db.commit()
    db.refresh(vehicle)
    return vehicle

@router.delete("/{vehicle_id}")
def delete_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a vehicle"""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    db.delete(vehicle)
    db.commit()
    return {"message": "Vehicle deleted successfully"}

@router.patch("/{vehicle_id}/status")
def update_vehicle_status(
    vehicle_id: UUID,
    status: VehicleStatusEnum,
    db: Session = Depends(get_db)
):
    """Update vehicle status"""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    vehicle.status = status
    db.commit()
    db.refresh(vehicle)
    return {"message": f"Vehicle status updated to {status.value}"}
