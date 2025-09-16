"""
RouteShape CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

try:
    from ..dependencies import get_db
except ImportError:
    from world.fleet_manager.api.start_fleet_manager import get_db
from ...models.route_shape import RouteShape as RouteShapeModel
from ..schemas.route_shape import RouteShape, RouteShapeCreate, RouteShapeUpdate

router = APIRouter(
    prefix="/route_shapes",
    tags=["route_shapes"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=RouteShape)
def create_route_shape(
    route_shape: RouteShapeCreate,
    db: Session = Depends(get_db)
):
    """Create a new route-shape link"""
    db_route_shape = RouteShapeModel(**route_shape.dict())
    db.add(db_route_shape)
    db.commit()
    db.refresh(db_route_shape)
    return db_route_shape

@router.get("/", response_model=List[RouteShape])
def read_route_shapes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all route-shape links with pagination"""
    route_shapes = db.query(RouteShapeModel).offset(skip).limit(limit).all()
    return route_shapes

@router.get("/{route_id}/{shape_id}", response_model=RouteShape)
def read_route_shape(
    route_id: UUID,
    shape_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific route-shape link by composite key"""
    route_shape = db.query(RouteShapeModel).filter(
        RouteShapeModel.route_id == route_id,
        RouteShapeModel.shape_id == shape_id
    ).first()
    if route_shape is None:
        raise HTTPException(status_code=404, detail="Route-shape link not found")
    return route_shape

@router.put("/{route_id}/{shape_id}", response_model=RouteShape)
def update_route_shape(
    route_id: UUID,
    shape_id: UUID,
    route_shape: RouteShapeUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific route-shape link"""
    db_route_shape = db.query(RouteShapeModel).filter(
        RouteShapeModel.route_id == route_id,
        RouteShapeModel.shape_id == shape_id
    ).first()
    if db_route_shape is None:
        raise HTTPException(status_code=404, detail="Route-shape link not found")
    
    update_data = route_shape.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_route_shape, field, value)
    
    db.commit()
    db.refresh(db_route_shape)
    return db_route_shape

@router.delete("/{route_id}/{shape_id}")
def delete_route_shape(
    route_id: UUID,
    shape_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific route-shape link"""
    route_shape = db.query(RouteShapeModel).filter(
        RouteShapeModel.route_id == route_id,
        RouteShapeModel.shape_id == shape_id
    ).first()
    if route_shape is None:
        raise HTTPException(status_code=404, detail="Route-shape link not found")
    
    db.delete(route_shape)
    db.commit()
    return {"message": "Route-shape link deleted successfully"}
