# world/fleet_manager/api/schemas/vehicle.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class VehicleBase(BaseModel):
    country_id: UUID = Field(..., description="Owning country UUID")
    reg_code: str = Field(..., description="Vehicle registration code (e.g., ZR123)")
    home_depot_id: UUID | None = None
    preferred_route_id: UUID | None = None
    status: str = Field(..., description="Vehicle status (available, active, inactive, maintenance)")
    profile_id: str | None = None
    notes: str | None = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    home_depot_id: UUID | None = None
    preferred_route_id: UUID | None = None
    status: str | None = None
    profile_id: str | None = None
    notes: str | None = None


class VehicleRead(VehicleBase):
    vehicle_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 replacement for orm_mode
