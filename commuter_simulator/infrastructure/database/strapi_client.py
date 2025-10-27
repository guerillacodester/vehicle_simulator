"""
Strapi API Client - Single Source of Truth
==========================================

This is the ONLY place where API access to Strapi is defined.
All other modules must use this client.

Architecture:
- infrastructure/database/strapi_client.py (this file) - HTTP client
- core/repositories/*.py - Domain-specific data access using this client
"""

import asyncio
import logging
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class DepotData:
    """Depot information from Strapi API"""
    id: int
    depot_id: str
    name: str
    address: Optional[str]
    location: Optional[Dict[str, float]]  # {lat: float, lon: float}
    latitude: Optional[float]
    longitude: Optional[float]
    capacity: int
    is_active: bool
    activity_level: float = 1.0


@dataclass
class RouteData:
    """Route information from Strapi API"""
    id: int
    short_name: str
    long_name: str
    parishes: Optional[List[str]]
    description: Optional[str]
    color: Optional[str]
    is_active: bool
    geometry_coordinates: List[List[float]]
    route_length_km: float
    coordinate_count: int
    activity_level: float = 1.0


@dataclass
class PassengerData:
    """Passenger/Commuter information"""
    id: int
    commuter_id: str
    name: str
    spawn_location: Dict[str, float]
    destination_location: Dict[str, float]
    assigned_route: str
    priority: int
    spawn_time: str
    status: str


class StrapiApiClient:
    """
    Single Source of Truth for all Strapi API access.
    
    Usage:
        async with StrapiApiClient("http://localhost:1337") as client:
            depots = await client.get_all_depots()
            routes = await client.get_all_routes()
    """
    
    def __init__(self, base_url: str = "http://localhost:1337"):
        self.base_url = base_url
        self.session: Optional[httpx.AsyncClient] = None
        self._connected = False
        self.logger = logging.getLogger(__name__)
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self) -> bool:
        """Initialize and test connection"""
        try:
            if not self.session:
                self.session = httpx.AsyncClient(timeout=30.0)
            
            response = await self.session.get(f"{self.base_url}/api/countries", timeout=5.0)
            if response.status_code == 200:
                self._connected = True
                self.logger.info(f"✓ Connected to Strapi API: {self.base_url}")
                return True
            else:
                self.logger.error(f"✗ API connection failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"✗ Failed to connect to API: {e}")
            return False
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
            self._connected = False
    
    def _ensure_connected(self):
        """Verify connection before API calls"""
        if not self.session or not self._connected:
            raise RuntimeError("API client not connected. Use async context manager or call connect() first.")
    
    # ========================================================================
    # DEPOT API
    # ========================================================================
    
    async def get_all_depots(self) -> List[DepotData]:
        """Retrieve all active depots"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/depots",
                params={
                    "filters[is_active][$eq]": True,
                    "pagination[pageSize]": 100
                }
            )
            response.raise_for_status()
            data = response.json()
            
            depots = []
            for item in data.get('data', []):
                attrs = item.get('attributes', item)
                
                # Get activity_level, default to 1.0 if not provided or None
                activity_level = attrs.get('activity_level', 1.0)
                if activity_level is None:
                    activity_level = 1.0
                else:
                    activity_level = float(activity_level)
                
                depot = DepotData(
                    id=item['id'],
                    depot_id=attrs.get('depot_id', f"DEPOT_{item['id']}"),
                    name=attrs.get('name', f"Depot {item['id']}"),
                    address=attrs.get('address'),
                    location=attrs.get('location'),
                    latitude=attrs.get('latitude'),
                    longitude=attrs.get('longitude'),
                    capacity=attrs.get('capacity', 50),
                    is_active=attrs.get('is_active', True),
                    activity_level=activity_level
                )
                depots.append(depot)
            
            self.logger.info(f"✓ Retrieved {len(depots)} depots")
            return depots
            
        except Exception as e:
            self.logger.error(f"✗ Failed to get depots: {e}")
            return []
    
    # ========================================================================
    # ROUTE API
    # ========================================================================
    
    async def get_all_routes(self) -> List[RouteData]:
        """Retrieve all active routes with geometry"""
        self._ensure_connected()
        
        try:
            response = await self.session.get(
                f"{self.base_url}/api/routes",
                params={
                    "filters[is_active][$eq]": True,
                    "pagination[pageSize]": 100
                }
            )
            response.raise_for_status()
            data = response.json()
            
            routes = []
            for item in data.get('data', []):
                attrs = item.get('attributes', item)
                
                # Get geometry coordinates
                geometry = attrs.get('geometry_coordinates', [])
                if isinstance(geometry, str):
                    import json
                    geometry = json.loads(geometry)
                
                route = RouteData(
                    id=item['id'],
                    short_name=attrs.get('short_name', f"Route {item['id']}"),
                    long_name=attrs.get('long_name', f"Route {item['id']}"),
                    parishes=attrs.get('parishes', []),
                    description=attrs.get('description'),
                    color=attrs.get('color'),
                    is_active=attrs.get('is_active', True),
                    geometry_coordinates=geometry,
                    route_length_km=attrs.get('route_length_km', 0.0),
                    coordinate_count=len(geometry),
                    activity_level=float(attrs.get('activity_level', 1.0))
                )
                routes.append(route)
            
            self.logger.info(f"✓ Retrieved {len(routes)} routes")
            return routes
            
        except Exception as e:
            self.logger.error(f"✗ Failed to get routes: {e}")
            return []
    
    # ========================================================================
    # PASSENGER API
    # ========================================================================
    
    async def create_passenger(self, passenger_data: Dict[str, Any]) -> Optional[PassengerData]:
        """Create a new passenger in the database"""
        self._ensure_connected()
        
        try:
            response = await self.session.post(
                f"{self.base_url}/api/commuters",
                json={"data": passenger_data}
            )
            response.raise_for_status()
            data = response.json()
            
            item = data.get('data', {})
            attrs = item.get('attributes', item)
            
            passenger = PassengerData(
                id=item['id'],
                commuter_id=attrs.get('commuter_id'),
                name=attrs.get('name'),
                spawn_location=attrs.get('spawn_location'),
                destination_location=attrs.get('destination_location'),
                assigned_route=attrs.get('assigned_route'),
                priority=attrs.get('priority', 3),
                spawn_time=attrs.get('spawn_time'),
                status=attrs.get('status', 'waiting')
            )
            
            return passenger
            
        except Exception as e:
            self.logger.error(f"✗ Failed to create passenger: {e}")
            return None
    
    async def update_passenger_status(self, passenger_id: int, status: str) -> bool:
        """Update passenger status"""
        self._ensure_connected()
        
        try:
            response = await self.session.put(
                f"{self.base_url}/api/commuters/{passenger_id}",
                json={"data": {"status": status}}
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Failed to update passenger status: {e}")
            return False
