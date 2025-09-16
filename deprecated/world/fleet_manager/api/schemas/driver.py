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

class DriverPublic(BaseModel):
    """Public driver schema without UUIDs for enhanced security"""
    name: str
    license_no: str
    employment_status: str = "active"

class DriverPublicCreate(BaseModel):
    """Create driver using public API with business identifiers only"""
    name: str
    license_no: str
    employment_status: str = "active"
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    # Business identifiers instead of UUIDs
    country_code: Optional[str] = None      # e.g., "BB" for Barbados

class DriverPublicUpdate(BaseModel):
    """Update driver using public API with business identifiers only"""
    name: Optional[str] = None
    employment_status: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
