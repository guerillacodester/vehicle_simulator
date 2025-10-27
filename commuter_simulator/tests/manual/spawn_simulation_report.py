"""
Spawn Simulation Report Generator
----------------------------------
Simulates realistic commuter spawning along a route during peak hours.

Generates a detailed table showing:
- Spawn coordinates (lat/lon)
- Address (from reverse geocoding)
- Distance from route
- Spawn time
- Building type
- Weight/probability
- Compute time per spawn

Run with:
    python commuter_simulator/tests/manual/spawn_simulation_report.py
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
import math

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.spawn.config_loader import SpawnConfigLoader
from infrastructure.geospatial.client import GeospatialClient


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lon points"""
    R = 6371000  # Earth radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def poisson_random(lambda_val: float) -> int:
    """Simple Poisson random number generator"""
    import random
    import math
    
    L = math.exp(-lambda_val)
    k = 0
    p = 1.0
    
    while p > L:
        k += 1
        p *= random.random()
    
    return k - 1


async def simulate_spawns_for_route(
    route_id: int,
    start_hour: int,
    end_hour: int,
    spawn_interval_minutes: int = 1
):
    """
    Simulate spawning along a route during peak hours.
    
    Args:
        route_id: Route ID to simulate
        start_hour: Start hour (0-23)
        end_hour: End hour (0-23)
        spawn_interval_minutes: Minutes between spawn cycles
    """
    
    print("=" * 120)
    print(f"SPAWN SIMULATION REPORT - Route {route_id}")
    print(f"Peak Hours: {start_hour:02d}:00 - {end_hour:02d}:00 | Interval: {spawn_interval_minutes} min")
    print("=" * 120)
    
    # Initialize clients
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    geo_client = GeospatialClient(base_url="http://localhost:8001")
    
    # Load spawn config
    print("\n[1] Loading spawn configuration...")
    config = await config_loader.get_config_by_country("Barbados")
    if not config:
        print("[ERR] Failed to load config")
        return
    
    dist_params = config_loader.get_distribution_params(config)
    print(f"[OK] Config loaded: {config['name']}")
    print(f"   Poisson lambda: {dist_params['poisson_lambda']}")
    print(f"   Max spawns/cycle: {dist_params['max_spawns_per_cycle']}")
    print(f"   Spawn radius: {dist_params['spawn_radius_meters']}m")
    
    # Query buildings near route
    # For this simulation, we'll use a central point in Bridgetown as a proxy for Route 1
    # In production, you would fetch actual route geometry from Strapi
    route_center_lat = 13.0969  # Bridgetown, Barbados
    route_center_lon = -59.6145
    
    print(f"\n[2] Querying buildings within {dist_params['spawn_radius_meters']}m of route center...")
    print(f"   Route center: ({route_center_lat}, {route_center_lon})")
    query_start = time.time()
    
    try:
        result = geo_client.find_nearby_buildings(
            latitude=route_center_lat,
            longitude=route_center_lon,
            radius_meters=dist_params['spawn_radius_meters'],
            limit=100
        )
        buildings = result.get('buildings', [])
        query_time = (time.time() - query_start) * 1000
        
        print(f"[OK] Found {len(buildings)} buildings ({query_time:.2f}ms)")
        
        if len(buildings) == 0:
            print("[WARN] No buildings found near route. Cannot simulate spawns.")
            return
            
    except Exception as e:
        print(f"[ERR] Failed to query buildings: {e}")
        return
    
    # Get route center point for distance calculations
    print(f"\n[3] Using route center for distance calculations...")
    route_center = (route_center_lat, route_center_lon)
    print(f"[OK] Route center: {route_center}")
    
    # Calculate weights for all buildings
    print(f"\n[4] Calculating spawn weights for all buildings...")
    weighted_buildings = []
    
    for building in buildings[:50]:  # Limit to first 50 for performance
        building_type = building.get('building_type', 'residential')
        
        # Get weight from config
        weight = config_loader.get_building_weight(
            config, 
            building_type, 
            apply_peak_multiplier=True
        )
        
        if weight > 0:
            weighted_buildings.append({
                'id': building.get('osm_id', building.get('id', 'unknown')),
                'type': building_type,
                'latitude': building['latitude'],
                'longitude': building['longitude'],
                'weight': weight,
                'distance_from_route': haversine_distance(
                    route_center[0], route_center[1],
                    building['latitude'], building['longitude']
                )
            })
    
    print(f"[OK] {len(weighted_buildings)} buildings with active weights")
    
    if len(weighted_buildings) == 0:
        print("[WARN] No weighted buildings found. Check spawn-config settings.")
        return
    
    # Simulate spawning during peak hours
    print(f"\n[5] Simulating spawns from {start_hour:02d}:00 to {end_hour:02d}:00...")
    print("\n" + "=" * 120)
    
    # Table header
    header = f"{'Time':<8} | {'Lat':<10} | {'Lon':<11} | {'Building Type':<15} | {'Weight':<7} | {'Distance':<9} | {'Address':<35} | {'Compute':<10}"
    print(header)
    print("=" * 120)
    
    all_spawns = []
    total_compute_time = 0
    
    # Simulate each hour
    current_time = datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_time = datetime.now().replace(hour=end_hour, minute=0, second=0, microsecond=0)
    
    while current_time < end_time:
        hour = current_time.hour
        day_of_week = "monday"  # For consistency
        
        # Get hourly rate
        hourly_rate = config_loader.get_hourly_rate(config, hour)
        day_mult = config_loader.get_day_multiplier(config, day_of_week)
        
        # Calculate adjusted lambda
        adjusted_lambda = dist_params['poisson_lambda'] * hourly_rate * day_mult
        
        # Generate number of spawns for this cycle
        num_spawns = poisson_random(adjusted_lambda)
        num_spawns = min(num_spawns, dist_params['max_spawns_per_cycle'])
        
        # Calculate total weight for probability normalization
        total_weight = sum(b['weight'] * hourly_rate * day_mult for b in weighted_buildings)
        
        # Weighted random selection
        for _ in range(num_spawns):
            spawn_start = time.time()
            
            # Select building based on weights
            rand_val = random.random() * total_weight
            cumulative = 0
            selected_building = None
            
            for building in weighted_buildings:
                building_weight = building['weight'] * hourly_rate * day_mult
                cumulative += building_weight
                if rand_val <= cumulative:
                    selected_building = building
                    break
            
            if not selected_building:
                selected_building = weighted_buildings[-1]  # Fallback
            
            # Reverse geocode to get address
            try:
                address_result = geo_client.reverse_geocode(
                    selected_building['latitude'],
                    selected_building['longitude']
                )
                
                # Extract address from API response
                address = address_result.get('address', 'Address not found')
                
                # Truncate long addresses
                if len(address) > 35:
                    address = address[:32] + "..."
            except Exception as e:
                address = f"Error: {str(e)[:20]}"
            
            compute_time = (time.time() - spawn_start) * 1000
            total_compute_time += compute_time
            
            # Calculate final weight for this spawn
            final_weight = building_weight
            
            # Record spawn
            spawn = {
                'time': current_time.strftime("%H:%M"),
                'latitude': selected_building['latitude'],
                'longitude': selected_building['longitude'],
                'building_type': selected_building['type'],
                'weight': final_weight,
                'distance': selected_building['distance_from_route'],
                'address': address,
                'compute_ms': compute_time
            }
            
            all_spawns.append(spawn)
            
            # Print row
            row = (
                f"{spawn['time']:<8} | "
                f"{spawn['latitude']:<10.6f} | "
                f"{spawn['longitude']:<11.6f} | "
                f"{spawn['building_type']:<15} | "
                f"{spawn['weight']:<7.2f} | "
                f"{spawn['distance']:<9.1f}m | "
                f"{spawn['address']:<35} | "
                f"{spawn['compute_ms']:<10.2f}ms"
            )
            print(row)
        
        # Move to next spawn cycle
        current_time += timedelta(minutes=spawn_interval_minutes)
    
    # Summary statistics
    print("=" * 120)
    print(f"\n{'SUMMARY STATISTICS':<120}")
    print("=" * 120)
    print(f"Total spawns: {len(all_spawns)}")
    print(f"Total compute time: {total_compute_time:.2f}ms")
    print(f"Average compute per spawn: {total_compute_time/len(all_spawns) if all_spawns else 0:.2f}ms")
    print(f"Time range: {start_hour:02d}:00 - {end_hour:02d}:00")
    print(f"Buildings queried: {len(weighted_buildings)}")
    
    # Building type breakdown
    type_counts = {}
    for spawn in all_spawns:
        btype = spawn['building_type']
        type_counts[btype] = type_counts.get(btype, 0) + 1
    
    print(f"\nSpawns by building type:")
    for btype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(all_spawns) * 100) if all_spawns else 0
        print(f"  {btype:<15}: {count:>4} ({pct:>5.1f}%)")
    
    # Distance statistics
    if all_spawns:
        distances = [s['distance'] for s in all_spawns]
        print(f"\nDistance from route:")
        print(f"  Min: {min(distances):.1f}m")
        print(f"  Max: {max(distances):.1f}m")
        print(f"  Avg: {sum(distances)/len(distances):.1f}m")
    
    print("\n" + "=" * 120)
    
    return all_spawns


async def main():
    """Run spawn simulation"""
    
    # Simulate morning peak (6am - 10am)
    print("\n[MORNING PEAK SIMULATION]")
    morning_spawns = await simulate_spawns_for_route(
        route_id=1,
        start_hour=6,
        end_hour=10,
        spawn_interval_minutes=15  # Every 15 minutes
    )
    
    # Simulate evening peak (4pm - 7pm)
    print("\n\n[EVENING PEAK SIMULATION]")
    evening_spawns = await simulate_spawns_for_route(
        route_id=1,
        start_hour=16,
        end_hour=19,
        spawn_interval_minutes=15
    )
    
    print("\n[SIMULATION COMPLETE]")


if __name__ == "__main__":
    asyncio.run(main())
