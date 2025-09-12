"""
Basic interface definitions for vehicle simulator components.

Includes data classes for vehicle assignments and route information.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class VehicleAssignment:
    """Vehicle assignment data from Fleet Manager API."""
    vehicle_id: str
    route_id: str
    driver_id: str
    assignment_type: str = "regular"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    # Human-readable friendly names
    vehicle_reg_code: Optional[str] = None    # License plate (e.g., "ZR101")
    driver_name: Optional[str] = None         # Driver name (e.g., "John Smith")
    route_name: Optional[str] = None          # Route name (e.g., "1A")


@dataclass
class DriverAssignment:
    """Driver assignment data from Fleet Manager API."""
    driver_id: str
    driver_name: str
    license_number: str
    vehicle_id: Optional[str] = None
    route_id: Optional[str] = None
    status: str = "available"
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None


@dataclass
class RouteInfo:
    """Route information data from Fleet Manager API."""
    route_id: str
    route_name: str
    route_type: str
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON LineString with coordinates
    stops: Optional[List[Dict[str, Any]]] = None
    distance_km: Optional[float] = None
    coordinate_count: Optional[int] = None     # Number of GPS coordinate points
    shape_id: Optional[str] = None             # Reference to shape data


class IDispatcher(ABC):
    """
    Interface for dispatcher component - API gateway functionality.
    """
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the dispatcher."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the dispatcher."""
        pass
    
    @abstractmethod
    async def get_api_status(self) -> Dict[str, Any]:
        """Get current API status."""
        pass
    
    @abstractmethod
    async def get_vehicle_assignments(self) -> List[VehicleAssignment]:
        """Get vehicle assignments from API."""
        pass
    
    @abstractmethod
    async def get_driver_assignments(self) -> List[DriverAssignment]:
        """Get driver assignments from API."""
        pass
    
    @abstractmethod
    async def get_route_info(self, route_id: str) -> Optional[RouteInfo]:
        """Get route information from API."""
        pass
    
    @abstractmethod
    async def send_routes_to_drivers(self, driver_routes: List[Dict[str, str]]) -> bool:
        """Send route assignments to drivers. Returns success status."""
        pass


class IDepotManager(ABC):
    """
    Interface for depot manager component - master orchestrator.
    """
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the depot manager."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the depot manager."""
        pass
    
    @abstractmethod
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        pass