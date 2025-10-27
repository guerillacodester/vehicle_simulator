"""
Realistic Route 1 spawn simulation with proper statistical distributions.
"""
import asyncio
import httpx
import random
import time
from datetime import datetime, timedelta
import math
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader


def weighted_random_choice(weights):
    """Select index based on weights."""
    total = sum(weights)
    r = random.uniform(0, total)
    cumsum = 0
    for i, w in enumerate(weights):
        cumsum += w
        if r <= cumsum:
            return i
    return len(weights) - 1


def boarding_probability(position_fraction):
    """
    Probability of boarding at position along route.
    Heavy boarding at start (0-40%), decreasing toward end.
    Uses exponential decay.
    """
    return math.exp(-2.5 * position_fraction)


def alighting_probability(boarding_pos, alighting_pos):
    """
    Probability of alighting at position, given boarding position.
    - Must be after boarding (can't go backwards)
    - Peaks around 60-80% of route (commercial/school zone)
    - Lower probability for very short trips
    """
    if alighting_pos <= boarding_pos:
        return 0
    
    trip_fraction = alighting_pos - boarding_pos
    
    # Discourage very short trips (< 10% of route)
    if trip_fraction < 0.1:
        return 0.1
    
    # Peak probability around 60-80% of route
    # Use beta-like distribution centered on destination zones
    if 0.5 <= alighting_pos <= 0.9:
        return 1.0  # High probability in commercial/school zone
    elif alighting_pos < 0.5:
        return 0.3  # Lower probability early in route
    else:
        return 0.7  # Medium probability at terminus


async def get_route_1_coordinates():
    """Fetch Route 1 geometry from Strapi."""
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:1337/api/routes?populate=*&filters[short_name][$eq]=1")
        resp.raise_for_status()
        data = resp.json()
        
        if not data['data']:
            raise ValueError("Route 1 not found")
        
        route = data['data'][0]
        
        # Extract all coordinates from all features
        all_coords = []
        for feature in route['geojson_data']['features']:
            coords = feature['geometry']['coordinates']
            for coord in coords:
                if isinstance(coord, str):
                    lon, lat = map(float, coord.split())
                else:
                    lon, lat = coord[0], coord[1]
                all_coords.append((lat, lon))
        
        return all_coords, route


