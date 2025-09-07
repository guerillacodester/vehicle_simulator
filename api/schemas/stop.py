"""
Stop Schemas
============
Pydantic schemas for Stop model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class StopBase(BaseSchema):
    code: Optional[str] = None
    name: str
    zone_id: Optional[str] = None
    # Note: location (geometry) handling would need special serialization

class StopCreate(StopBase):
    country_id: UUID
    latitude: float
    longitude: float

class StopUpdate(BaseSchema):
    code: Optional[str] = None
    name: Optional[str] = None
    zone_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Stop(StopBase):
    stop_id: UUID
    country_id: UUID
    created_at: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class StopList(BaseSchema):
    stops: list[Stop]
    total: int
