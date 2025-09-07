"""
GTFS Models Package
===================
Imports all GTFS SQLAlchemy models for easy access
"""

from .base import Base
from .enums import VehicleStatusEnum, VehicleStatus

# Core models
from .country import Country
from .route import Route
from .vehicle import Vehicle
from .stop import Stop
from .depot import Depot
from .driver import Driver
from .service import Service
from .shape import Shape

# Trip and schedule models
from .trip import Trip
from .block import Block
from .stop_time import StopTime
from .route_shape import RouteShape
from .frequency import Frequency
from .timetable import Timetable

# Assignment models
from .vehicle_assignment import VehicleAssignment
from .driver_assignment import DriverAssignment
from .vehicle_status_event import VehicleStatusEvent

# Operational models
from .block_trip import BlockTrip
from .block_break import BlockBreak

# System models
from .spatial_ref_sys import SpatialRefSys
from .alembic_version import AlembicVersion

__all__ = [
    "Base",
    "VehicleStatusEnum", 
    "VehicleStatus",
    
    # Core models
    "Country",
    "Route", 
    "Vehicle",
    "Stop",
    "Depot",
    "Driver",
    "Service", 
    "Shape",
    
    # Trip and schedule models
    "Trip",
    "Block",
    "StopTime",
    "RouteShape",
    "Frequency",
    "Timetable",
    
    # Assignment models
    "VehicleAssignment",
    "DriverAssignment", 
    "VehicleStatusEvent",
    
    # Operational models
    "BlockTrip",
    "BlockBreak",
    
    # System models
    "SpatialRefSys",
    "AlembicVersion"
]
