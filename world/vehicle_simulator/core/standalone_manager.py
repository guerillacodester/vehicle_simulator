"""
Standalone Fleet Manager
-----------------------
Lightweight fleet manager that doesn't depend on the full fleet_manager module.
Uses provider interfaces for maximum flexibility.
"""

import logging
from typing import Dict, List, Optional, Any
from world.vehicle_simulator.interfaces.route_provider import IRouteProvider, IVehicleProvider, IConfigProvider
from world.vehicle_simulator.providers.file_route_provider import FileRouteProvider
from world.vehicle_simulator.providers.config_provider import SelfContainedConfigProvider

logger = logging.getLogger(__name__)


class StandaloneFleetManager:
    """
    Lightweight fleet manager for vehicle simulation.
    Completely independent of world.fleet_manager module.
    """
    
    def __init__(self, 
                 route_provider: Optional[IRouteProvider] = None,
                 config_provider: Optional[IConfigProvider] = None):
        
        self.route_provider = route_provider or FileRouteProvider()
        self.config_provider = config_provider or SelfContainedConfigProvider()
        
        logger.info("Standalone fleet manager initialized")
    
    def get_route_coordinates(self, route_identifier: str) -> List[tuple]:
        """Get coordinates for a route"""
        return self.route_provider.get_route_coordinates(route_identifier)
    
    def get_route_info(self, route_identifier: str) -> Optional[Dict[str, Any]]:
        """Get route information"""
        return self.route_provider.get_route_info(route_identifier)
    
    def list_available_routes(self) -> List[str]:
        """List all available routes"""
        return self.route_provider.list_available_routes()
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config_provider.get_database_config()
    
    def get_gps_config(self) -> Dict[str, Any]:
        """Get GPS configuration"""
        return self.config_provider.get_gps_config()
    
    def get_simulation_config(self) -> Dict[str, Any]:
        """Get simulation configuration"""
        return self.config_provider.get_simulation_config()


class FleetManagerFactory:
    """
    Factory for creating appropriate fleet manager based on available components.
    """
    
    @staticmethod
    def create_fleet_manager(prefer_database: bool = True) -> Any:
        """
        Create appropriate fleet manager implementation.
        
        Args:
            prefer_database: If True, try to use database fleet manager first
            
        Returns:
            Fleet manager instance (either full FleetManager or StandaloneFleetManager)
        """
        if prefer_database:
            try:
                # Try to import and use full fleet manager
                from world.fleet_manager.manager import FleetManager
                logger.info("Using full database-backed fleet manager")
                return FleetManager()
            except ImportError:
                logger.info("Fleet manager not available, using standalone implementation")
                return StandaloneFleetManager()
        else:
            logger.info("Using standalone fleet manager (database disabled)")
            return StandaloneFleetManager()
