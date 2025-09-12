"""
Route schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from .base import BaseSchema

class RouteBase(BaseModel):
    country_id: UUID
    short_name: str
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class RouteCreate(RouteBase):
    pass

class RouteUpdate(BaseModel):
    country_id: Optional[UUID] = None
    short_name: Optional[str] = None
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class Route(RouteBase, BaseSchema):
    route_id: UUID
    created_at: datetime
    updated_at: datetime

class RoutePublic(BaseModel):
    """Public route schema without UUIDs for enhanced security"""
    short_name: str
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
