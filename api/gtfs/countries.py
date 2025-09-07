"""
Country API Endpoints
=====================
FastAPI endpoints for Country CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..schemas.country import Country, CountryCreate, CountryUpdate, CountryList
from ...models.gtfs.country import Country as CountryModel

router = APIRouter(prefix="/countries", tags=["Countries"])

@router.post("/", response_model=Country)
def create_country(
    country: CountryCreate,
    db: Session = Depends(get_db)
):
    """Create a new country"""
    db_country = CountryModel(**country.model_dump())
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return db_country

@router.get("/", response_model=CountryList)
def list_countries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all countries with pagination"""
    countries = db.query(CountryModel).offset(skip).limit(limit).all()
    total = db.query(CountryModel).count()
    return CountryList(countries=countries, total=total)

@router.get("/{country_id}", response_model=Country)
def get_country(
    country_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific country by ID"""
    country = db.query(CountryModel).filter(CountryModel.country_id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@router.put("/{country_id}", response_model=Country)
def update_country(
    country_id: UUID,
    country_update: CountryUpdate,
    db: Session = Depends(get_db)
):
    """Update a country"""
    db_country = db.query(CountryModel).filter(CountryModel.country_id == country_id).first()
    if not db_country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    update_data = country_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_country, field, value)
    
    db.commit()
    db.refresh(db_country)
    return db_country

@router.delete("/{country_id}")
def delete_country(
    country_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a country"""
    db_country = db.query(CountryModel).filter(CountryModel.country_id == country_id).first()
    if not db_country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    db.delete(db_country)
    db.commit()
    return {"message": "Country deleted successfully"}
