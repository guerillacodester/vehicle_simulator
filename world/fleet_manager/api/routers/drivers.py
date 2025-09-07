"""
Driver CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db
from ...models.driver import Driver as DriverModel
from ..schemas.driver import Driver, DriverCreate, DriverUpdate

router = APIRouter(
    prefix="/drivers",
    tags=["drivers"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Driver)
def create_driver(
    driver: DriverCreate,
    db: Session = Depends(get_db)
):
    """Create a new driver"""
    db_driver = DriverModel(**driver.dict())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver

@router.get("/", response_model=List[Driver])
def read_drivers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all drivers with pagination"""
    drivers = db.query(DriverModel).offset(skip).limit(limit).all()
    return drivers

@router.get("/{driver_id}", response_model=Driver)
def read_driver(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific driver by ID"""
    driver = db.query(DriverModel).filter(DriverModel.driver_id == driver_id).first()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@router.get("/depot/{depot_id}", response_model=List[Driver])
def read_drivers_by_depot(
    depot_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all drivers for a specific depot"""
    drivers = db.query(DriverModel).filter(DriverModel.depot_id == depot_id).all()
    return drivers

@router.get("/license/{license_number}", response_model=Driver)
def read_driver_by_license(
    license_number: str,
    db: Session = Depends(get_db)
):
    """Get a driver by license number"""
    driver = db.query(DriverModel).filter(DriverModel.license_number == license_number).first()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@router.put("/{driver_id}", response_model=Driver)
def update_driver(
    driver_id: UUID,
    driver: DriverUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific driver"""
    db_driver = db.query(DriverModel).filter(DriverModel.driver_id == driver_id).first()
    if db_driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    update_data = driver.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_driver, field, value)
    
    db.commit()
    db.refresh(db_driver)
    return db_driver

@router.delete("/{driver_id}")
def delete_driver(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific driver"""
    driver = db.query(DriverModel).filter(DriverModel.driver_id == driver_id).first()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    db.delete(driver)
    db.commit()
    return {"message": "Driver deleted successfully"}
