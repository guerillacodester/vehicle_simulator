"""
Vehicle Simulator Provider Implementations
------------------------------------------
Core data provider for fleet management integration.
Legacy file-based and standalone providers have been removed.
"""

from world.vehicle_simulator.providers.data_provider import FleetDataProvider
from world.vehicle_simulator.providers.api_monitor import SocketIOAPIMonitor

__all__ = ['FleetDataProvider', 'SocketIOAPIMonitor']
