"""
Vehicle Simulator Core Components
--------------------------------
Core classes and managers for the vehicle simulation system.
Building components step by step with testing.
"""

from world.vehicle_simulator.core.states import (
    DepotState, PersonState, DriverState, DeviceState, StateMachine
)
from world.vehicle_simulator.core.interfaces import (
    IDispatcher, IDepotManager, VehicleAssignment, RouteInfo
)
from world.vehicle_simulator.core.dispatcher import Dispatcher
from world.vehicle_simulator.core.depot_manager import DepotManager

__all__ = [
    'DepotState', 'PersonState', 'DriverState', 'DeviceState', 'StateMachine',
    'IDispatcher', 'IDepotManager', 'VehicleAssignment', 'RouteInfo',
    'Dispatcher', 'DepotManager'
]
