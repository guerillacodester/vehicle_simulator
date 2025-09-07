"""
Route API Endpoints
==================
CRUD operations for Route model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..schemas.route import RouteCreate, RouteUpdate, RouteResponse
from models.gtfs import Route

router = APIRouter()

@router.post("/", response_model=RouteResponse)
def create_route(
    route: RouteCreate,
    db: Session = Depends(get_db)
):
    """Create a new route"""
    db_route = Route(**route.model_dump())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route

@router.get("/", response_model=List[RouteResponse])
def list_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List routes with optional filtering"""
    query = db.query(Route)
    
    if country_id:
        query = query.filter(Route.country_id == country_id)
    if is_active is not None:
        query = query.filter(Route.is_active == is_active)
    
    routes = query.offset(skip).limit(limit).all()
    return routes

@router.get("/{route_id}", response_model=RouteResponse)
def get_route(
    route_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific route by ID"""
    route = db.query(Route).filter(Route.route_id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.put("/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: UUID,
    route_update: RouteUpdate,
    db: Session = Depends(get_db)
):
    """Update a route"""
    route = db.query(Route).filter(Route.route_id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    for field, value in route_update.model_dump(exclude_unset=True).items():
        setattr(route, field, value)
    
    db.commit()
    db.refresh(route)
    return route

@router.delete("/{route_id}")
def delete_route(
    route_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a route"""
    route = db.query(Route).filter(Route.route_id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    db.delete(route)
    db.commit()
    return {"message": "Route deleted successfully"}
