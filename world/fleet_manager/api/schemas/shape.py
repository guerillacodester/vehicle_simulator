"""
Shape schemas for Fleet Management API
"""
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Dict, Any, Optional
from .base import BaseSchema

class ShapeBase(BaseModel):
    geom: Dict[str, Any]  # GeoJSON geometry object

class ShapeCreate(ShapeBase):
    pass

class ShapeUpdate(ShapeBase):
    pass

class Shape(BaseSchema):
    shape_id: UUID
    geom: Optional[Dict[str, Any]] = Field(default=None, description="GeoJSON geometry object")
    
    class Config:
        # Allow extra fields and handle geometry conversion
        extra = "ignore"
