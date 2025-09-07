"""
Depot API Endpoints
==================
CRUD operations for Depot model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..schemas.depot import DepotCreate, DepotUpdate, DepotResponse
from ...models.gtfs import Depot

router = APIRouter()

@router.post("/", response_model=DepotResponse)
def create_depot(
    depot: DepotCreate,
    db: Session = Depends(get_db)
):
    """Create a new depot"""
    db_depot = Depot(**depot.model_dump())
    db.add(db_depot)
    db.commit()
    db.refresh(db_depot)
    return db_depot

@router.get("/", response_model=List[DepotResponse])
def list_depots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List depots with optional filtering"""
    query = db.query(Depot)
    
    if country_id:
        query = query.filter(Depot.country_id == country_id)
    
    depots = query.offset(skip).limit(limit).all()
    return depots

@router.get("/{depot_id}", response_model=DepotResponse)
def get_depot(
    depot_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific depot by ID"""
    depot = db.query(Depot).filter(Depot.depot_id == depot_id).first()
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")
    return depot

@router.put("/{depot_id}", response_model=DepotResponse)
def update_depot(
    depot_id: UUID,
    depot_update: DepotUpdate,
    db: Session = Depends(get_db)
):
    """Update a depot"""
    depot = db.query(Depot).filter(Depot.depot_id == depot_id).first()
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")
    
    for field, value in depot_update.model_dump(exclude_unset=True).items():
        setattr(depot, field, value)
    
    db.commit()
    db.refresh(depot)
    return depot

@router.delete("/{depot_id}")
def delete_depot(
    depot_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a depot"""
    depot = db.query(Depot).filter(Depot.depot_id == depot_id).first()
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")
    
    db.delete(depot)
    db.commit()
    return {"message": "Depot deleted successfully"}
