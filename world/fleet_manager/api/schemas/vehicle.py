from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, Literal
from datetime import datetime
from uuid import UUID

# Vehicle status enum
VehicleStatus = Literal["available", "active", "inactive", "maintenance"]

# ✅ Regex: ZR + 2–3 digits only (ZR12 or ZR123)
RegCode = Annotated[
    str,
    StringConstraints(pattern=r"^ZR[0-9]{2,3}$", strip_whitespace=True)
]

class VehicleBase(BaseModel):
    country_id: UUID = Field(..., description="Owning country UUID")
    reg_code: RegCode = Field(
        ...,
        description="Vehicle registration code (ZR + 2–3 digits, e.g., ZR123)"
    )
    home_depot_id: UUID | None = Field(None, description="Assigned depot UUID")
    preferred_route_id: UUID | None = Field(None, description="Preferred operating route")
    status: VehicleStatus = Field(..., description="Vehicle status")
    profile_id: str | None = Field(None, description="Linked profile or driver ID")
    notes: str | None = Field(None, description="Optional notes")

class VehicleCreate(VehicleBase):
    """Schema for creating a new vehicle."""
    pass

class VehicleUpdate(BaseModel):
    """Schema for partial updates (PATCH)."""
    home_depot_id: UUID | None = None
    preferred_route_id: UUID | None = None
    status: VehicleStatus | None = None
    profile_id: str | None = None
    notes: str | None = None

class VehicleRead(VehicleBase):
    vehicle_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 replacement for orm_mode
