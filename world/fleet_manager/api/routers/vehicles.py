"""
Vehicle CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db
from ...models.vehicle import Vehicle as VehicleModel
from ..schemas.vehicle import Vehicle, VehicleCreate, VehicleUpdate

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Vehicle)
def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db)
):
    """Create a new vehicle"""
    db_vehicle = VehicleModel(**vehicle.dict())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.get("/", response_model=List[Vehicle])
def read_vehicles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all vehicles with pagination"""
    vehicles = db.query(VehicleModel).offset(skip).limit(limit).all()
    return vehicles

@router.get("/{vehicle_id}", response_model=Vehicle)
def read_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific vehicle by ID"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.vehicle_id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.get("/depot/{depot_id}", response_model=List[Vehicle])
def read_vehicles_by_depot(
    depot_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all vehicles for a specific depot"""
    vehicles = db.query(VehicleModel).filter(VehicleModel.depot_id == depot_id).all()
    return vehicles

@router.get("/status/{status}", response_model=List[Vehicle])
def read_vehicles_by_status(
    status: str,
    db: Session = Depends(get_db)
):
    """Get all vehicles with a specific status"""
    vehicles = db.query(VehicleModel).filter(VehicleModel.status == status).all()
    return vehicles

@router.get("/license/{license_plate}", response_model=Vehicle)
def read_vehicle_by_license(
    license_plate: str,
    db: Session = Depends(get_db)
):
    """Get a vehicle by license plate"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.license_plate == license_plate).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.put("/{vehicle_id}", response_model=Vehicle)
def update_vehicle(
    vehicle_id: UUID,
    vehicle: VehicleUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific vehicle"""
    db_vehicle = db.query(VehicleModel).filter(VehicleModel.vehicle_id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    update_data = vehicle.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)
    
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.delete("/{vehicle_id}")
def delete_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific vehicle"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.vehicle_id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    db.delete(vehicle)
    db.commit()
    return {"message": "Vehicle deleted successfully"}
