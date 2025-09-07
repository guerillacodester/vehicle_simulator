"""
Block schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time
from uuid import UUID
from .base import BaseSchema

class BlockBase(BaseModel):
    country_id: UUID
    route_id: UUID
    service_id: UUID
    start_time: time
    end_time: time

class BlockCreate(BlockBase):
    pass

class BlockUpdate(BaseModel):
    country_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class Block(BlockBase, BaseSchema):
    block_id: UUID
    created_at: datetime
