"""
Depot Schemas
=============
Pydantic schemas for Depot model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema, TimestampMixin

class DepotBase(BaseSchema):
    name: str
    capacity: Optional[int] = None
    notes: Optional[str] = None

class DepotCreate(DepotBase):
    country_id: UUID
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DepotUpdate(BaseSchema):
    name: Optional[str] = None
    capacity: Optional[int] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Depot(DepotBase, TimestampMixin):
    depot_id: UUID
    country_id: UUID
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DepotList(BaseSchema):
    depots: list[Depot]
    total: int
