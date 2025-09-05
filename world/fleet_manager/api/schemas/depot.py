# world/fleet_manager/api/schemas/depot.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class DepotBase(BaseModel):
    country_id: UUID = Field(..., description="Owning country UUID")
    name: str = Field(..., description="Depot name")
    capacity: int | None = Field(None, description="Max number of vehicles")
    notes: str | None = Field(None, description="Optional notes")


class DepotCreate(DepotBase):
    pass


class DepotUpdate(BaseModel):
    name: str | None = None
    capacity: int | None = None
    notes: str | None = None


class DepotRead(DepotBase):
    depot_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True   # Pydantic v2 equivalent of orm_mode
