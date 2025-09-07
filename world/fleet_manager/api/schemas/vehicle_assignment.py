"""
VehicleAssignment schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class VehicleAssignmentBase(BaseModel):
    vehicle_id: UUID
    route_id: UUID
    block_id: Optional[UUID] = None
    assignment_start: datetime
    assignment_end: Optional[datetime] = None

class VehicleAssignmentCreate(VehicleAssignmentBase):
    pass

class VehicleAssignmentUpdate(BaseModel):
    vehicle_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    block_id: Optional[UUID] = None
    assignment_start: Optional[datetime] = None
    assignment_end: Optional[datetime] = None

class VehicleAssignment(VehicleAssignmentBase, BaseSchema):
    assignment_id: UUID
