"""
Driver Schemas
==============
Pydantic schemas for Driver model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema, TimestampMixin

class DriverBase(BaseSchema):
    name: str
    license_no: str
    employment_status: str = "active"

class DriverCreate(DriverBase):
    country_id: UUID
    home_depot_id: Optional[UUID] = None

class DriverUpdate(BaseSchema):
    name: Optional[str] = None
    license_no: Optional[str] = None
    home_depot_id: Optional[UUID] = None
    employment_status: Optional[str] = None

class Driver(DriverBase, TimestampMixin):
    driver_id: UUID
    country_id: UUID
    home_depot_id: Optional[UUID] = None

class DriverList(BaseSchema):
    drivers: list[Driver]
    total: int
