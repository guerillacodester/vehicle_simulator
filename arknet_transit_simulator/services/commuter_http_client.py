"""
Commuter Service HTTP Client

HTTP client for conductor to query commuter_service API.
Uses the reservoir-backed endpoints for passenger visibility.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx


class CommuterServiceClient:
    """
    HTTP client for querying commuter_service passenger API.
    
    Used by conductor to find eligible passengers via the reservoir pattern:
    Conductor → HTTP API → Reservoir → Repository → Strapi
    """
    
    def __init__(self, base_url: str = "http://localhost:4000", logger: Optional[logging.Logger] = None):
        """
        Initialize commuter service client.
        
        Args:
            base_url: Base URL for commuter_service (default: http://localhost:4000)
            logger: Logger instance
        """
        self.base_url = base_url.rstrip("/")
        self.logger = logger or logging.getLogger(__name__)
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def connect(self) -> bool:
        """Test connection to commuter_service."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.logger.info(f"[CommuterServiceClient] Connected to {self.base_url}")
                return True
            else:
                self.logger.warning(f"[CommuterServiceClient] Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"[CommuterServiceClient] Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
        self.logger.info("[CommuterServiceClient] Disconnected")
    
    async def get_eligible_passengers(
        self,
        vehicle_lat: float,
        vehicle_lon: float,
        route_id: str,
        pickup_radius_km: float = 0.2,
        max_results: int = 50,
        status: str = "WAITING"
    ) -> List[Dict[str, Any]]:
        """
        Query for eligible passengers near vehicle position.
        
        This method calls the commuter_service /api/passengers/nearby endpoint
        which goes through the reservoir pattern for consistency.
        
        Args:
            vehicle_lat: Current vehicle latitude
            vehicle_lon: Current vehicle longitude
            route_id: Route ID to filter passengers
            pickup_radius_km: Search radius in kilometers (default: 0.2 km)
            max_results: Maximum passengers to return (default: 50)
            status: Filter by passenger status (default: WAITING)
        
        Returns:
            List of passenger dictionaries, sorted by distance (closest first)
        """
        try:
            params = {
                "latitude": vehicle_lat,
                "longitude": vehicle_lon,
                "route_id": route_id,
                "radius_km": pickup_radius_km,
                "max_results": max_results,
                "status": status
            }
            
            response = await self.client.get(
                f"{self.base_url}/api/passengers/nearby",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                passengers = data.get("data", [])
                self.logger.debug(
                    f"[CommuterServiceClient] Found {len(passengers)} eligible passengers "
                    f"for route {route_id} within {pickup_radius_km}km"
                )
                return passengers
            else:
                self.logger.warning(
                    f"[CommuterServiceClient] Query failed: {response.status_code} - {response.text}"
                )
                return []
                
        except Exception as e:
            self.logger.error(f"[CommuterServiceClient] Error querying passengers: {e}")
            return []
    
    async def board_passenger(
        self,
        passenger_id: str,
        vehicle_id: str
    ) -> bool:
        """
        Board a passenger (mark as boarded via API).
        
        Args:
            passenger_id: Passenger document ID
            vehicle_id: Vehicle ID boarding the passenger
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.patch(
                f"{self.base_url}/api/passengers/{passenger_id}/board",
                json={"vehicle_id": vehicle_id}
            )
            
            if response.status_code == 200:
                self.logger.info(f"[CommuterServiceClient] Boarded passenger {passenger_id}")
                return True
            else:
                self.logger.warning(
                    f"[CommuterServiceClient] Failed to board passenger {passenger_id}: "
                    f"{response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"[CommuterServiceClient] Error boarding passenger {passenger_id}: {e}")
            return False
    
    async def alight_passenger(self, passenger_id: str) -> bool:
        """
        Alight a passenger (mark as alighted via API).
        
        Args:
            passenger_id: Passenger document ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.patch(
                f"{self.base_url}/api/passengers/{passenger_id}/alight",
                json={}
            )
            
            if response.status_code == 200:
                self.logger.info(f"[CommuterServiceClient] Alighted passenger {passenger_id}")
                return True
            else:
                self.logger.warning(
                    f"[CommuterServiceClient] Failed to alight passenger {passenger_id}: "
                    f"{response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"[CommuterServiceClient] Error alighting passenger {passenger_id}: {e}")
            return False
    
    async def get_passenger(self, passenger_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single passenger by ID.
        
        Args:
            passenger_id: Passenger document ID
        
        Returns:
            Passenger dictionary or None if not found
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/passengers/{passenger_id}"
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                self.logger.debug(f"[CommuterServiceClient] Passenger {passenger_id} not found")
                return None
            else:
                self.logger.warning(
                    f"[CommuterServiceClient] Failed to get passenger {passenger_id}: "
                    f"{response.status_code}"
                )
                return None
                
        except Exception as e:
            self.logger.error(f"[CommuterServiceClient] Error getting passenger {passenger_id}: {e}")
            return None
