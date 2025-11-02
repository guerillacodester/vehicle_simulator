"""
PassengerRepository - Database access layer for active passengers.

Provides persistence operations for passengers via Strapi API:
- Insert new passengers (spawned by Poisson plugin)
- Mark passengers as boarded/alighted
- Query passengers near locations
- Delete expired passengers

Based on commuter_service_deprecated/passenger_db.py pattern.
"""

import aiohttp
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

try:
    from common.config_provider import get_config
    _config_available = True
except ImportError:
    _config_available = False


class PassengerRepository:
    """Repository for Strapi active-passengers API operations."""
    
    def __init__(
        self,
        strapi_url: Optional[str] = None,
        api_token: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Strapi API client.
        
        Args:
            strapi_url: Strapi base URL. If None, loads from config.ini.
                       Defaults to "http://localhost:1337" if config unavailable.
            api_token: Strapi API token for authentication
            logger: Logger instance
        """
        # Load strapi_url from config if not provided
        if strapi_url is None:
            if _config_available:
                try:
                    config = get_config()
                    strapi_url = config.infrastructure.strapi_url
                except Exception:
                    strapi_url = "http://localhost:1337"  # Fallback default
            else:
                strapi_url = "http://localhost:1337"  # Fallback if config not available
        
        self.strapi_url = strapi_url.rstrip('/api')
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info(f"[PassengerRepository] Initialized with URL: {self.strapi_url}")
        
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
        self.logger.info("[PassengerRepository] Connected to Strapi")
    
    async def disconnect(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("[PassengerRepository] Disconnected from Strapi")
    
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
            route_position: Optional distance along route in meters
            spawned_at: Optional spawn time (uses current time if not provided)
        
        Returns:
            True if insert successful, False otherwise
        """
        if not self.session:
            self.logger.error("[PassengerRepository] Session not connected")
            return False
        
        if spawned_at is None:
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
        
        # Add route_position if provided
        if route_position is not None:
            data["data"]["route_position"] = route_position
        
        try:
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
                    self.logger.info(f"✅ Inserted passenger {passenger_id} on route {route_id}")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"❌ Error inserting passenger {passenger_id}: "
                        f"{response.status} - {response.reason}\n"
                        f"   URL: {self.strapi_url}/api/active-passengers\n"
                        f"   Response: {error_text[:200]}"
                    )
                    return False
        except Exception as e:
            self.logger.error(f"❌ Error inserting passenger {passenger_id}: {e}")
            return False
    
    async def bulk_insert_passengers(self, passengers: List[Dict]) -> tuple[int, int]:
        """
        Insert multiple passengers concurrently via Strapi API.
        
        This is much faster than sequential inserts - 30-40 passengers in ~2 seconds
        vs 30-80 seconds with sequential calls.
        
        Args:
            passengers: List of passenger dicts with keys:
                - passenger_id, route_id, latitude, longitude
                - destination_lat, destination_lon, destination_name
                - direction (optional), priority (optional), expires_minutes (optional)
                - spawned_at (optional), depot_id (optional), route_position (optional)
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not self.session:
            self.logger.error("[PassengerRepository] Session not connected")
            return (0, len(passengers))
        
        if not passengers:
            return (0, 0)
        
        import asyncio
        
        async def insert_one(passenger: Dict) -> bool:
            """Helper to insert a single passenger"""
            try:
                spawned_at = passenger.get('spawned_at') or datetime.utcnow()
                expires_minutes = passenger.get('expires_minutes', 30)
                expires_at = spawned_at + timedelta(minutes=expires_minutes)
                
                data = {
                    "data": {
                        "passenger_id": passenger['passenger_id'],
                        "route_id": passenger['route_id'],
                        "depot_id": passenger.get('depot_id'),
                        "direction": passenger.get('direction'),
                        "latitude": passenger['latitude'],
                        "longitude": passenger['longitude'],
                        "destination_name": passenger['destination_name'],
                        "destination_lat": passenger['destination_lat'],
                        "destination_lon": passenger['destination_lon'],
                        "spawned_at": spawned_at.isoformat() + "Z" if isinstance(spawned_at, datetime) else spawned_at,
                        "expires_at": expires_at.isoformat() + "Z" if isinstance(expires_at, datetime) else expires_at,
                        "status": "WAITING",
                        "priority": passenger.get('priority', 3)
                    }
                }
                
                if passenger.get('route_position') is not None:
                    data["data"]["route_position"] = passenger['route_position']
                
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                async with self.session.post(
                    f"{self.strapi_url}/api/active-passengers",
                    json=data,
                    headers=headers
                ) as response:
                    if response.status not in (200, 201):
                        error_text = await response.text()
                        self.logger.error(
                            f"Failed to insert passenger {passenger.get('passenger_id')}: "
                            f"Status {response.status}, Response: {error_text[:200]}"
                        )
                    return response.status in (200, 201)
            except Exception as e:
                self.logger.error(f"Error inserting passenger {passenger.get('passenger_id')}: {e}")
                return False
        
        # Launch inserts with concurrency limit to avoid overwhelming Strapi
        # Limit to 10 concurrent requests at a time
        semaphore = asyncio.Semaphore(10)
        
        async def rate_limited_insert(passenger):
            async with semaphore:
                return await insert_one(passenger)
        
        tasks = [rate_limited_insert(p) for p in passengers]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        successful = sum(1 for r in results if r is True)
        failed = len(passengers) - successful
        
        self.logger.info(
            f"✅ Bulk insert complete: {successful} successful, {failed} failed "
            f"({len(passengers)} total passengers)"
        )
        
        return (successful, failed)
    
    async def mark_boarded(self, passenger_id: str) -> bool:
        """
        Mark passenger as boarded via Strapi API.
        
        Args:
            passenger_id: Passenger to mark as boarded
        
        Returns:
            True if update successful, False otherwise
        """
        if not self.session:
            self.logger.error("[PassengerRepository] Session not connected")
            return False
        
        try:
            async with self.session.post(
                f"{self.strapi_url}/api/active-passengers/mark-boarded/{passenger_id}"
            ) as response:
                if response.status == 200:
                    self.logger.info(f"✅ Marked passenger {passenger_id} as boarded")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"❌ Error marking passenger {passenger_id} as boarded: "
                        f"{response.status} - {error_text}"
                    )
                    return False
        except Exception as e:
            self.logger.error(f"❌ Error marking passenger {passenger_id} as boarded: {e}")
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
            self.logger.error("[PassengerRepository] Session not connected")
            return False
        
        try:
            async with self.session.post(
                f"{self.strapi_url}/api/active-passengers/mark-alighted/{passenger_id}"
            ) as response:
                if response.status == 200:
                    self.logger.info(f"✅ Marked passenger {passenger_id} as alighted")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"❌ Error marking passenger {passenger_id} as alighted: "
                        f"{response.status} - {error_text}"
                    )
                    return False
        except Exception as e:
            self.logger.error(f"❌ Error marking passenger {passenger_id} as alighted: {e}")
            return False
    
    async def query_passengers_near_location(
        self,
        route_id: str,
        latitude: float,
        longitude: float,
        max_distance_meters: float = 1000.0
    ) -> List[Dict]:
        """
        Query passengers near a location via Strapi API.
        
        Args:
            route_id: Route ID to filter by
            latitude: Center latitude
            longitude: Center longitude
            max_distance_meters: Maximum distance in meters
        
        Returns:
            List of passenger dictionaries
        """
        if not self.session:
            self.logger.error("[PassengerRepository] Session not connected")
            return []
        
        try:
            params = {
                "filters[route_id][$eq]": route_id,
                "filters[status][$eq]": "WAITING",
                "pagination[limit]": 100
            }
            
            async with self.session.get(
                f"{self.strapi_url}/api/active-passengers",
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    passengers = result.get("data", [])
                    
                    # Filter by distance (simple great circle distance)
                    from math import radians, cos, sin, asin, sqrt
                    
                    def haversine(lat1, lon1, lat2, lon2):
                        """Calculate haversine distance in meters"""
                        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * asin(sqrt(a))
                        r = 6371000  # Radius of earth in meters
                        return c * r
                    
                    nearby = []
                    for p in passengers:
                        attrs = p.get("attributes", {})
                        p_lat = attrs.get("latitude")
                        p_lon = attrs.get("longitude")
                        
                        if p_lat is not None and p_lon is not None:
                            dist = haversine(latitude, longitude, p_lat, p_lon)
                            if dist <= max_distance_meters:
                                nearby.append({
                                    "id": p.get("id"),
                                    "passenger_id": attrs.get("passenger_id"),
                                    "latitude": p_lat,
                                    "longitude": p_lon,
                                    "destination_lat": attrs.get("destination_lat"),
                                    "destination_lon": attrs.get("destination_lon"),
                                    "destination_name": attrs.get("destination_name"),
                                    "spawned_at": attrs.get("spawned_at"),
                                    "status": attrs.get("status"),
                                    "priority": attrs.get("priority"),
                                    "distance_meters": dist
                                })
                    
                    return nearby
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"❌ Error querying passengers: {response.status} - {error_text}"
                    )
                    return []
        except Exception as e:
            self.logger.error(f"❌ Error querying passengers: {e}")
            return []

    async def get_waiting_passengers_by_route(self, route_id: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve waiting passengers filtered by route_id.

        Returns a simplified list of passenger dicts (id + attributes).
        """
        if not self.session:
            self.logger.error("[PassengerRepository] Session not connected")
            return []

        try:
            params = {
                "filters[route_id][$eq]": route_id,
                "filters[status][$eq]": "WAITING",
                "pagination[limit]": limit,
            }

            async with self.session.get(
                f"{self.strapi_url}/api/active-passengers",
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get("data", [])
                    simplified = []
                    for p in data:
                        attrs = p.get("attributes", {})
                        simplified.append({
                            "id": p.get("id"),
                            "passenger_id": attrs.get("passenger_id"),
                            "route_id": attrs.get("route_id"),
                            "depot_id": attrs.get("depot_id"),
                            "latitude": attrs.get("latitude"),
                            "longitude": attrs.get("longitude"),
                            "destination_lat": attrs.get("destination_lat"),
                            "destination_lon": attrs.get("destination_lon"),
                            "destination_name": attrs.get("destination_name"),
                            "spawned_at": attrs.get("spawned_at"),
                            "status": attrs.get("status"),
                            "priority": attrs.get("priority"),
                        })
                    return simplified
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"❌ Error querying passengers by route: {response.status} - {error_text}"
                    )
                    return []
        except Exception as e:
            self.logger.error(f"❌ Error querying passengers by route: {e}")
            return []

    async def get_waiting_passengers_by_depot(self, depot_id: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve waiting passengers filtered by depot_id.

        Returns a simplified list of passenger dicts (id + attributes).
        """
        if not self.session:
            self.logger.error("[PassengerRepository] Session not connected")
            return []

        try:
            params = {
                "filters[depot_id][$eq]": depot_id,
                "filters[status][$eq]": "WAITING",
                "pagination[limit]": limit,
            }

            async with self.session.get(
                f"{self.strapi_url}/api/active-passengers",
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get("data", [])
                    simplified = []
                    for p in data:
                        attrs = p.get("attributes", {})
                        simplified.append({
                            "id": p.get("id"),
                            "passenger_id": attrs.get("passenger_id"),
                            "route_id": attrs.get("route_id"),
                            "depot_id": attrs.get("depot_id"),
                            "latitude": attrs.get("latitude"),
                            "longitude": attrs.get("longitude"),
                            "destination_lat": attrs.get("destination_lat"),
                            "destination_lon": attrs.get("destination_lon"),
                            "destination_name": attrs.get("destination_name"),
                            "spawned_at": attrs.get("spawned_at"),
                            "status": attrs.get("status"),
                            "priority": attrs.get("priority"),
                        })
                    return simplified
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"❌ Error querying passengers by depot: {response.status} - {error_text}"
                    )
                    return []
        except Exception as e:
            self.logger.error(f"❌ Error querying passengers by depot: {e}")
            return []
    
    async def delete_expired_passengers(self) -> int:
        """
        Delete expired passengers from database.
        
        Returns:
            Number of passengers deleted
        """
        if not self.session:
            self.logger.error("[PassengerRepository] Session not connected")
            return 0
        
        try:
            now = datetime.utcnow().isoformat() + "Z"
            
            # Query expired passengers
            params = {
                "filters[expires_at][$lt]": now,
                "pagination[limit]": 1000
            }
            
            async with self.session.get(
                f"{self.strapi_url}/api/active-passengers",
                params=params
            ) as response:
                if response.status != 200:
                    return 0
                
                result = await response.json()
                expired = result.get("data", [])
                
                # Delete each expired passenger
                deleted_count = 0
                for p in expired:
                    passenger_id = p.get("id")
                    async with self.session.delete(
                        f"{self.strapi_url}/api/active-passengers/{passenger_id}"
                    ) as delete_response:
                        if delete_response.status in (200, 204):
                            deleted_count += 1
                
                if deleted_count > 0:
                    self.logger.info(f"🗑️  Deleted {deleted_count} expired passengers")
                
                return deleted_count
        except Exception as e:
            self.logger.error(f"❌ Error deleting expired passengers: {e}")
            return 0
