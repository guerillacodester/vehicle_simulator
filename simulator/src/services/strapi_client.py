"""
Strapi API client for simulator microservice
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import aiohttp
import json

logger = logging.getLogger(__name__)


class StrapiClient:
    """Client for communicating with Strapi backend"""
    
    def __init__(self, base_url: str, api_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'Content-Type': 'application/json'
        }
        
        if api_token:
            self.headers['Authorization'] = f'Bearer {api_token}'
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def ensure_session(self):
        """Ensure session is created"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def test_connection(self) -> bool:
        """Test connection to Strapi backend"""
        try:
            await self.ensure_session()
            async with self.session.get(f"{self.base_url}/api") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to Strapi API"""
        await self.ensure_session()
        
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"GET {url} failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}", "detail": error_text}
        
        except Exception as e:
            logger.error(f"GET {url} exception: {e}")
            return {"error": "Request failed", "detail": str(e)}
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to Strapi API"""
        await self.ensure_session()
        
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"POST {url} failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}", "detail": error_text}
        
        except Exception as e:
            logger.error(f"POST {url} exception: {e}")
            return {"error": "Request failed", "detail": str(e)}
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request to Strapi API"""
        await self.ensure_session()
        
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.put(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"PUT {url} failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}", "detail": error_text}
        
        except Exception as e:
            logger.error(f"PUT {url} exception: {e}")
            return {"error": "Request failed", "detail": str(e)}
    
    # Fleet Management API Methods
    
    async def get_vehicles(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get vehicles from Strapi"""
        params = {}
        if filters:
            params.update(filters)
        
        response = await self.get("vehicles", params=params)
        
        if "error" in response:
            logger.error(f"Failed to get vehicles: {response['error']}")
            return []
        
        return response.get("data", [])
    
    async def get_drivers(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get drivers from Strapi"""
        params = {}
        if filters:
            params.update(filters)
        
        response = await self.get("drivers", params=params)
        
        if "error" in response:
            logger.error(f"Failed to get drivers: {response['error']}")
            return []
        
        return response.get("data", [])
    
    async def get_routes(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get routes from Strapi"""
        params = {}
        if filters:
            params.update(filters)
        
        response = await self.get("routes", params=params)
        
        if "error" in response:
            logger.error(f"Failed to get routes: {response['error']}")
            return []
        
        return response.get("data", [])
    
    async def update_vehicle_status(self, vehicle_id: str, status_data: Dict) -> bool:
        """Update vehicle status in Strapi"""
        response = await self.put(f"vehicles/{vehicle_id}", {"data": status_data})
        
        if "error" in response:
            logger.error(f"Failed to update vehicle {vehicle_id}: {response['error']}")
            return False
        
        return True
    
    async def create_telemetry_record(self, telemetry_data: Dict) -> bool:
        """Create telemetry record in Strapi"""
        response = await self.post("telemetries", {"data": telemetry_data})
        
        if "error" in response:
            logger.error(f"Failed to create telemetry record: {response['error']}")
            return False
        
        return True
    
    async def bulk_create_telemetry(self, telemetry_records: List[Dict]) -> int:
        """Bulk create telemetry records"""
        success_count = 0
        
        # Process in batches to avoid overwhelming the API
        batch_size = 50
        for i in range(0, len(telemetry_records), batch_size):
            batch = telemetry_records[i:i + batch_size]
            
            tasks = [
                self.create_telemetry_record(record)
                for record in batch
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count += sum(1 for result in results if result is True)
        
        return success_count