async def main():
    print("="*80)
    print("ROUTE 1 REALISTIC SPAWN SIMULATION - MORNING PEAK")
    print("="*80)
    
    # Get Route 1 data
    print("\nFetching Route 1 geometry from database...")
    coords, route_data = await get_route_1_coordinates()
    
    # Calculate cumulative distances
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    cumulative_distances = [0]
    total_route_length = 0
    for i in range(1, len(coords)):
        prev_lat, prev_lon = coords[i-1]
        curr_lat, curr_lon = coords[i]
        segment_dist = haversine(prev_lat, prev_lon, curr_lat, curr_lon)
        total_route_length += segment_dist
        cumulative_distances.append(total_route_length)
    
    print(f"Route: {route_data['long_name']} (Route {route_data['short_name']})")
    print(f"Length: {total_route_length:.0f}m ({total_route_length/1000:.2f}km)")
    print(f"Direction: Saint Lucy (rural) -> Saint Peter (coastal/commercial)")
    
    # Initialize clients
    geo_client = GeospatialClient(base_url="http://localhost:8001")
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    spawn_config = await config_loader.get_config_by_country("Barbados")
    
    # Calculate realistic spawn count
    # Base rate: ~30 spawns/hour for this route type
    base_spawns_per_hour = 30
    
    hour_7_rate = config_loader.get_hourly_rate(spawn_config, 7)  # 1.25
    hour_8_rate = config_loader.get_hourly_rate(spawn_config, 8)  # 2.8
    
    spawns_7am = int(base_spawns_per_hour * hour_7_rate)
    spawns_8am = int(base_spawns_per_hour * hour_8_rate)
    total_spawns = spawns_7am + spawns_8am
    
    print(f"\nSpawn Rate Calculation:")
    print(f"  Base rate: {base_spawns_per_hour} spawns/hour")
    print(f"  7:00-8:00 AM (rate {hour_7_rate}): {spawns_7am} spawns")
    print(f"  8:00-9:00 AM (rate {hour_8_rate}): {spawns_8am} spawns")
    print(f"  Total spawns: {total_spawns}")
    
    # Generate spawn times weighted by hourly rates
    spawn_times = []
    start_time = datetime(2025, 10, 26, 7, 0)
    
    for _ in range(spawns_7am):
        minutes = random.randint(0, 59)
        spawn_times.append(start_time + timedelta(minutes=minutes))
    
    for _ in range(spawns_8am):
        minutes = random.randint(0, 59)
        spawn_times.append(start_time + timedelta(hours=1, minutes=minutes))
    
    spawn_times.sort()
    
    print(f"\n" + "="*80)
    print(f"SIMULATING {total_spawns} SPAWNS")
    print("="*80)
    print(f"\n{'Time':<8} {'Pos':<6} {'Origin':<25} {'Dest':<25} {'Dist':<10} {'Type':<12} {'Weight':<8}")
    print(f"{'':8} {'':6} {'Origin Address':<80}")
    print(f"{'':8} {'':6} {'Destination Address':<80}")
    print("-"*200)
    
    # Track statistics
    origin_positions = []
    dest_positions = []
    trip_distances = []
    building_types = {}
    
    for spawn_time in spawn_times:
        # Calculate boarding position using weighted distribution
        boarding_weights = [boarding_probability(i / len(coords)) for i in range(len(coords))]
        origin_idx = weighted_random_choice(boarding_weights)
        origin_lat, origin_lon = coords[origin_idx]
        origin_pos_pct = (origin_idx / len(coords)) * 100
        
        # Calculate alighting position (must be after boarding)
        alighting_weights = []
        for i in range(len(coords)):
            pos_fraction = i / len(coords)
            boarding_fraction = origin_idx / len(coords)
            prob = alighting_probability(boarding_fraction, pos_fraction)
            alighting_weights.append(prob)
        
        dest_idx = weighted_random_choice(alighting_weights)
        dest_lat, dest_lon = coords[dest_idx]
        dest_pos_pct = (dest_idx / len(coords)) * 100
        
        # Get addresses (simplified - only for display)
        origin_addr_data = geo_client.reverse_geocode(origin_lat, origin_lon)
        dest_addr_data = geo_client.reverse_geocode(dest_lat, dest_lon)
        
        # Get building type
        buildings_data = geo_client.find_nearby_buildings(origin_lat, origin_lon, radius_meters=100)
        buildings = buildings_data.get('buildings', [])
        building_type = buildings[0].get('building', 'residential') if buildings else 'residential'
        
        # Calculate weight
        feature_weight = config_loader.get_building_weight(spawn_config, building_type)
        weight = config_loader.calculate_spawn_probability(
            config=spawn_config,
            feature_weight=feature_weight,
            current_hour=spawn_time.hour,
            day_of_week="monday"
        )
        
        # Route distance
        route_dist = cumulative_distances[dest_idx] - cumulative_distances[origin_idx]
        
        # Track stats
        origin_positions.append(origin_pos_pct)
        dest_positions.append(dest_pos_pct)
        trip_distances.append(route_dist)
        building_types[building_type] = building_types.get(building_type, 0) + 1
        
        # Print spawn
        time_str = spawn_time.strftime("%H:%M")
        pos_str = f"{origin_pos_pct:.0f}%"
        origin_coords = f"{origin_lat:.6f}, {origin_lon:.6f}"
        dest_coords = f"{dest_lat:.6f}, {dest_lon:.6f}"
        
        print(f"{time_str:<8} {pos_str:<6} {origin_coords:<25} {dest_coords:<25} {route_dist:.0f}m{'':<6} {building_type:<12} {weight:.2f}")
        print(f"{'':8} {'':6} {origin_addr_data['address']:<80}")
        print(f"{'':8} {'':6} {dest_addr_data['address']:<80}")
        print()
    
    # Print statistics
    print("\n" + "="*80)
    print("SPAWN STATISTICS")
    print("="*80)
    
    print(f"\nBoarding Position Distribution:")
    print(f"  0-25% of route:   {sum(1 for p in origin_positions if p < 25)} spawns ({sum(1 for p in origin_positions if p < 25)/len(origin_positions)*100:.1f}%)")
    print(f"  25-50% of route:  {sum(1 for p in origin_positions if 25 <= p < 50)} spawns ({sum(1 for p in origin_positions if 25 <= p < 50)/len(origin_positions)*100:.1f}%)")
    print(f"  50-75% of route:  {sum(1 for p in origin_positions if 50 <= p < 75)} spawns ({sum(1 for p in origin_positions if 50 <= p < 75)/len(origin_positions)*100:.1f}%)")
    print(f"  75-100% of route: {sum(1 for p in origin_positions if p >= 75)} spawns ({sum(1 for p in origin_positions if p >= 75)/len(origin_positions)*100:.1f}%)")
    
    print(f"\nAlighting Position Distribution:")
    print(f"  0-25% of route:   {sum(1 for p in dest_positions if p < 25)} spawns")
    print(f"  25-50% of route:  {sum(1 for p in dest_positions if 25 <= p < 50)} spawns")
    print(f"  50-75% of route:  {sum(1 for p in dest_positions if 50 <= p < 75)} spawns")
    print(f"  75-100% of route: {sum(1 for p in dest_positions if p >= 75)} spawns")
    
    print(f"\nTrip Distance:")
    print(f"  Average: {sum(trip_distances)/len(trip_distances):.0f}m")
    print(f"  Shortest: {min(trip_distances):.0f}m")
    print(f"  Longest: {max(trip_distances):.0f}m")
    
    print(f"\nBuilding Types:")
    for btype, count in sorted(building_types.items(), key=lambda x: -x[1]):
        print(f"  {btype}: {count} ({count/len(spawn_times)*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
