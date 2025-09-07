"""
Country API Endpoints
====================
CRUD operations for Country model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..schemas.country import CountryCreate, CountryUpdate, CountryResponse
from ...models.gtfs import Country

router = APIRouter()

@router.post("/", response_model=CountryResponse)
def create_country(
    country: CountryCreate,
    db: Session = Depends(get_db)
):
    """Create a new country"""
    db_country = Country(**country.model_dump())
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return db_country

@router.get("/", response_model=List[CountryResponse])
def list_countries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all countries with pagination"""
    countries = db.query(Country).offset(skip).limit(limit).all()
    return countries

@router.get("/{country_id}", response_model=CountryResponse)
def get_country(
    country_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific country by ID"""
    country = db.query(Country).filter(Country.country_id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@router.put("/{country_id}", response_model=CountryResponse)
def update_country(
    country_id: UUID,
    country_update: CountryUpdate,
    db: Session = Depends(get_db)
):
    """Update a country"""
    country = db.query(Country).filter(Country.country_id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    for field, value in country_update.model_dump(exclude_unset=True).items():
        setattr(country, field, value)
    
    db.commit()
    db.refresh(country)
    return country

@router.delete("/{country_id}")
def delete_country(
    country_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a country"""
    country = db.query(Country).filter(Country.country_id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    db.delete(country)
    db.commit()
    return {"message": "Country deleted successfully"}
