"""
Trip schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class TripBase(BaseModel):
    route_id: UUID
    service_id: UUID
    shape_id: Optional[UUID] = None
    trip_headsign: Optional[str] = None
    direction_id: Optional[int] = None
    block_id: Optional[UUID] = None

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    route_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    shape_id: Optional[UUID] = None
    trip_headsign: Optional[str] = None
    direction_id: Optional[int] = None
    block_id: Optional[UUID] = None

class Trip(TripBase, BaseSchema):
    trip_id: UUID
    created_at: datetime
