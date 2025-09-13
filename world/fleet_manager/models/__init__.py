"""
Fleet Manager Models Package

This package contains all the ORM models for the fleet management system,
corresponding to the GTFS database schema with fleet management extensions.
"""

from .base import Base, VehicleStatus
from .country import Country
from .depot import Depot
from .route import Route
from .vehicle import Vehicle
from .gps_device import GPSDevice
from .service import Service
from .shape import Shape
from .route_shape import RouteShape
from .stop import Stop
from .trip import Trip
from .stop_time import StopTime
from .block import Block
from .block_break import BlockBreak
from .block_trip import BlockTrip
from .driver import Driver
from .driver_assignment import DriverAssignment
from .vehicle_assignment import VehicleAssignment
from .vehicle_status_event import VehicleStatusEvent
from .frequency import Frequency
from .timetable import Timetable
from .alembic_version import AlembicVersion
from .spatial_ref_sys import SpatialRefSys

__all__ = [
    'Base',
    'VehicleStatus',
    'Country',
    'Depot',
    'Route',
    'Vehicle',
    'GPSDevice',
    'Service',
    'Shape',
    'RouteShape',
    'Stop',
    'Trip',
    'StopTime',
    'Block',
    'BlockBreak',
    'BlockTrip',
    'Driver',
    'DriverAssignment',
    'VehicleAssignment',
    'VehicleStatusEvent',
    'Frequency',
    'Timetable',
    'AlembicVersion',
    'SpatialRefSys',
]
