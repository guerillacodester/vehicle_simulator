"""
RouteShape API Endpoints
=======================
CRUD operations for RouteShape model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ...models.gtfs import RouteShape

router = APIRouter()

@router.post("/", response_model=dict)
def create_route_shape(
    route_shape_data: dict,
    db: Session = Depends(get_db)
):
    """Create a new route shape association"""
    db_route_shape = RouteShape(**route_shape_data)
    db.add(db_route_shape)
    db.commit()
    db.refresh(db_route_shape)
    return {"message": "Route shape association created successfully"}

@router.get("/", response_model=List[dict])
def list_route_shapes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    route_id: Optional[UUID] = Query(None),
    shape_id: Optional[UUID] = Query(None),
    is_default: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List route shapes with optional filtering"""
    query = db.query(RouteShape)
    
    if route_id:
        query = query.filter(RouteShape.route_id == route_id)
    if shape_id:
        query = query.filter(RouteShape.shape_id == shape_id)
    if is_default is not None:
        query = query.filter(RouteShape.is_default == is_default)
    
    route_shapes = query.offset(skip).limit(limit).all()
    return [
        {
            "route_id": str(rs.route_id),
            "shape_id": str(rs.shape_id),
            "variant_code": rs.variant_code,
            "is_default": rs.is_default
        } for rs in route_shapes
    ]

@router.get("/{route_id}/{shape_id}", response_model=dict)
def get_route_shape(
    route_id: UUID,
    shape_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific route shape by composite key"""
    route_shape = db.query(RouteShape).filter(
        RouteShape.route_id == route_id,
        RouteShape.shape_id == shape_id
    ).first()
    
    if not route_shape:
        raise HTTPException(status_code=404, detail="Route shape not found")
    
    return {
        "route_id": str(route_shape.route_id),
        "shape_id": str(route_shape.shape_id),
        "variant_code": route_shape.variant_code,
        "is_default": route_shape.is_default
    }

@router.put("/{route_id}/{shape_id}", response_model=dict)
def update_route_shape(
    route_id: UUID,
    shape_id: UUID,
    route_shape_update: dict,
    db: Session = Depends(get_db)
):
    """Update a route shape"""
    route_shape = db.query(RouteShape).filter(
        RouteShape.route_id == route_id,
        RouteShape.shape_id == shape_id
    ).first()
    
    if not route_shape:
        raise HTTPException(status_code=404, detail="Route shape not found")
    
    for field, value in route_shape_update.items():
        if hasattr(route_shape, field):
            setattr(route_shape, field, value)
    
    db.commit()
    db.refresh(route_shape)
    return {"message": "Route shape updated successfully"}

@router.delete("/{route_id}/{shape_id}")
def delete_route_shape(
    route_id: UUID,
    shape_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a route shape"""
    route_shape = db.query(RouteShape).filter(
        RouteShape.route_id == route_id,
        RouteShape.shape_id == shape_id
    ).first()
    
    if not route_shape:
        raise HTTPException(status_code=404, detail="Route shape not found")
    
    db.delete(route_shape)
    db.commit()
    return {"message": "Route shape deleted successfully"}
