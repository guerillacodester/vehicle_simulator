# world/fleet_manager/api/routers/shapes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from .. import deps
from ..schemas.shape import ShapeCreate, ShapeRead
from ...services.shape_manager import ShapeManager

router = APIRouter(prefix="/api/v1/shapes", tags=["shapes"])

@router.get("/", response_model=List[ShapeRead])
def list_shapes(sm: ShapeManager = Depends(deps.get_shape_manager)):
    shapes = sm.list_shapes()
    return [
        ShapeRead(shape_id=s.shape_id, coordinates=sm.get_coords(s.shape_id))
        for s in shapes
    ]

@router.post("/", response_model=ShapeRead)
def create_shape(payload: ShapeCreate, sm: ShapeManager = Depends(deps.get_shape_manager)):
    s = sm.create_shape(payload.coordinates)
    return ShapeRead(shape_id=s.shape_id, coordinates=payload.coordinates)

@router.get("/{shape_id}", response_model=ShapeRead)
def get_shape(shape_id: UUID, sm: ShapeManager = Depends(deps.get_shape_manager)):
    s = sm.get_shape(shape_id)
    if not s:
        raise HTTPException(status_code=404, detail="Shape not found")
    coords = sm.get_coords(shape_id)
    return ShapeRead(shape_id=s.shape_id, coordinates=coords)

@router.delete("/{shape_id}")
def delete_shape(shape_id: UUID, sm: ShapeManager = Depends(deps.get_shape_manager)):
    sm.delete_shape(shape_id)
    return {"ok": True}
