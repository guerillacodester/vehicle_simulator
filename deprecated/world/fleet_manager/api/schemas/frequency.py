"""
Frequency schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import time
from uuid import UUID
from .base import BaseSchema

class FrequencyBase(BaseModel):
    trip_id: UUID
    start_time: time
    end_time: time
    headway_secs: int
    exact_times: Optional[int] = None

class FrequencyCreate(FrequencyBase):
    pass

class FrequencyUpdate(BaseModel):
    trip_id: Optional[UUID] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    headway_secs: Optional[int] = None
    exact_times: Optional[int] = None

class Frequency(FrequencyBase, BaseSchema):
    frequency_id: UUID
