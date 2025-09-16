"""
Service schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from .base import BaseSchema

class ServiceBase(BaseModel):
    country_id: UUID
    name: str
    mon: bool = False
    tue: bool = False
    wed: bool = False
    thu: bool = False
    fri: bool = False
    sat: bool = False
    sun: bool = False
    date_start: date
    date_end: date

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    country_id: Optional[UUID] = None
    name: Optional[str] = None
    mon: Optional[bool] = None
    tue: Optional[bool] = None
    wed: Optional[bool] = None
    thu: Optional[bool] = None
    fri: Optional[bool] = None
    sat: Optional[bool] = None
    sun: Optional[bool] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None

class Service(ServiceBase, BaseSchema):
    service_id: UUID
    created_at: datetime
    updated_at: datetime
