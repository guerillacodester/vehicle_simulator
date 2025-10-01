#!/usr/bin/env python3
"""
Simple API bridge for arknet_transit_simulator to access Strapi backend
This provides the FastAPI-compatible endpoints that the simulator expects
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import aiohttp
from aiohttp import web, ClientSession
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class StrapiAPIBridge:
    def __init__(self, strapi_url: str = "http://localhost:1337", port: int = 8000):
        self.strapi_url = strapi_url.rstrip('/')
        self.port = port
        self.session: Optional[ClientSession] = None
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup routes that match what the simulator expects"""
        # Health check
        self.app.router.add_get('/health', self.health_check)
        
        # Vehicle and assignment endpoints  
        self.app.router.add_get('/api/v1/search/vehicle-driver-pairs', self.get_vehicle_driver_pairs)
        self.app.router.add_get('/api/v1/vehicles/public', self.get_vehicles_public)
        
        # Route endpoints
        self.app.router.add_get('/api/v1/routes/public/{code}', self.get_route_public)
        self.app.router.add_get('/api/v1/routes/public/{code}/geometry', self.get_route_geometry)
        
        # Enable CORS
        self.app.router.add_options('/{path:.*}', self.cors_handler)
    
    async def start(self):
        """Start the bridge server"""
        self.session = aiohttp.ClientSession()
        logger.info(f"🌉 Starting API Bridge on port {self.port}")
        logger.info(f"🎯 Proxying to Strapi at {self.strapi_url}")
        
        # Test Strapi connection
        try:
            async with self.session.get(f"{self.strapi_url}/admin") as response:
                if response.status < 500:
                    logger.info("✅ Strapi backend is accessible")
                else:
                    logger.warning("⚠️  Strapi backend may not be running properly")
        except Exception as e:
            logger.error(f"❌ Cannot connect to Strapi: {e}")
            logger.info("📝 Make sure Strapi is running on port 1337")
        
        return web.AppRunner(self.app)
    
    async def stop(self):
        """Stop the bridge server"""
        if self.session:
            await self.session.close()
    
    async def cors_handler(self, request: web.Request) -> web.Response:
        """Handle CORS preflight requests"""
        return web.Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            }
        )
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "ok",
            "service": "arknet-api-bridge",
            "strapi_url": self.strapi_url,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def get_vehicle_driver_pairs(self, request: web.Request) -> web.Response:
        """Get vehicle-driver assignment pairs for simulator"""
        try:
            # Since Strapi requires authentication for now, return mock data
            # In a real setup, this would query Strapi with proper auth
            mock_assignments = [
                {
                    # Fields the simulator expects
                    "driver_employment_status": "active",
                    "registration": "ZR001", 
                    "route_code": "1",
                    "driver_license": "DRV001",
                    "assignment_date": "2025-09-17T18:00:00Z",
                    "driver_name": "John Driver",
                    "route_name": "Route 1 - Main Line", 
                    "vehicle_status": "available"  # Changed from "active" to "available"  
                }
            ]
            
            logger.info(f"📋 Returning {len(mock_assignments)} vehicle-driver assignments")
            return web.json_response(mock_assignments)
            
        except Exception as e:
            logger.error(f"❌ Error in get_vehicle_driver_pairs: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def get_vehicles_public(self, request: web.Request) -> web.Response:
        """Get public vehicles data"""
        try:
            mock_vehicles = [
                {
                    "id": 1,
                    "registration": "ZR001",
                    "reg_code": "ZR001",  # depot manager looks for this field
                    "type": "bus",
                    "capacity": 40,
                    "status": "available",  # changed from "active" to "available"
                    "driver": {
                        "id": 1,
                        "name": "John Driver",
                        "license_number": "DRV001"
                    },
                    "route": {
                        "id": 1,
                        "code": "1", 
                        "name": "Route 1 - Main Line"
                    },
                    "depot": {
                        "id": 1,
                        "name": "Main Depot"
                    }
                }
            ]
            
            logger.info(f"🚌 Returning {len(mock_vehicles)} vehicles")
            return web.json_response(mock_vehicles)
            
        except Exception as e:
            logger.error(f"❌ Error in get_vehicles_public: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def get_route_public(self, request: web.Request) -> web.Response:
        """Get public route data by code"""
        try:
            route_code = request.match_info['code']
            
            mock_route = {
                "id": 1,
                "code": route_code,
                "long_name": f"Route {route_code} - Main Line",  # simulator expects 'long_name'
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-59.6463, 13.2810],
                        [-59.6464, 13.2811], 
                        [-59.6465, 13.2812],
                        [-59.6466, 13.2813]
                    ]
                }
            }
            
            logger.info(f"🗺️  Returning route data for code: {route_code}")
            return web.json_response(mock_route)
            
        except Exception as e:
            logger.error(f"❌ Error in get_route_public: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def get_route_geometry(self, request: web.Request) -> web.Response:
        """Get route geometry by code"""
        try:
            route_code = request.match_info['code']
            
            # The simulator expects geometry wrapped in a 'geometry' field
            mock_geometry_response = {
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-59.6463, 13.2810],
                        [-59.6464, 13.2811],
                        [-59.6465, 13.2812], 
                        [-59.6466, 13.2813]
                    ]
                }
            }
            
            logger.info(f"📍 Returning geometry for route: {route_code}")
            return web.json_response(mock_geometry_response)
            
        except Exception as e:
            logger.error(f"❌ Error in get_route_geometry: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)

async def main():
    parser = argparse.ArgumentParser(description='Strapi API Bridge for arknet_transit_simulator')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the bridge on (default: 8000)')
    parser.add_argument('--strapi-url', default='http://localhost:1337', help='Strapi backend URL')
    args = parser.parse_args()
    
    bridge = StrapiAPIBridge(strapi_url=args.strapi_url, port=args.port)
    
    try:
        runner = await bridge.start()
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', args.port)
        await site.start()
        
        logger.info(f"🚀 API Bridge started successfully!")
        logger.info(f"📡 Simulator can now connect to: http://localhost:{args.port}")
        logger.info(f"🔗 Health check: http://localhost:{args.port}/health")
        logger.info("Press Ctrl+C to stop")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down API Bridge...")
    except Exception as e:
        logger.error(f"❌ Error running bridge: {e}")
    finally:
        await bridge.stop()

if __name__ == '__main__':
    asyncio.run(main())