# world/fleet_manager/api/schemas/shape.py
from pydantic import BaseModel
from uuid import UUID
from typing import List, Tuple

LonLat = Tuple[float, float]

class ShapeBase(BaseModel):
    pass  # reserved for future (tags, etc.)

class ShapeCreate(BaseModel):
    coordinates: List[LonLat]

class ShapeRead(BaseModel):
    shape_id: UUID
    coordinates: List[LonLat]

    class Config:
        from_attributes = True
