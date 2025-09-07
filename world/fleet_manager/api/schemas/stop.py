"""
Stop schemas for Fleet Management API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class StopBase(BaseModel):
    country_id: UUID
    code: Optional[str] = None
    name: str
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    zone_id: Optional[str] = None

class StopCreate(StopBase):
    pass

class StopUpdate(BaseModel):
    country_id: Optional[UUID] = None
    code: Optional[str] = None
    name: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    zone_id: Optional[str] = None

class Stop(BaseSchema):
    stop_id: UUID
    country_id: UUID
    code: Optional[str] = None
    name: str
    latitude: float
    longitude: float
    zone_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
