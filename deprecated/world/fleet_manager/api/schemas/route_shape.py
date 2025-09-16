"""
RouteShape schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from .base import BaseSchema

class RouteShapeBase(BaseModel):
    route_id: UUID
    shape_id: UUID
    variant_code: Optional[str] = None
    is_default: bool = False

class RouteShapeCreate(RouteShapeBase):
    pass

class RouteShapeUpdate(BaseModel):
    variant_code: Optional[str] = None
    is_default: Optional[bool] = None

class RouteShape(RouteShapeBase, BaseSchema):
    pass  # Composite primary key, no additional fields
