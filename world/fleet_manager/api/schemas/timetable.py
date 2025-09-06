from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class TimetableBase(BaseModel):
    vehicle_id: UUID = Field(..., description="Assigned vehicle UUID")
    route_id: UUID = Field(..., description="Assigned route UUID")
    departure_time: datetime = Field(..., description="Planned departure time (UTC)")
    arrival_time: datetime | None = Field(None, description="Optional planned arrival time")
    notes: str | None = Field(None, description="Optional notes")

class TimetableCreate(TimetableBase):
    pass

class TimetableUpdate(BaseModel):
    departure_time: datetime | None = None
    arrival_time: datetime | None = None
    route_id: UUID | None = None
    notes: str | None = None

class TimetableRead(TimetableBase):
    timetable_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 compatible
