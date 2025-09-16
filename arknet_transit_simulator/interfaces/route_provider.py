"""
Route Provider Interface
-----------------------
Abstract interface for route data providers, allowing different implementations
(database, file-based, API, etc.) to be used interchangeably.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any


class IRouteProvider(ABC):
    """Interface for route data providers"""
    
    @abstractmethod
    def get_route_coordinates(self, route_identifier: str) -> List[Tuple[float, float]]:
        """
        Get coordinates for a route by identifier.
        
        Args:
            route_identifier: Route ID, short name, or file path
            
        Returns:
            List of (longitude, latitude) coordinate tuples
        """
        pass
    
    @abstractmethod
    def get_route_info(self, route_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get route metadata.
        
        Args:
            route_identifier: Route ID, short name, or file path
            
        Returns:
            Dictionary with route information or None if not found
        """
        pass
    
    @abstractmethod
    def list_available_routes(self) -> List[str]:
        """
        List all available route identifiers.
        
        Returns:
            List of route identifiers
        """
        pass


class IVehicleProvider(ABC):
    """Interface for vehicle data providers"""
    
    @abstractmethod
    def get_vehicle_info(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get vehicle information by ID"""
        pass
    
    @abstractmethod
    def list_active_vehicles(self) -> List[Dict[str, Any]]:
        """List all active vehicles"""
        pass
    
    @abstractmethod
    def update_vehicle_status(self, vehicle_id: str, status: str) -> bool:
        """Update vehicle status"""
        pass


class IConfigProvider(ABC):
    """Interface for configuration providers"""
    
    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        pass
    
    @abstractmethod
    def get_gps_config(self) -> Dict[str, Any]:
        """Get GPS server configuration"""
        pass
    
    @abstractmethod
    def get_simulation_config(self) -> Dict[str, Any]:
        """Get simulation parameters"""
        pass
