"""
Depot schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class DepotBase(BaseModel):
    country_id: UUID
    name: str
    capacity: Optional[int] = None
    notes: Optional[str] = None

class DepotCreate(DepotBase):
    pass

class DepotUpdate(BaseModel):
    country_id: Optional[UUID] = None
    name: Optional[str] = None
    capacity: Optional[int] = None
    notes: Optional[str] = None

class Depot(DepotBase, BaseSchema):
    depot_id: UUID
    created_at: datetime
    updated_at: datetime
