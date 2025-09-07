"""
BlockTrip schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from .base import BaseSchema

class BlockTripBase(BaseModel):
    block_id: UUID
    trip_id: UUID
    trip_order: int

class BlockTripCreate(BlockTripBase):
    pass

class BlockTripUpdate(BaseModel):
    block_id: Optional[UUID] = None
    trip_id: Optional[UUID] = None
    trip_order: Optional[int] = None

class BlockTrip(BlockTripBase, BaseSchema):
    block_trip_id: UUID
