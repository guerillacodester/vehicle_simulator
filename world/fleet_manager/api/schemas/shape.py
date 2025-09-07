"""
Shape schemas for Fleet Management API
"""
from pydantic import BaseModel
from uuid import UUID
from .base import BaseSchema

class ShapeBase(BaseModel):
    pass  # Geometry field will be handled separately

class ShapeCreate(ShapeBase):
    pass

class ShapeUpdate(ShapeBase):
    pass

class Shape(ShapeBase, BaseSchema):
    shape_id: UUID
