"""
Passenger Service Interface - Abstract dependency for Conductor

Defines the contract that any passenger repository must implement.
Allows Conductor to work with any passenger storage system without tight coupling.

Implementations:
- StrapiPassengerService - Strapi API-based (production)
- PassengerRepository (from commuter_service) - Backend for StrapiPassengerService
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime


class PassengerService(ABC):
    """Abstract interface for passenger database operations."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to passenger storage backend."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from passenger storage backend."""
        pass
    
    @abstractmethod
    async def insert_passenger(
        self,
        passenger_id: str,
        route_id: str,
        latitude: float,
        longitude: float,
        destination_lat: float,
        destination_lon: float,
        destination_name: str = "Destination",
        depot_id: Optional[str] = None,
        direction: Optional[str] = None,
        priority: int = 3,
        expires_minutes: int = 30,
        route_position: Optional[float] = None,
        spawned_at: Optional[datetime] = None
    ) -> bool:
        """Insert a new passenger."""
        pass
    
    @abstractmethod
    async def delete_passenger(self, passenger_id: str) -> bool:
        """Delete a passenger (after pickup/expiration)."""
        pass
    
    @abstractmethod
    async def query_nearby_passengers(
        self,
        route_id: str,
        latitude: float,
        longitude: float,
        radius_meters: float = 100.0,
        max_count: int = 30
    ) -> List[Dict[str, Any]]:
        """Query passengers near a location on a route."""
        pass
    
    @abstractmethod
    async def get_passenger(self, passenger_id: str) -> Optional[Dict[str, Any]]:
        """Get a single passenger by ID."""
        pass
    
    @abstractmethod
    async def list_passengers_by_route(
        self,
        route_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List all passengers waiting for a route."""
        pass
    
    @abstractmethod
    async def update_passenger_status(
        self,
        passenger_id: str,
        status: str,
        boarded_at: Optional[datetime] = None,
        alighted_at: Optional[datetime] = None
    ) -> bool:
        """Update passenger status (boarded, alighted, etc)."""
        pass
