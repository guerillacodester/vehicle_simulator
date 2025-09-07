"""
Country schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class CountryBase(BaseModel):
    iso_code: str
    name: str

class CountryCreate(CountryBase):
    pass

class CountryUpdate(BaseModel):
    iso_code: Optional[str] = None
    name: Optional[str] = None

class Country(CountryBase, BaseSchema):
    country_id: UUID
    created_at: datetime
