"""
Vehicle Simulator Provider Implementations
------------------------------------------
Concrete implementations of provider interfaces.
"""

from world.vehicle_simulator.providers.file_route_provider import FileRouteProvider
from world.vehicle_simulator.providers.config_provider import SelfContainedConfigProvider

try:
    from world.vehicle_simulator.providers.database_route_provider import DatabaseRouteProvider
    __all__ = ['FileRouteProvider', 'SelfContainedConfigProvider', 'DatabaseRouteProvider']
except ImportError:
    # Database provider not available (fleet_manager not installed)
    __all__ = ['FileRouteProvider', 'SelfContainedConfigProvider']
