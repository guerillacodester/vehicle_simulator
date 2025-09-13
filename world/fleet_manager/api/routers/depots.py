"""
Depot CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db
from ...models.depot import Depot as DepotModel
from ..schemas.depot import Depot, DepotCreate, DepotUpdate

router = APIRouter(
    prefix="/depots",
    tags=["depots"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Depot)
def create_depot(
    depot: DepotCreate,
    db: Session = Depends(get_db)
):
    """Create a new depot"""
    db_depot = DepotModel(**depot.dict())
    db.add(db_depot)
    db.commit()
    db.refresh(db_depot)
    return db_depot

@router.get("/", response_model=List[Depot])
def read_depots(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all depots with pagination"""
    depots = db.query(DepotModel).offset(skip).limit(limit).all()
    return depots

@router.get("/public", response_model=List[dict])
def read_depots_public(
    db: Session = Depends(get_db)
):
    """Get all depots with public information only (no UUIDs)"""
    depots = db.query(DepotModel).all()
    
    public_depots = []
    for depot in depots:
        # Extract coordinates from PostGIS geometry if available
        latitude = None
        longitude = None
        
        if depot.location:
            try:
                # Convert PostGIS geometry to lat/lon
                from sqlalchemy import text
                result = db.execute(
                    text("SELECT ST_Y(:geom) as lat, ST_X(:geom) as lon"),
                    {"geom": depot.location}
                ).first()
                if result:
                    latitude = float(result.lat)
                    longitude = float(result.lon)
            except Exception:
                pass
        
        public_depot = {
            "name": depot.name,
            "capacity": depot.capacity,
            "latitude": latitude,
            "longitude": longitude,
            "notes": depot.notes,
            "country": depot.country.name if depot.country else None
        }
        public_depots.append(public_depot)
    
    return public_depots

@router.get("/{depot_id}", response_model=Depot)
def read_depot(
    depot_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific depot by ID"""
    depot = db.query(DepotModel).filter(DepotModel.depot_id == depot_id).first()
    if depot is None:
        raise HTTPException(status_code=404, detail="Depot not found")
    return depot

@router.get("/country/{country_id}", response_model=List[Depot])
def read_depots_by_country(
    country_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all depots in a specific country"""
    depots = db.query(DepotModel).filter(DepotModel.country_id == country_id).all()
    return depots

@router.put("/{depot_id}", response_model=Depot)
def update_depot(
    depot_id: UUID,
    depot: DepotUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific depot"""
    db_depot = db.query(DepotModel).filter(DepotModel.depot_id == depot_id).first()
    if db_depot is None:
        raise HTTPException(status_code=404, detail="Depot not found")
    
    update_data = depot.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_depot, field, value)
    
    db.commit()
    db.refresh(db_depot)
    return db_depot

@router.delete("/{depot_id}")
def delete_depot(
    depot_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific depot"""
    depot = db.query(DepotModel).filter(DepotModel.depot_id == depot_id).first()
    if depot is None:
        raise HTTPException(status_code=404, detail="Depot not found")
    
    db.delete(depot)
    db.commit()
    return {"message": "Depot deleted successfully"}
