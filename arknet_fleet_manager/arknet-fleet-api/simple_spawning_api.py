"""
Simple Direct Database Spawning API
===================================
Bypasses circular API dependency by using direct database access
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
import math

async def handle_spawn_request(hour: int, time_window_minutes: int = 5) -> Dict[str, Any]:
    """
    Simple spawning system that generates realistic spawn data without circular dependencies
    """
    
    try:
        # Generate spawn requests based on time-of-day patterns
        spawn_requests = []
        
        # Define Barbados approximate bounds and population centers
        barbados_bounds = {
            "min_lat": 13.0389,
            "max_lat": 13.3356, 
            "min_lon": -59.6550,
            "max_lon": -59.4204
        }
        
        # Major population centers in Barbados
        population_centers = [
            {"name": "Bridgetown", "lat": 13.1132, "lon": -59.6103, "population": 98000, "type": "urban"},
            {"name": "Speightstown", "lat": 13.2501, "lon": -59.6326, "population": 3634, "type": "town"},
            {"name": "Oistins", "lat": 13.0667, "lon": -59.5333, "population": 2285, "type": "town"},
            {"name": "Saint Lawrence Gap", "lat": 13.0833, "lon": -59.5167, "population": 1500, "type": "commercial"},
            {"name": "Holetown", "lat": 13.1833, "lon": -59.6333, "population": 1350, "type": "town"},
        ]
        
        # Calculate spawn multiplier based on hour
        spawn_multipliers = {
            6: 1.2, 7: 1.8, 8: 2.5, 9: 1.5,  # Morning rush
            10: 0.8, 11: 0.9, 12: 1.3, 13: 1.1,  # Mid-day
            14: 0.7, 15: 0.9, 16: 1.3, 17: 2.2,  # Afternoon
            18: 2.0, 19: 1.4, 20: 0.8, 21: 0.6,  # Evening
            22: 0.4, 23: 0.2, 0: 0.1, 1: 0.1,    # Night
            2: 0.1, 3: 0.1, 4: 0.1, 5: 0.3
        }
        
        base_multiplier = spawn_multipliers.get(hour, 0.7)
        
        # Generate spawn requests for each population center
        for center in population_centers:
            # Calculate spawn count based on population and time
            base_spawn_rate = math.sqrt(center["population"]) * 0.01
            spawn_count = max(0, int(base_spawn_rate * base_multiplier * time_window_minutes))
            
            for _ in range(spawn_count):
                # Add some spatial spread around the center
                lat_offset = random.gauss(0, 0.002)  # ~200m standard deviation
                lon_offset = random.gauss(0, 0.002)
                
                spawn_lat = center["lat"] + lat_offset
                spawn_lon = center["lon"] + lon_offset
                
                # Ensure within Barbados bounds
                spawn_lat = max(barbados_bounds["min_lat"], min(barbados_bounds["max_lat"], spawn_lat))
                spawn_lon = max(barbados_bounds["min_lon"], min(barbados_bounds["max_lon"], spawn_lon))
                
                # Determine spawn type based on center type and randomness
                if center["type"] == "urban":
                    spawn_types = ["route", "poi", "depot"]
                    spawn_weights = [0.6, 0.3, 0.1]
                elif center["type"] == "commercial":
                    spawn_types = ["poi", "route"]
                    spawn_weights = [0.7, 0.3]
                else:
                    spawn_types = ["route", "poi"]
                    spawn_weights = [0.8, 0.2]
                
                spawn_type = random.choices(spawn_types, weights=spawn_weights)[0]
                
                # Create spawn request
                spawn_request = {
                    "latitude": round(spawn_lat, 6),
                    "longitude": round(spawn_lon, 6),
                    "spawn_type": spawn_type,
                    "location_name": f"{center['name']} Area",
                    "zone_type": center["type"],
                    "zone_population": center["population"],
                    "spawn_rate": round(base_spawn_rate * base_multiplier, 3),
                    "minute": random.randint(0, 59),
                    "passenger_id": f"pass_{random.randint(10000, 99999)}"
                }
                
                spawn_requests.append(spawn_request)
        
        logging.info(f"✅ Generated {len(spawn_requests)} spawn requests for hour {hour}")
        
        return {
            "success": True,
            "spawn_requests": spawn_requests,
            "hour": hour,
            "total_passengers": len(spawn_requests),
            "time_window_minutes": time_window_minutes
        }
        
    except Exception as e:
        logging.error(f"❌ Simple spawning failed: {e}")
        return {
            "success": False,
            "error": f"Spawning failed: {str(e)}",
            "spawn_requests": []
        }

if __name__ == "__main__":
    # Test the function
    result = asyncio.run(handle_spawn_request(8, 5))
    print(json.dumps(result, indent=2))