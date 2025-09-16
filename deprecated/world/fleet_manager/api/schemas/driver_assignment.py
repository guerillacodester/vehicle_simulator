"""
DriverAssignment schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class DriverAssignmentBase(BaseModel):
    driver_id: UUID
    vehicle_id: UUID
    block_id: Optional[UUID] = None
    assignment_start: datetime
    assignment_end: Optional[datetime] = None

class DriverAssignmentCreate(DriverAssignmentBase):
    pass

class DriverAssignmentUpdate(BaseModel):
    driver_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    block_id: Optional[UUID] = None
    assignment_start: Optional[datetime] = None
    assignment_end: Optional[datetime] = None

class DriverAssignment(DriverAssignmentBase, BaseSchema):
    assignment_id: UUID
