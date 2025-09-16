"""
Core schemas module - imports all schema classes for easy access
"""

# Base schemas
from .base import BaseSchema

# Entity schemas
from .country import Country, CountryCreate, CountryUpdate
from .depot import Depot, DepotCreate, DepotUpdate  
from .route import Route, RouteCreate, RouteUpdate
from .vehicle import Vehicle, VehicleCreate, VehicleUpdate
from .driver import Driver, DriverCreate, DriverUpdate
from .service import Service, ServiceCreate, ServiceUpdate
from .shape import Shape, ShapeCreate, ShapeUpdate
from .route_shape import RouteShape, RouteShapeCreate, RouteShapeUpdate
from .stop import Stop, StopCreate, StopUpdate
from .trip import Trip, TripCreate, TripUpdate
from .stop_time import StopTime, StopTimeCreate, StopTimeUpdate
from .block import Block, BlockCreate, BlockUpdate

# Assignment and operational schemas
from .block_break import BlockBreak, BlockBreakCreate, BlockBreakUpdate
from .block_trip import BlockTrip, BlockTripCreate, BlockTripUpdate
from .driver_assignment import DriverAssignment, DriverAssignmentCreate, DriverAssignmentUpdate
from .vehicle_assignment import VehicleAssignment, VehicleAssignmentCreate, VehicleAssignmentUpdate
from .vehicle_status_event import VehicleStatusEvent, VehicleStatusEventCreate, VehicleStatusEventUpdate

# Schedule schemas
from .frequency import Frequency, FrequencyCreate, FrequencyUpdate
from .timetable import Timetable, TimetableCreate, TimetableUpdate

__all__ = [
    # Base
    "BaseSchema",
    
    # Core entities
    "Country", "CountryCreate", "CountryUpdate",
    "Depot", "DepotCreate", "DepotUpdate",
    "Route", "RouteCreate", "RouteUpdate", 
    "Vehicle", "VehicleCreate", "VehicleUpdate",
    "Driver", "DriverCreate", "DriverUpdate",
    "Service", "ServiceCreate", "ServiceUpdate",
    "Shape", "ShapeCreate", "ShapeUpdate",
    "RouteShape", "RouteShapeCreate", "RouteShapeUpdate",
    "Stop", "StopCreate", "StopUpdate",
    "Trip", "TripCreate", "TripUpdate",
    "StopTime", "StopTimeCreate", "StopTimeUpdate",
    "Block", "BlockCreate", "BlockUpdate",
    
    # Assignments and operations
    "BlockBreak", "BlockBreakCreate", "BlockBreakUpdate",
    "BlockTrip", "BlockTripCreate", "BlockTripUpdate", 
    "DriverAssignment", "DriverAssignmentCreate", "DriverAssignmentUpdate",
    "VehicleAssignment", "VehicleAssignmentCreate", "VehicleAssignmentUpdate",
    "VehicleStatusEvent", "VehicleStatusEventCreate", "VehicleStatusEventUpdate",
    
    # Schedules
    "Frequency", "FrequencyCreate", "FrequencyUpdate",
    "Timetable", "TimetableCreate", "TimetableUpdate",
]
