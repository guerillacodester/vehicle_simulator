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
        status: str = "WAITING",
        current_time: Optional[str] = None
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
            current_time: Current simulation time (ISO8601). If provided, only passengers
                         with spawned_at <= current_time are returned
        
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
            
            # Add current_time if provided
            if current_time:
                params["current_time"] = current_time
            
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
    
    async def get_route_depot_coordinates(
        self,
        route_id: str,
        strapi_url: str = "http://localhost:1337"
    ) -> Optional[Dict[str, float]]:
        """
        Get depot coordinates for a route by querying route-depots junction table.
        
        Returns depot coordinates that are marked as start_terminus for the given route.
        This is used by conductor to detect when vehicle is at depot.
        
        Args:
            route_id: Route ID (short_name or document_id)
            strapi_url: Strapi base URL
        
        Returns:
            Dict with 'latitude' and 'longitude' keys, or None if not found
        """
        try:
            # Query route-depots with populated depot relation
            # Filter for depots that are start terminus (where buses begin their route)
            params = {
                "filters[route_short_name][$eq]": route_id,
                "filters[is_start_terminus][$eq]": "true",
                "populate": "depot",
                "pagination[limit]": 1  # Just need first start depot
            }
            
            response = await self.client.get(
                f"{strapi_url}/api/route-depots",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json().get("data", [])
                if data:
                    # Get first depot marked as start terminus
                    depot = data[0].get("depot")
                    if depot:
                        lat = depot.get("latitude")
                        lon = depot.get("longitude")
                        depot_name = depot.get("name", "Unknown")
                        
                        if lat is not None and lon is not None:
                            self.logger.debug(
                                f"[CommuterServiceClient] Found depot for route {route_id}: "
                                f"{depot_name} ({lat:.6f}, {lon:.6f})"
                            )
                            return {
                                "latitude": lat,
                                "longitude": lon,
                                "depot_name": depot_name,
                                "depot_id": depot.get("depot_id")
                            }
                
                self.logger.warning(
                    f"[CommuterServiceClient] No start depot found for route {route_id}"
                )
                return None
            
            else:
                self.logger.warning(
                    f"[CommuterServiceClient] Failed to query route-depots: {response.status_code}"
                )
                return None
                
        except Exception as e:
            self.logger.error(
                f"[CommuterServiceClient] Error getting depot for route {route_id}: {e}"
            )
            return None
