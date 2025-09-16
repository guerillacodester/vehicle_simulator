"""
Base schemas for Fleet Management API
"""
from pydantic import BaseModel, ConfigDict
from enum import Enum

# Enum for vehicle status
class VehicleStatusEnum(str, Enum):
    available = "available"
    in_service = "in_service"
    maintenance = "maintenance"
    retired = "retired"

class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)
