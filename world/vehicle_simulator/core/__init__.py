"""
Vehicle Simulator Core Components
--------------------------------
Core classes and managers for the vehicle simulation system.
Legacy standalone and vehicles depot components have been removed.
"""

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher
from world.vehicle_simulator.core.timetable_scheduler import TimetableScheduler

__all__ = ['DepotManager', 'Dispatcher', 'TimetableScheduler']
