"""
Depot Reservoir API Integration for Strapi
=========================================
Connects Strapi visualization with the actual DepotReservoir system
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add the parent directory to import commuter_service
sys.path.append(str(Path(__file__).parent.parent.parent))

from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.strapi_api_client import StrapiApiClient

class DepotReservoirAPI:
    """Production depot reservoir API using the real DepotReservoir system"""
    
    def __init__(self):
        self.api_client = StrapiApiClient(base_url="http://localhost:1337")
        self.depot_reservoir = DepotReservoir()
        self._initialized = False
        self.depots_cache = {}
    
    async def initialize(self):
        """Initialize the depot reservoir system"""
        if not self._initialized:
            try:
                # Load depot data from Strapi
                depots = await self.api_client.get_all_depots()
                for depot in depots:
                    self.depots_cache[depot.id] = {
                        'id': depot.id,
                        'name': depot.name,
                        'location': (depot.latitude, depot.longitude),
                        'capacity': getattr(depot, 'capacity', 100)
                    }
                
                self._initialized = True
                logging.info(f"✅ Depot reservoir API initialized with {len(self.depots_cache)} depots")
                return True
            except Exception as e:
                logging.error(f"❌ Failed to initialize depot reservoir API: {e}")
                return False
        return True
    
    async def spawn_batch_commuters(self, hour: int, time_window_minutes: int, depot_ids: List[str]):
        """Spawn batch of commuters using actual depot reservoir"""
        if not await self.initialize():
            return {"error": "Failed to initialize depot reservoir"}
        
        try:
            spawned_commuters = []
            
            for depot_id in depot_ids:
                if depot_id not in self.depots_cache:
                    continue
                
                depot_info = self.depots_cache[depot_id]
                depot_location = depot_info['location']
                
                # Calculate how many commuters to spawn based on hour and depot capacity
                spawn_count = self._calculate_spawn_count(depot_info, hour, time_window_minutes)
                
                for i in range(spawn_count):
                    # Create a destination (for now, use a point along route - in real system this would be more sophisticated)
                    destination = self._generate_destination(depot_location)
                    
                    # Use the actual depot reservoir spawn_commuter method
                    commuter = await self.depot_reservoir.spawn_commuter(
                        depot_id=depot_id,
                        route_id="1A",  # Default route for now
                        depot_location=depot_location,
                        destination=destination,
                        priority=3,
                        max_wait_time=timedelta(minutes=30)
                    )
                    
                    # Convert to visualization format
                    commuter_data = {
                        "commuter_id": commuter.commuter_id,
                        "depot_id": depot_id,
                        "depot_name": depot_info['name'],
                        "route_id": "1A",
                        "current_location": {
                            "lat": depot_location[0],
                            "lon": depot_location[1]
                        },
                        "destination": {
                            "lat": destination[0],
                            "lon": destination[1]
                        },
                        "direction": commuter.direction.value if hasattr(commuter, 'direction') else "OUTBOUND",
                        "priority": commuter.priority,
                        "max_walking_distance": getattr(commuter, 'max_walking_distance_m', 500),
                        "spawn_time": commuter.spawn_time.strftime("%H:%M:%S") if hasattr(commuter, 'spawn_time') else f"{hour:02d}:00:00"
                    }
                    
                    spawned_commuters.append(commuter_data)
            
            logging.info(f"🎯 Depot reservoir spawned {len(spawned_commuters)} commuters for hour {hour}")
            
            return {
                "success": True,
                "spawned_commuters": spawned_commuters,
                "hour": hour,
                "total_commuters": len(spawned_commuters),
                "time_window_minutes": time_window_minutes,
                "depot_count": len(depot_ids)
            }
            
        except Exception as e:
            logging.error(f"❌ Error in depot reservoir batch spawn: {e}")
            return {
                "success": False,
                "error": str(e),
                "spawned_commuters": []
            }
    
    def _calculate_spawn_count(self, depot_info: Dict, hour: int, time_window_minutes: int) -> int:
        """Calculate realistic spawn count based on depot capacity and time of day"""
        base_capacity = depot_info.get('capacity', 100)
        
        # Time-based multipliers (rush hours = more passengers)
        if 7 <= hour <= 9:  # Morning rush
            multiplier = 0.8
        elif 17 <= hour <= 19:  # Evening rush
            multiplier = 0.6
        elif 6 <= hour <= 22:  # Normal hours
            multiplier = 0.3
        else:  # Night
            multiplier = 0.1
        
        # Calculate for time window
        hourly_spawn = int(base_capacity * multiplier)
        time_window_spawn = max(1, int(hourly_spawn * (time_window_minutes / 60)))
        
        return time_window_spawn
    
    def _generate_destination(self, depot_location: tuple) -> tuple:
        """Generate a realistic destination for commuter (simplified)"""
        import random
        
        # Add some random offset to simulate different destinations
        lat_offset = random.uniform(-0.01, 0.01)  # ~1km range
        lon_offset = random.uniform(-0.01, 0.01)
        
        destination_lat = depot_location[0] + lat_offset
        destination_lon = depot_location[1] + lon_offset
        
        return (destination_lat, destination_lon)

# Global instance
depot_api = DepotReservoirAPI()

async def handle_batch_spawn_request(hour: int, time_window_minutes: int, depot_ids: List[str]):
    """Handle batch spawn request from Strapi API"""
    return await depot_api.spawn_batch_commuters(hour, time_window_minutes, depot_ids)

if __name__ == "__main__":
    # Test the depot reservoir API
    async def test_api():
        result = await handle_batch_spawn_request(hour=8, time_window_minutes=5, depot_ids=["depot_1"])
        print(f"Test result: {json.dumps(result, indent=2)}")
    
    asyncio.run(test_api())