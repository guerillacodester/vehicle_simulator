"""
Vehicle Simulator Provider Interfaces
------------------------------------
Abstract interfaces for data providers.
"""

from world.vehicle_simulator.interfaces.route_provider import IRouteProvider, IVehicleProvider, IConfigProvider

__all__ = ['IRouteProvider', 'IVehicleProvider', 'IConfigProvider']
