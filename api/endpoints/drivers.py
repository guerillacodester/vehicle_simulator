"""
Driver API Endpoints
===================
CRUD operations for Driver model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from models.gtfs import Driver

router = APIRouter()

@router.post("/", response_model=DriverResponse)
def create_driver(
    driver: DriverCreate,
    db: Session = Depends(get_db)
):
    """Create a new driver"""
    db_driver = Driver(**driver.model_dump())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver

@router.get("/", response_model=List[DriverResponse])
def list_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country_id: Optional[UUID] = Query(None),
    depot_id: Optional[UUID] = Query(None),
    employment_status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List drivers with optional filtering"""
    query = db.query(Driver)
    
    if country_id:
        query = query.filter(Driver.country_id == country_id)
    if depot_id:
        query = query.filter(Driver.home_depot_id == depot_id)
    if employment_status:
        query = query.filter(Driver.employment_status == employment_status)
    
    drivers = query.offset(skip).limit(limit).all()
    return drivers

@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific driver by ID"""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: UUID,
    driver_update: DriverUpdate,
    db: Session = Depends(get_db)
):
    """Update a driver"""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    for field, value in driver_update.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    
    db.commit()
    db.refresh(driver)
    return driver

@router.delete("/{driver_id}")
def delete_driver(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a driver"""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    db.delete(driver)
    db.commit()
    return {"message": "Driver deleted successfully"}
