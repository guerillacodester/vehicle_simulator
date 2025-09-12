"""
Vehicle schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema, VehicleStatusEnum

class VehicleBase(BaseModel):
    country_id: UUID
    reg_code: str
    home_depot_id: Optional[UUID] = None
    preferred_route_id: Optional[UUID] = None
    assigned_driver_id: Optional[UUID] = None
    status: VehicleStatusEnum = VehicleStatusEnum.available
    profile_id: Optional[str] = None
    notes: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    country_id: Optional[UUID] = None
    reg_code: Optional[str] = None
    home_depot_id: Optional[UUID] = None
    preferred_route_id: Optional[UUID] = None
    assigned_driver_id: Optional[UUID] = None
    status: Optional[VehicleStatusEnum] = None
    profile_id: Optional[str] = None
    notes: Optional[str] = None

class Vehicle(VehicleBase, BaseSchema):
    vehicle_id: UUID
    created_at: datetime
    updated_at: datetime

class VehiclePublic(BaseModel):
    """Public vehicle schema without UUIDs for enhanced security"""
    reg_code: str
    status: VehicleStatusEnum = VehicleStatusEnum.available
    profile_id: Optional[str] = None
    notes: Optional[str] = None
