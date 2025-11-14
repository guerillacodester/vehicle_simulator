"""
Production Passenger Spawning API Endpoint for Strapi
====================================================
Integrates the PoissonGeoJSONSpawner with Strapi for real-time spawning
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to import commuter_service
sys.path.append(str(Path(__file__).parent.parent.parent))

from commuter_service.poisson_geojson_spawner import PoissonGeoJSONSpawner
from commuter_service.strapi_api_client import StrapiApiClient

class ProductionSpawningAPI:
    """Production spawning API using the real Poisson GeoJSON system"""
    
    def __init__(self):
        self.api_client = StrapiApiClient(base_url="http://localhost:1337")
        self.spawner = PoissonGeoJSONSpawner(self.api_client)
        self._initialized = False
    
    async def initialize(self):
        """Initialize the spawning system"""
        if not self._initialized:
            success = await self.spawner.initialize(country_code="barbados")
            if success:
                self._initialized = True
                logging.info("✅ Production spawning API initialized")
                return True
            else:
                logging.error("❌ Failed to initialize production spawning API")
                return False
        return True
    
    async def generate_spawn_requests(self, hour: int, time_window_minutes: int = 5):
        """Generate spawn requests for given hour using production system"""
        if not await self.initialize():
            return {"error": "Failed to initialize spawning system"}
        
        try:
            # Create datetime object for the current hour
            current_time = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # Generate spawn requests using production Poisson system
            spawn_requests = await self.spawner.generate_poisson_spawn_requests(
                current_time=current_time,
                time_window_minutes=time_window_minutes
            )
            
            # Convert to visualization format
            visualization_requests = []
            for request in spawn_requests:
                viz_request = {
                    "latitude": request.get("spawn_location", {}).get("latitude"),
                    "longitude": request.get("spawn_location", {}).get("longitude"),
                    "spawn_type": self._determine_spawn_type(request),
                    "location_name": request.get("location_name", "Unknown"),
                    "zone_type": request.get("zone_type", "unknown"),
                    "zone_population": request.get("zone_population", 0),
                    "spawn_rate": request.get("spawn_rate", 0.0),
                    "minute": request.get("spawn_time", current_time).minute
                }
                
                # Only add valid coordinates
                if viz_request["latitude"] and viz_request["longitude"]:
                    visualization_requests.append(viz_request)
            
            logging.info(f"🎯 Generated {len(visualization_requests)} spawn requests for hour {hour}")
            
            return {
                "success": True,
                "spawn_requests": visualization_requests,
                "hour": hour,
                "total_passengers": len(visualization_requests),
                "time_window_minutes": time_window_minutes
            }
            
        except Exception as e:
            logging.error(f"❌ Error generating spawn requests: {e}")
            return {
                "success": False,
                "error": str(e),
                "spawn_requests": []
            }
    
    def _determine_spawn_type(self, request):
        """Determine spawn type based on request data"""
        zone_type = request.get("zone_type", "").lower()
        
        if "depot" in zone_type:
            return "depot"
        elif zone_type in ["residential", "commercial", "retail", "amenity"]:
            return "poi"
        else:
            return "route"

# Global instance
production_api = ProductionSpawningAPI()

async def handle_spawn_request(hour: int, time_window_minutes: int = 5):
    """Handle spawn request from web API"""
    return await production_api.generate_spawn_requests(hour, time_window_minutes)

if __name__ == "__main__":
    # Test the production API
    async def test_api():
        result = await handle_spawn_request(hour=8, time_window_minutes=5)
        print(f"Test result: {result}")
    
    asyncio.run(test_api())