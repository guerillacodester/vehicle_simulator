"""
Stop CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_X, ST_Y, ST_Distance, ST_GeomFromText

from ..dependencies import get_db
from ...models.stop import Stop as StopModel
from ..schemas.stop import Stop, StopCreate, StopUpdate

router = APIRouter(
    prefix="/stops",
    tags=["stops"],
    responses={404: {"description": "Not found"}},
)

def stop_to_dict(stop_obj, db_session):
    """Convert Stop model to dictionary with lat/lon extracted from geometry"""
    # Query coordinates from geometry
    coords = db_session.query(
        ST_Y(stop_obj.location).label('latitude'),
        ST_X(stop_obj.location).label('longitude')
    ).filter(StopModel.stop_id == stop_obj.stop_id).first()
    
    return {
        "stop_id": stop_obj.stop_id,
        "country_id": stop_obj.country_id,
        "code": stop_obj.code,
        "name": stop_obj.name,
        "latitude": float(coords.latitude) if coords else 0.0,
        "longitude": float(coords.longitude) if coords else 0.0,
        "zone_id": stop_obj.zone_id,
        "created_at": stop_obj.created_at
    }

@router.post("/", response_model=Stop)
def create_stop(
    stop: StopCreate,
    db: Session = Depends(get_db)
):
    """Create a new stop"""
    # Convert latitude/longitude to PostGIS geometry
    stop_data = stop.dict()
    latitude = stop_data.pop("latitude")
    longitude = stop_data.pop("longitude")
    
    # Create WKT point geometry
    location = WKTElement(f'POINT({longitude} {latitude})', srid=4326)
    
    db_stop = StopModel(**stop_data, location=location)
    db.add(db_stop)
    db.commit()
    db.refresh(db_stop)
    return stop_to_dict(db_stop, db)

@router.get("/", response_model=List[Stop])
def read_stops(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all stops with pagination"""
    stops = db.query(StopModel).offset(skip).limit(limit).all()
    return [stop_to_dict(stop, db) for stop in stops]

@router.get("/{stop_id}", response_model=Stop)
def read_stop(
    stop_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific stop by ID"""
    stop = db.query(StopModel).filter(StopModel.stop_id == stop_id).first()
    if stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop_to_dict(stop, db)

@router.get("/code/{stop_code}", response_model=Stop)
def read_stop_by_code(
    stop_code: str,
    db: Session = Depends(get_db)
):
    """Get a stop by stop code"""
    stop = db.query(StopModel).filter(StopModel.code == stop_code).first()
    if stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop_to_dict(stop, db)

@router.get("/nearby/", response_model=List[Stop])
def read_nearby_stops(
    latitude: float,
    longitude: float,
    radius_km: float = 1.0,
    db: Session = Depends(get_db)
):
    """Get stops within a radius of a coordinate (using PostGIS spatial queries)"""
    from geoalchemy2.functions import ST_Distance, ST_GeomFromText
    
    # Create point for search location
    search_point = f'POINT({longitude} {latitude})'
    
    # Query stops within radius using PostGIS
    stops = db.query(StopModel).filter(
        ST_Distance(
            StopModel.location,
            ST_GeomFromText(search_point, 4326)
        ) <= radius_km * 1000  # Convert km to meters
    ).all()
    
    return [stop_to_dict(stop, db) for stop in stops]

@router.put("/{stop_id}", response_model=Stop)
def update_stop(
    stop_id: UUID,
    stop: StopUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific stop"""
    db_stop = db.query(StopModel).filter(StopModel.stop_id == stop_id).first()
    if db_stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    update_data = stop.dict(exclude_unset=True)
    
    # Handle geometry updates if latitude/longitude provided
    if 'latitude' in update_data and 'longitude' in update_data:
        latitude = update_data.pop('latitude')
        longitude = update_data.pop('longitude')
        location = WKTElement(f'POINT({longitude} {latitude})', srid=4326)
        update_data['location'] = location
    
    for field, value in update_data.items():
        setattr(db_stop, field, value)
    
    db.commit()
    db.refresh(db_stop)
    return stop_to_dict(db_stop, db)

@router.delete("/{stop_id}")
def delete_stop(
    stop_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific stop"""
    stop = db.query(StopModel).filter(StopModel.stop_id == stop_id).first()
    if stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    db.delete(stop)
    db.commit()
    return {"message": "Stop deleted successfully"}
