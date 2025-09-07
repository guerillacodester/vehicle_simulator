"""
Driver schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class DriverBase(BaseModel):
    country_id: UUID
    name: str
    license_no: str
    home_depot_id: Optional[UUID] = None
    employment_status: str = "active"

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    country_id: Optional[UUID] = None
    name: Optional[str] = None
    license_no: Optional[str] = None
    home_depot_id: Optional[UUID] = None
    employment_status: Optional[str] = None

class Driver(DriverBase, BaseSchema):
    driver_id: UUID
    created_at: datetime
    updated_at: datetime
