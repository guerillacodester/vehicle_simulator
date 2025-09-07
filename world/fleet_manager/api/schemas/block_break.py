"""
BlockBreak schemas for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import time
from uuid import UUID
from .base import BaseSchema

class BlockBreakBase(BaseModel):
    block_id: UUID
    break_start: time
    break_end: time
    break_duration: int

class BlockBreakCreate(BlockBreakBase):
    pass

class BlockBreakUpdate(BaseModel):
    block_id: Optional[UUID] = None
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    break_duration: Optional[int] = None

class BlockBreak(BlockBreakBase, BaseSchema):
    break_id: UUID
