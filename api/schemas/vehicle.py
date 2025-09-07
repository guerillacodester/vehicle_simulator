"""
Vehicle Schemas
===============
Pydantic schemas for Vehicle model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum
from .base import BaseSchema, TimestampMixin

class VehicleStatusEnum(str, Enum):
    available = "available"
    in_service = "in_service"
    maintenance = "maintenance"
    retired = "retired"

class VehicleBase(BaseSchema):
    reg_code: str
    status: VehicleStatusEnum = VehicleStatusEnum.available
    profile_id: Optional[str] = None
    notes: Optional[str] = None

class VehicleCreate(VehicleBase):
    country_id: UUID
    home_depot_id: Optional[UUID] = None
    preferred_route_id: Optional[UUID] = None

class VehicleUpdate(BaseSchema):
    reg_code: Optional[str] = None
    home_depot_id: Optional[UUID] = None
    preferred_route_id: Optional[UUID] = None
    status: Optional[VehicleStatusEnum] = None
    profile_id: Optional[str] = None
    notes: Optional[str] = None

class Vehicle(VehicleBase, TimestampMixin):
    vehicle_id: UUID
    country_id: UUID
    home_depot_id: Optional[UUID] = None
    preferred_route_id: Optional[UUID] = None

class VehicleList(BaseSchema):
    vehicles: list[Vehicle]
    total: int
