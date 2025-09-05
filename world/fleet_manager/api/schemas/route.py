from __future__ import annotations
from typing import Optional, List, Tuple, Any
from uuid import UUID
from pydantic import BaseModel, Field

LonLat = Tuple[float, float]

class RouteOut(BaseModel):
    route_id: UUID
    short_name: str
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: bool = True

class RouteCreate(BaseModel):
    country_id: Optional[UUID] = None
    short_name: str = Field(..., min_length=1, max_length=32)
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: bool = True

class RouteUpdate(BaseModel):
    short_name: Optional[str] = None
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: Optional[bool] = None

class CoordinatesResponse(BaseModel):
    route: str
    split_by_shape: bool
    coordinates: Any  # List[LonLat] or List[List[LonLat]]
