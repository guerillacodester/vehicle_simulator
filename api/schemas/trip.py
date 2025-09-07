"""
Trip Schemas
============
Pydantic schemas for Trip model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class TripBase(BaseSchema):
    trip_headsign: Optional[str] = None
    direction_id: Optional[int] = None

class TripCreate(TripBase):
    route_id: UUID
    service_id: UUID
    shape_id: Optional[UUID] = None
    block_id: Optional[UUID] = None

class TripUpdate(BaseSchema):
    trip_headsign: Optional[str] = None
    direction_id: Optional[int] = None
    shape_id: Optional[UUID] = None
    block_id: Optional[UUID] = None

class Trip(TripBase):
    trip_id: UUID
    route_id: UUID
    service_id: UUID
    shape_id: Optional[UUID] = None
    block_id: Optional[UUID] = None
    created_at: datetime

class TripResponse(Trip):
    """Response schema for Trip model"""
    pass

class TripList(BaseSchema):
    trips: list[Trip]
    total: int
