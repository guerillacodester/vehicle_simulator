"""
PassengerDatabase - Helper class for active_passengers via Strapi API.

Provides methods to:
- Insert new passengers via Strapi REST API
- Mark passengers as boarded/alighted
- Query passengers near a location
- Delete expired passengers
"""

import aiohttp
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import math


class PassengerDatabase:
    """Helper class for Strapi active-passengers API operations."""
    
    def __init__(self, strapi_url: Optional[str] = None, api_token: Optional[str] = None):
        """
        Initialize Strapi API client.
        
        Args:
            strapi_url: Strapi base URL (default: http://localhost:1337)
            api_token: Strapi API token for authentication
        """
        self.strapi_url = strapi_url or "http://localhost:1337"
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
    
    async def connect(self):
        """Create aiohttp session."""
        self.session = aiohttp.ClientSession(headers=self.headers)
    
    async def disconnect(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
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
        expires_minutes: int = 30
    ) -> bool:
        """
        Insert a new passenger via Strapi API.
        
        Args:
            passenger_id: Unique passenger identifier
            route_id: Route the passenger is waiting for
            latitude: Passenger current latitude
            longitude: Passenger current longitude
            destination_lat: Destination latitude
            destination_lon: Destination longitude
            destination_name: Destination name/description
            depot_id: Optional depot ID if spawned from depot
            direction: Optional direction (OUTBOUND/INBOUND)
            priority: Priority level (1-5, default 3)
            expires_minutes: Minutes until passenger expires (default 30)
        
        Returns:
            True if insert successful, False otherwise
        """
        if not self.session:
            return False
        
        spawned_at = datetime.utcnow()
        expires_at = spawned_at + timedelta(minutes=expires_minutes)
        
        data = {
            "data": {
                "passenger_id": passenger_id,
                "route_id": route_id,
                "depot_id": depot_id,
                "direction": direction,
                "latitude": latitude,
                "longitude": longitude,
                "destination_name": destination_name,
                "destination_lat": destination_lat,
                "destination_lon": destination_lon,
                "spawned_at": spawned_at.isoformat() + "Z",
                "expires_at": expires_at.isoformat() + "Z",
                "status": "WAITING",
                "priority": priority
            }
        }
        
        try:
            async with self.session.post(
                f"{self.strapi_url}/api/active-passengers",
                json=data
            ) as response:
                if response.status in (200, 201):
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Error inserting passenger {passenger_id}: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error inserting passenger {passenger_id}: {e}")
            return False
    
    async def mark_boarded(self, passenger_id: str) -> bool:
        """
        Mark passenger as boarded via Strapi API.
        
        Args:
            passenger_id: Passenger to mark as boarded
        
        Returns:
            True if update successful, False otherwise
        """
        if not self.session:
            return False
        
        try:
            async with self.session.post(
                f"{self.strapi_url}/api/active-passengers/mark-boarded/{passenger_id}"
            ) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Error marking passenger {passenger_id} as boarded: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error marking passenger {passenger_id} as boarded: {e}")
            return False
    
    async def mark_alighted(self, passenger_id: str) -> bool:
        """
        Mark passenger as alighted via Strapi API.
        
        Args:
            passenger_id: Passenger to mark as alighted
        
        Returns:
            True if update successful, False otherwise
        """
        if not self.session:
            return False
        
        try:
            async with self.session.post(
                f"{self.strapi_url}/api/active-passengers/mark-alighted/{passenger_id}"
            ) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Error marking passenger {passenger_id} as alighted: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error marking passenger {passenger_id} as alighted: {e}")
            return False
    
    async def delete_expired(self) -> int:
        """
        Delete all expired passengers via Strapi API.
        
        Returns:
            Number of passengers deleted
        """
        if not self.session:
            return 0
        
        try:
            async with self.session.delete(
                f"{self.strapi_url}/api/active-passengers/cleanup/expired"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('deleted_count', 0)
                else:
                    print(f"❌ Error deleting expired passengers: {response.status}")
                    return 0
        except Exception as e:
            print(f"❌ Error deleting expired passengers: {e}")
            return 0
    
    async def query_passengers_near_location(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float,
        route_id: Optional[str] = None,
        status: str = "WAITING"
    ) -> List[Dict]:
        """
        Query passengers within radius of a location via Strapi API.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_meters: Search radius in meters
            route_id: Optional filter by route ID
            status: Filter by status (default WAITING)
        
        Returns:
            List of passenger dicts with distance_meters included
        """
        if not self.session:
            return []
        
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'radius': radius_meters,
                'status': status
            }
            if route_id:
                params['route_id'] = route_id
            
            async with self.session.get(
                f"{self.strapi_url}/api/active-passengers/near-location",
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('passengers', [])
                else:
                    print(f"❌ Error querying passengers near location: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error querying passengers near location: {e}")
            return []
    
    async def get_passenger_count(
        self,
        route_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """
        Get count of passengers via Strapi API.
        
        Args:
            route_id: Optional route ID filter
            status: Optional status filter (WAITING/ONBOARD/COMPLETED)
        
        Returns:
            Count of matching passengers
        """
        if not self.session:
            return 0
        
        try:
            params = {}
            if route_id:
                params['route_id'] = route_id
            if status:
                params['status'] = status
            
            async with self.session.get(
                f"{self.strapi_url}/api/active-passengers/stats/count",
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('total', 0)
                else:
                    print(f"❌ Error getting passenger count: {response.status}")
                    return 0
        except Exception as e:
            print(f"❌ Error getting passenger count: {e}")
            return 0
