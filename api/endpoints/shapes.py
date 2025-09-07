"""
Shape API Endpoints
==================
CRUD operations for Shape model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ...models.gtfs import Shape

router = APIRouter()

@router.post("/", response_model=dict)
def create_shape(
    shape_data: dict,
    db: Session = Depends(get_db)
):
    """Create a new shape"""
    db_shape = Shape(**shape_data)
    db.add(db_shape)
    db.commit()
    db.refresh(db_shape)
    return {"message": "Shape created successfully", "shape_id": str(db_shape.shape_id)}

@router.get("/", response_model=List[dict])
def list_shapes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List shapes with pagination"""
    shapes = db.query(Shape).offset(skip).limit(limit).all()
    return [{"shape_id": str(s.shape_id), "geom": str(s.geom)} for s in shapes]

@router.get("/{shape_id}", response_model=dict)
def get_shape(
    shape_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific shape by ID"""
    shape = db.query(Shape).filter(Shape.shape_id == shape_id).first()
    if not shape:
        raise HTTPException(status_code=404, detail="Shape not found")
    return {"shape_id": str(shape.shape_id), "geom": str(shape.geom)}

@router.put("/{shape_id}", response_model=dict)
def update_shape(
    shape_id: UUID,
    shape_update: dict,
    db: Session = Depends(get_db)
):
    """Update a shape"""
    shape = db.query(Shape).filter(Shape.shape_id == shape_id).first()
    if not shape:
        raise HTTPException(status_code=404, detail="Shape not found")
    
    for field, value in shape_update.items():
        if hasattr(shape, field):
            setattr(shape, field, value)
    
    db.commit()
    db.refresh(shape)
    return {"message": "Shape updated successfully"}

@router.delete("/{shape_id}")
def delete_shape(
    shape_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a shape"""
    shape = db.query(Shape).filter(Shape.shape_id == shape_id).first()
    if not shape:
        raise HTTPException(status_code=404, detail="Shape not found")
    
    db.delete(shape)
    db.commit()
    return {"message": "Shape deleted successfully"}
