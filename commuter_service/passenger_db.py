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
        self.strapi_url = (strapi_url or "http://localhost:1337").rstrip('/api')  # Remove trailing /api if present
        print(f"🔍 PassengerDatabase initialized with URL: {self.strapi_url}")
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
            # Ensure proper headers for JSON POST
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with self.session.post(
                f"{self.strapi_url}/api/active-passengers",
                json=data,
                headers=headers
            ) as response:
                if response.status in (200, 201):
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Error inserting passenger {passenger_id}: {response.status} - {response.reason}")
                    print(f"   URL: {self.strapi_url}/api/active-passengers")
                    print(f"   Response: {error_text[:200]}")
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
    
    async def get_eligible_passengers(
        self,
        vehicle_lat: float,
        vehicle_lon: float,
        route_id: str,
        pickup_radius_km: float = 0.2,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Find eligible passengers near vehicle location.
        
        Args:
            vehicle_lat: Vehicle latitude
            vehicle_lon: Vehicle longitude
            route_id: Route the vehicle is serving
            pickup_radius_km: Search radius in kilometers (default: 0.2km = 200m)
            max_results: Maximum passengers to return
            
        Returns:
            List of passenger records sorted by priority (high to low)
        """
        if not self.session:
            print("❌ Session not connected, call connect() first")
            return []
        
        try:
            # Calculate bounding box for spatial query
            # ~111km per degree latitude, adjusted for longitude
            lat_delta = pickup_radius_km / 111.0
            lon_delta = pickup_radius_km / (111.0 * math.cos(math.radians(vehicle_lat)))
            
            # Build Strapi query filters
            params = {
                "filters[route_id][$eq]": route_id,
                "filters[status][$eq]": "WAITING",
                "filters[latitude][$gte]": vehicle_lat - lat_delta,
                "filters[latitude][$lte]": vehicle_lat + lat_delta,
                "filters[longitude][$gte]": vehicle_lon - lon_delta,
                "filters[longitude][$lte]": vehicle_lon + lon_delta,
                "sort": "priority:desc",  # High priority first
                "pagination[limit]": max_results
            }
            
            async with self.session.get(
                f"{self.strapi_url}/api/active-passengers",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    passengers = data.get('data', [])
                    print(f"✅ Found {len(passengers)} eligible passengers for route {route_id}")
                    return passengers
                else:
                    error_text = await response.text()
                    print(f"❌ Error fetching passengers: HTTP {response.status} - {error_text[:200]}")
                    return []
                    
        except Exception as e:
            print(f"❌ Error fetching eligible passengers: {e}")
            import traceback
            traceback.print_exc()
            return []
