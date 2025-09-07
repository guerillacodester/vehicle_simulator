"""
Base Pydantic Schemas
=====================
Base classes and common schemas for GTFS API
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date, time
from uuid import UUID

class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )

class TimestampMixin(BaseModel):
    """Mixin for models with timestamps"""
    created_at: datetime
    updated_at: Optional[datetime] = None

class UUIDMixin(BaseModel):
    """Mixin for models with UUID primary keys"""
    pass
