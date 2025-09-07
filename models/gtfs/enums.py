"""
GTFS Enums
==========
Enumerations used across GTFS models
"""

import enum
from sqlalchemy import Enum as SQLEnum

class VehicleStatusEnum(enum.Enum):
    available = "available"
    in_service = "in_service" 
    maintenance = "maintenance"
    retired = "retired"

# SQLAlchemy enum type for use in models
VehicleStatus = SQLEnum(VehicleStatusEnum)
