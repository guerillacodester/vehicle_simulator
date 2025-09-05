from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CountryBase(BaseModel):
    iso_code: str
    name: str


class CountryCreate(CountryBase):
    pass


class CountryUpdate(BaseModel):
    iso_code: str | None = None
    name: str | None = None


class CountryRead(CountryBase):
    country_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True  # ✅ Pydantic v2 replacement for orm_mode
