"""
Vehicle Simulator Package
------------------------
Standalone vehicle simulation system completely decoupled from fleet_manager.

This package provides:
- Vehicle simulation with GPS tracking
- Route-based navigation
- Multiple simulation modes (enhanced, depot-based)
- File-based or database route providers
- Complete independence from fleet_manager
"""

__version__ = "1.0.0"
__author__ = "Vehicle Simulator Team"

# Core imports - import only when needed to avoid circular dependencies
# from arknet_transit_simulator.main import VehicleSimulatorApp
# from arknet_transit_simulator.core.standalone_manager import StandaloneFleetManager
# from arknet_transit_simulator.providers.file_route_provider import FileRouteProvider
# from arknet_transit_simulator.providers.config_provider import SelfContainedConfigProvider

__all__ = [
    'VehicleSimulatorApp',
    'StandaloneFleetManager', 
    'FileRouteProvider',
    'SelfContainedConfigProvider'
]
