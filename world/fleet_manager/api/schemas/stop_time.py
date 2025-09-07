"""
StopTime schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import time
from uuid import UUID
from .base import BaseSchema

class StopTimeBase(BaseModel):
    trip_id: UUID
    stop_id: UUID
    arrival_time: time
    departure_time: time
    stop_sequence: int

class StopTimeCreate(StopTimeBase):
    pass

class StopTimeUpdate(BaseModel):
    arrival_time: Optional[time] = None
    departure_time: Optional[time] = None
    stop_sequence: Optional[int] = None

class StopTime(StopTimeBase, BaseSchema):
    pass  # Composite primary key, no additional fields
