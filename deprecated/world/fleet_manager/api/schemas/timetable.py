"""
Timetable schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, time
from uuid import UUID
from .base import BaseSchema

class TimetableBase(BaseModel):
    service_id: UUID
    route_id: UUID
    effective_date: date
    expiry_date: Optional[date] = None
    start_time: time
    end_time: time

class TimetableCreate(TimetableBase):
    pass

class TimetableUpdate(BaseModel):
    service_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class Timetable(TimetableBase, BaseSchema):
    timetable_id: UUID
