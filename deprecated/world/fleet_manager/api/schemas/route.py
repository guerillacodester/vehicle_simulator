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

class RoutePublicCreate(BaseModel):
    """Create route using public API with business identifiers only"""
    short_name: str
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    # Business identifiers instead of UUIDs
    country_code: Optional[str] = None      # e.g., "BB" for Barbados
    # Geometry data for route navigation
    geometry: Optional[dict] = None         # GeoJSON LineString
    variant_code: Optional[str] = "default" # Shape variant identifier

class RoutePublicUpdate(BaseModel):
    """Update route using public API with business identifiers only"""
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    # Geometry updates
    geometry: Optional[dict] = None         # GeoJSON LineString
    variant_code: Optional[str] = None      # Shape variant identifier

class RoutePublicWithGeometry(BaseModel):
    """Public route schema with geometry data included"""
    short_name: str
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    geometry: Optional[dict] = None         # GeoJSON LineString
    coordinate_count: Optional[int] = None  # Number of GPS points
