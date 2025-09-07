"""
Route CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ...database import get_db
from ...models.route import Route as RouteModel
from ..schemas.route import Route, RouteCreate, RouteUpdate

router = APIRouter(
    prefix="/routes",
    tags=["routes"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Route)
def create_route(
    route: RouteCreate,
    db: Session = Depends(get_db)
):
    """Create a new route"""
    db_route = RouteModel(**route.dict())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route

@router.get("/", response_model=List[Route])
def read_routes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all routes with pagination"""
    routes = db.query(RouteModel).offset(skip).limit(limit).all()
    return routes

@router.get("/{route_id}", response_model=Route)
def read_route(
    route_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific route by ID"""
    route = db.query(RouteModel).filter(RouteModel.route_id == route_id).first()
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.get("/short_name/{route_short_name}", response_model=List[Route])
def read_routes_by_short_name(
    route_short_name: str,
    db: Session = Depends(get_db)
):
    """Get routes by short name"""
    routes = db.query(RouteModel).filter(RouteModel.route_short_name == route_short_name).all()
    return routes

@router.get("/type/{route_type}", response_model=List[Route])
def read_routes_by_type(
    route_type: int,
    db: Session = Depends(get_db)
):
    """Get routes by type (0=Tram, 1=Subway, 2=Rail, 3=Bus, etc.)"""
    routes = db.query(RouteModel).filter(RouteModel.route_type == route_type).all()
    return routes

@router.put("/{route_id}", response_model=Route)
def update_route(
    route_id: UUID,
    route: RouteUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific route"""
    db_route = db.query(RouteModel).filter(RouteModel.route_id == route_id).first()
    if db_route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    
    update_data = route.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_route, field, value)
    
    db.commit()
    db.refresh(db_route)
    return db_route

@router.delete("/{route_id}")
def delete_route(
    route_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific route"""
    route = db.query(RouteModel).filter(RouteModel.route_id == route_id).first()
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    
    db.delete(route)
    db.commit()
    return {"message": "Route deleted successfully"}
