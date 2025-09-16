"""
Driver CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db
from ...models.driver import Driver as DriverModel
from ..schemas.driver import Driver, DriverCreate, DriverUpdate, DriverPublic, DriverPublicCreate, DriverPublicUpdate

router = APIRouter(
    prefix="/drivers",
    tags=["drivers"],
    responses={404: {"description": "Not found"}},
)



@router.get("/public", response_model=List[DriverPublic])
def read_drivers_public(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all drivers without UUIDs for enhanced security"""
    drivers = db.query(DriverModel).offset(skip).limit(limit).all()
    # Convert to public schema (excludes UUIDs)
    return [DriverPublic(
        name=driver.name,
        license_no=driver.license_no,
        employment_status=driver.employment_status
    ) for driver in drivers]

@router.post("/public", response_model=DriverPublic)
def create_driver_public(
    driver: DriverPublicCreate,
    db: Session = Depends(get_db)
):
    """Create a new driver using PUBLIC API with business identifiers only - NO UUIDs"""
    from ...models.country import Country as CountryModel
    
    # Look up country UUID from business identifier (internal use only)
    country_id = None
    if driver.country_code:
        country = db.query(CountryModel).filter(CountryModel.code == driver.country_code).first()
        if country:
            country_id = country.country_id
        else:
            raise HTTPException(status_code=400, detail=f"Country code '{driver.country_code}' not found")
    
    # Check if license number already exists
    existing_driver = db.query(DriverModel).filter(DriverModel.license_no == driver.license_no).first()
    if existing_driver:
        raise HTTPException(status_code=400, detail=f"Driver with license {driver.license_no} already exists")
    
    # Create driver with internal UUID (hidden from response)
    db_driver = DriverModel(
        name=driver.name,
        license_no=driver.license_no,
        employment_status=driver.employment_status,
        phone=driver.phone,
        email=driver.email,
        address=driver.address,
        country_id=country_id
    )
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    
    # Return public schema (no UUIDs)
    return DriverPublic(
        name=db_driver.name,
        license_no=db_driver.license_no,
        employment_status=db_driver.employment_status
    )

@router.get("/public/{license_no}", response_model=DriverPublic)
def read_driver_public(
    license_no: str,
    db: Session = Depends(get_db)
):
    """Get a specific driver by license number - PUBLIC API with NO UUIDs"""
    driver = db.query(DriverModel).filter(DriverModel.license_no == license_no).first()
    if driver is None:
        raise HTTPException(status_code=404, detail=f"Driver with license {license_no} not found")
    
    return DriverPublic(
        name=driver.name,
        license_no=driver.license_no,
        employment_status=driver.employment_status
    )

@router.put("/public/{license_no}", response_model=DriverPublic)
def update_driver_public(
    license_no: str,
    driver_update: DriverPublicUpdate,
    db: Session = Depends(get_db)
):
    """Update a driver using PUBLIC API with business identifiers only - NO UUIDs"""
    # Find driver by license number
    db_driver = db.query(DriverModel).filter(DriverModel.license_no == license_no).first()
    if db_driver is None:
        raise HTTPException(status_code=404, detail=f"Driver with license {license_no} not found")
    
    # Update fields
    if driver_update.name is not None:
        db_driver.name = driver_update.name
    if driver_update.employment_status is not None:
        db_driver.employment_status = driver_update.employment_status
    if driver_update.phone is not None:
        db_driver.phone = driver_update.phone
    if driver_update.email is not None:
        db_driver.email = driver_update.email
    if driver_update.address is not None:
        db_driver.address = driver_update.address
    
    db.commit()
    db.refresh(db_driver)
    
    # Return public schema (no UUIDs)
    return DriverPublic(
        name=db_driver.name,
        license_no=db_driver.license_no,
        employment_status=db_driver.employment_status
    )

@router.delete("/public/{license_no}")
def delete_driver_public(
    license_no: str,
    db: Session = Depends(get_db)
):
    """Delete a driver using PUBLIC API with business identifier - NO UUIDs"""
    db_driver = db.query(DriverModel).filter(DriverModel.license_no == license_no).first()
    if db_driver is None:
        raise HTTPException(status_code=404, detail=f"Driver with license {license_no} not found")
    
    db.delete(db_driver)
    db.commit()
    return {"message": f"Driver with license {license_no} deleted successfully"}

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
