"""
Country Schemas
===============
Pydantic schemas for Country model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema

class CountryBase(BaseSchema):
    iso_code: str
    name: str

class CountryCreate(CountryBase):
    pass

class CountryUpdate(BaseSchema):
    iso_code: Optional[str] = None
    name: Optional[str] = None

class Country(CountryBase):
    country_id: UUID
    created_at: datetime

class CountryList(BaseSchema):
    countries: list[Country]
    total: int
