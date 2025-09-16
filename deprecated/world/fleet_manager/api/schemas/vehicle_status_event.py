"""
VehicleStatusEvent schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy import Enum
from .base import BaseSchema

class VehicleStatusEventBase(BaseModel):
    vehicle_id: UUID
    status: str  # Should be enum: active, inactive, maintenance, out_of_service
    event_time: datetime
    notes: Optional[str] = None

class VehicleStatusEventCreate(VehicleStatusEventBase):
    pass

class VehicleStatusEventUpdate(BaseModel):
    vehicle_id: Optional[UUID] = None
    status: Optional[str] = None
    event_time: Optional[datetime] = None
    notes: Optional[str] = None

class VehicleStatusEvent(VehicleStatusEventBase, BaseSchema):
    event_id: UUID
