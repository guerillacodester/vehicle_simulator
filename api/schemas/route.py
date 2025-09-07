"""
Route Schemas
=============
Pydantic schemas for Route model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from .base import BaseSchema, TimestampMixin

class RouteBase(BaseSchema):
    short_name: str
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class RouteCreate(RouteBase):
    country_id: UUID

class RouteUpdate(BaseSchema):
    short_name: Optional[str] = None
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class Route(RouteBase, TimestampMixin):
    route_id: UUID
    country_id: UUID

class RouteResponse(Route):
    """Response schema for Route model"""
    pass

class RouteList(BaseSchema):
    routes: list[Route]
    total: int
