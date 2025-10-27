"""
Strapi Passenger Service - Concrete implementation using commuter_simulator

Wraps PassengerRepository from commuter_simulator to provide passenger operations
via Strapi API. This is the production implementation.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from arknet_transit_simulator.services.passenger_service import PassengerService


class StrapiPassengerService(PassengerService):
    """
    Strapi-based passenger service using commuter_simulator.infrastructure.database.PassengerRepository
    
    This service bridges arknet_transit_simulator (vehicle simulator) with
    commuter_simulator (passenger management) via dependency injection.
    """
    
    def __init__(self, passenger_repository, logger: Optional[logging.Logger] = None):
        """
        Initialize with injected passenger repository.
        
        Args:
            passenger_repository: Instance of PassengerRepository from commuter_simulator
            logger: Logger instance
        """
        self.passenger_repo = passenger_repository
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("[StrapiPassengerService] Initialized with PassengerRepository")
    
    async def connect(self) -> bool:
        """Connect to Strapi API."""
        try:
            await self.passenger_repo.connect()
            self.logger.info("[StrapiPassengerService] Connected to Strapi")
            return True
        except Exception as e:
            self.logger.error(f"[StrapiPassengerService] Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Strapi API."""
        try:
            await self.passenger_repo.disconnect()
            self.logger.info("[StrapiPassengerService] Disconnected from Strapi")
        except Exception as e:
            self.logger.error(f"[StrapiPassengerService] Disconnection error: {e}")
    
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
        """Insert a new passenger via PassengerRepository."""
        return await self.passenger_repo.insert_passenger(
            passenger_id=passenger_id,
            route_id=route_id,
            latitude=latitude,
            longitude=longitude,
            destination_lat=destination_lat,
            destination_lon=destination_lon,
            destination_name=destination_name,
            depot_id=depot_id,
            direction=direction,
            priority=priority,
            expires_minutes=expires_minutes,
            route_position=route_position,
            spawned_at=spawned_at
        )
    
    async def delete_passenger(self, passenger_id: str) -> bool:
        """Delete a passenger via PassengerRepository."""
        return await self.passenger_repo.delete_passenger(passenger_id)
    
    async def query_nearby_passengers(
        self,
        route_id: str,
        latitude: float,
        longitude: float,
        radius_meters: float = 100.0,
        max_count: int = 30
    ) -> List[Dict[str, Any]]:
        """Query nearby passengers via PassengerRepository."""
        return await self.passenger_repo.query_nearby_passengers(
            route_id=route_id,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            max_count=max_count
        )
    
    async def get_passenger(self, passenger_id: str) -> Optional[Dict[str, Any]]:
        """Get a single passenger via PassengerRepository."""
        return await self.passenger_repo.get_passenger(passenger_id)
    
    async def list_passengers_by_route(
        self,
        route_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List passengers by route via PassengerRepository."""
        return await self.passenger_repo.list_passengers_by_route(
            route_id=route_id,
            limit=limit
        )
    
    async def update_passenger_status(
        self,
        passenger_id: str,
        status: str,
        boarded_at: Optional[datetime] = None,
        alighted_at: Optional[datetime] = None
    ) -> bool:
        """Update passenger status via PassengerRepository."""
        return await self.passenger_repo.update_passenger_status(
            passenger_id=passenger_id,
            status=status,
            boarded_at=boarded_at,
            alighted_at=alighted_at
        )
