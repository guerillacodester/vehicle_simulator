"""
GTFS API Client
==============
HTTP client for interacting with GTFS FastAPI endpoints
Platform-agnostic and designed for distributed deployment
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class GTFSAPIClient:
    """Client for interacting with GTFS FastAPI endpoints"""
    
    def __init__(self, base_url: Optional[str] = None):
        # Use environment variable or default to localhost
        self.base_url = base_url or os.getenv("GTFS_API_URL", "http://localhost:8000/api/v1")
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make HTTP request to GTFS API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"API request failed: {method} {url} - {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in API request: {e}")
                raise
    
    # Country operations
    async def get_countries(self) -> List[Dict[str, Any]]:
        """Get all countries"""
        return await self._make_request("GET", "/countries")
    
    async def create_country(self, country_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new country"""
        return await self._make_request("POST", "/countries", json=country_data)
    
    async def get_country(self, country_id: str) -> Dict[str, Any]:
        """Get specific country by ID"""
        return await self._make_request("GET", f"/countries/{country_id}")
    
    # Vehicle operations
    async def get_vehicles(self, country_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get vehicles, optionally filtered by country"""
        params = {"skip": skip, "limit": limit}
        if country_id:
            params["country_id"] = country_id
        return await self._make_request("GET", "/vehicles", params=params)
    
    async def create_vehicle(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new vehicle"""
        return await self._make_request("POST", "/vehicles", json=vehicle_data)
    
    async def get_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        """Get specific vehicle by ID"""
        return await self._make_request("GET", f"/vehicles/{vehicle_id}")
    
    async def update_vehicle(self, vehicle_id: str, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update vehicle"""
        return await self._make_request("PUT", f"/vehicles/{vehicle_id}", json=vehicle_data)
    
    # Route operations
    async def get_routes(self, country_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get routes, optionally filtered by country"""
        params = {"skip": skip, "limit": limit}
        if country_id:
            params["country_id"] = country_id
        return await self._make_request("GET", "/routes", params=params)
    
    async def create_route(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new route"""
        return await self._make_request("POST", "/routes", json=route_data)
    
    async def get_route(self, route_id: str) -> Dict[str, Any]:
        """Get specific route by ID"""
        return await self._make_request("GET", f"/routes/{route_id}")
    
    # Stop operations
    async def get_stops(self, country_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get stops, optionally filtered by country"""
        params = {"skip": skip, "limit": limit}
        if country_id:
            params["country_id"] = country_id
        return await self._make_request("GET", "/stops", params=params)
    
    async def create_stop(self, stop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new stop"""
        return await self._make_request("POST", "/stops", json=stop_data)
    
    # Trip operations
    async def get_trips(self, route_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trips, optionally filtered by route"""
        params = {"skip": skip, "limit": limit}
        if route_id:
            params["route_id"] = route_id
        return await self._make_request("GET", "/trips", params=params)
    
    async def create_trip(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new trip"""
        return await self._make_request("POST", "/trips", json=trip_data)
    
    # Timetable operations
    async def get_timetables(self, vehicle_id: Optional[str] = None, route_id: Optional[str] = None, 
                           skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get timetables, optionally filtered"""
        params = {"skip": skip, "limit": limit}
        if vehicle_id:
            params["vehicle_id"] = vehicle_id
        if route_id:
            params["route_id"] = route_id
        return await self._make_request("GET", "/timetables", params=params)
    
    async def create_timetable(self, timetable_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new timetable entry"""
        return await self._make_request("POST", "/timetables", json=timetable_data)
    
    # Batch operations for fleet management
    async def bulk_create_vehicles(self, vehicles_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple vehicles at once"""
        results = []
        for vehicle_data in vehicles_data:
            try:
                result = await self.create_vehicle(vehicle_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to create vehicle: {e}")
                # Continue with other vehicles
        return results
    
    async def bulk_create_routes(self, routes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple routes at once"""
        results = []
        for route_data in routes_data:
            try:
                result = await self.create_route(route_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to create route: {e}")
                # Continue with other routes
        return results
