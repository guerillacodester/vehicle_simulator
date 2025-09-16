"""
Country CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db
from ...models.country import Country as CountryModel
from ..schemas.country import Country, CountryCreate, CountryUpdate

router = APIRouter(
    prefix="/countries",
    tags=["countries"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Country)
def create_country(
    country: CountryCreate,
    db: Session = Depends(get_db)
):
    """Create a new country"""
    db_country = CountryModel(**country.dict())
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return db_country

@router.get("/", response_model=List[Country])
def read_countries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all countries with pagination"""
    countries = db.query(CountryModel).offset(skip).limit(limit).all()
    return countries

@router.get("/{country_id}", response_model=Country)
def read_country(
    country_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific country by ID"""
    country = db.query(CountryModel).filter(CountryModel.country_id == country_id).first()
    if country is None:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@router.get("/code/{country_code}", response_model=Country)
def read_country_by_code(
    country_code: str,
    db: Session = Depends(get_db)
):
    """Get a specific country by country code"""
    country = db.query(CountryModel).filter(CountryModel.country_code == country_code).first()
    if country is None:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@router.put("/{country_id}", response_model=Country)
def update_country(
    country_id: UUID,
    country: CountryUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific country"""
    db_country = db.query(CountryModel).filter(CountryModel.country_id == country_id).first()
    if db_country is None:
        raise HTTPException(status_code=404, detail="Country not found")
    
    update_data = country.dict(exclude_unset=True)
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
    """Delete a specific country"""
    country = db.query(CountryModel).filter(CountryModel.country_id == country_id).first()
    if country is None:
        raise HTTPException(status_code=404, detail="Country not found")
    
    db.delete(country)
    db.commit()
    return {"message": "Country deleted successfully"}
