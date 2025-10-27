"""
Intuitive spawn visualization showing individual spawns with constraints.
Shows how temporal and geospatial factors affect each spawn.
"""
import asyncio
import httpx
import random
import math
from datetime import datetime, timedelta
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader


class TemporalConstraint:
    """Time-based spawn multipliers."""
    
    @staticmethod
    def get_multiplier(hour: int, building_type: str, day_of_week: str) -> float:
        patterns = {
            'residential': {
                6: 2.5, 7: 3.0, 8: 2.0, 9: 1.0,
                16: 1.5, 17: 2.5, 18: 2.0
            },
            'school': {
                7: 3.0, 8: 1.5, 15: 2.5, 16: 1.0
            },
            'commercial': {
                7: 1.5, 8: 2.5, 9: 2.0,
                17: 2.5, 18: 2.0
            },
            'church': {
                8: 2.0 if day_of_week == 'sunday' else 0.2,
                9: 2.5 if day_of_week == 'sunday' else 0.2,
                10: 3.0 if day_of_week == 'sunday' else 0.2,
            }
        }
        
        pattern = patterns.get(building_type, patterns['residential'])
        return pattern.get(hour, 1.0)


async def get_route_1_coordinates():
    """Fetch Route 1 geometry."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://localhost:1337/api/routes?populate=*&filters[short_name][$eq]=1"
        )
        resp.raise_for_status()
        data = resp.json()
        route = data['data'][0]
        
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


def weighted_random_choice(weights):
    """Select index based on weights."""
    total = sum(weights)
    if total == 0:
        return random.randint(0, len(weights) - 1)
    r = random.uniform(0, total)
    cumsum = 0
    for i, w in enumerate(weights):
        cumsum += w
        if r <= cumsum:
            return i
    return len(weights) - 1


def base_boarding_probability(position_fraction):
    """Base probability (exponential decay from route start)."""
    return math.exp(-2.5 * position_fraction)


async def main():
    print("="*120)
    print("INDIVIDUAL SPAWN SIMULATION - MORNING PEAK (7:00-9:00 AM)")
    print("="*120)
    
    # Get route data
    coords, route_data = await get_route_1_coordinates()
    
    # Calculate distances
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
    
    print(f"\nRoute: {route_data['long_name']} (#{route_data['short_name']})")
    print(f"Length: {total_route_length/1000:.2f}km | Direction: Saint Lucy (rural) -> Saint Peter (coastal)")
    
    # Initialize
    geo_client = GeospatialClient(base_url="http://localhost:8001")
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    spawn_config = await config_loader.get_config_by_country("Barbados")
    
    # Generate spawn times (weighted by hourly rates)
    base_spawns_per_hour = 30
    hour_7_rate = config_loader.get_hourly_rate(spawn_config, 7)  # 2.5
    hour_8_rate = config_loader.get_hourly_rate(spawn_config, 8)  # 2.8
    
    spawns_7am = int(base_spawns_per_hour * hour_7_rate)
    spawns_8am = int(base_spawns_per_hour * hour_8_rate)
    
    print(f"\nSpawn Rate: {spawns_7am} spawns @ 7AM (rate {hour_7_rate}) + {spawns_8am} spawns @ 8AM (rate {hour_8_rate}) = {spawns_7am + spawns_8am} total")
    print(f"Showing: First 40 spawns with full constraint breakdown\n")
    
    # Generate spawn times
    spawn_times = []
    start_time = datetime(2025, 10, 26, 7, 0)
    
    for _ in range(spawns_7am):
        minutes = random.randint(0, 59)
        spawn_times.append(start_time + timedelta(minutes=minutes))
    
    for _ in range(spawns_8am):
        minutes = random.randint(0, 59)
        spawn_times.append(start_time + timedelta(hours=1, minutes=minutes))
    
    spawn_times.sort()
    
    # Table header
    print(f"{'#':<4} {'Time':<8} {'Pos':<6} {'Location':<35} {'Building':<12} {'Base':<7} {'Temp':<7} {'Geo':<7} {'Final':<8} {'Effect':<12}")
    print("-" * 120)
    
    # Building type and address caches
    building_cache = {}
    address_cache = {}
    
    # Generate spawns
    for spawn_num, spawn_time in enumerate(spawn_times[:40], 1):
        hour = spawn_time.hour
        
        # Calculate boarding position using weighted distribution
        boarding_weights = [
            base_boarding_probability(i / len(coords)) for i in range(len(coords))
        ]
        origin_idx = weighted_random_choice(boarding_weights)
        origin_lat, origin_lon = coords[origin_idx]
        origin_pos_pct = (origin_idx / len(coords)) * 100
        
        # Get building type (with caching to reduce API calls)
        cache_key = f"{origin_lat:.5f},{origin_lon:.5f}"
        if cache_key in building_cache:
            building_type, building_density = building_cache[cache_key]
        else:
            result = geo_client.find_nearby_buildings(origin_lat, origin_lon, radius_meters=150)
            buildings = result.get('buildings', [])
            building_type = buildings[0].get('building', 'residential') if buildings else 'residential'
            building_density = len(buildings)
            building_cache[cache_key] = (building_type, building_density)
        
        # Get address (with caching - only makes API call once per unique location)
        if cache_key in address_cache:
            location = address_cache[cache_key]
        else:
            addr_data = geo_client.reverse_geocode(origin_lat, origin_lon)
            location = addr_data['address'][:35]  # Truncate
            address_cache[cache_key] = location
        
        # Calculate probabilities
        base_prob = base_boarding_probability(origin_idx / len(coords))
        temporal_mult = TemporalConstraint.get_multiplier(hour, building_type, 'monday')
        density_mult = 1.3 if building_density > 10 else 1.1 if building_density > 5 else 1.0
        geo_mult = temporal_mult * density_mult
        final_prob = base_prob * geo_mult
        
        # Determine effect
        if geo_mult > 2.0:
            effect = "BOOSTED++"
        elif geo_mult > 1.5:
            effect = "BOOSTED"
        elif geo_mult > 0.8:
            effect = "NORMAL"
        else:
            effect = "SUPPRESSED"
        
        # Print row
        time_str = spawn_time.strftime("%H:%M")
        pos_str = f"{origin_pos_pct:.1f}%"
        
        print(f"{spawn_num:<4} {time_str:<8} {pos_str:<6} {location:<35} {building_type:<12} "
              f"{base_prob:<7.3f} {temporal_mult:<7.2f} {geo_mult:<7.2f} {final_prob:<8.3f} {effect:<12}")
    
    # Statistics
    print("\n" + "="*120)
    print("SPAWN ANALYSIS")
    print("="*120)
    
    # Analyze all spawns
    all_spawns = []
    for spawn_time in spawn_times:
        hour = spawn_time.hour
        boarding_weights = [base_boarding_probability(i / len(coords)) for i in range(len(coords))]
        origin_idx = weighted_random_choice(boarding_weights)
        origin_lat, origin_lon = coords[origin_idx]
        
        cache_key = f"{origin_lat:.5f},{origin_lon:.5f}"
        if cache_key in building_cache:
            building_type, building_density = building_cache[cache_key]
        else:
            result = geo_client.find_nearby_buildings(origin_lat, origin_lon, radius_meters=150)
            buildings = result.get('buildings', [])
            building_type = buildings[0].get('building', 'residential') if buildings else 'residential'
            building_density = len(buildings)
            building_cache[cache_key] = (building_type, building_density)
        
        temporal_mult = TemporalConstraint.get_multiplier(hour, building_type, 'monday')
        all_spawns.append({'hour': hour, 'building': building_type, 'temporal': temporal_mult})
    
    # Hour distribution
    hour_7_count = sum(1 for s in all_spawns if s['hour'] == 7)
    hour_8_count = sum(1 for s in all_spawns if s['hour'] == 8)
    
    print(f"\nTemporal Distribution:")
    print(f"  7:00-7:59 AM: {hour_7_count} spawns ({hour_7_count/len(all_spawns)*100:.1f}%)")
    print(f"  8:00-8:59 AM: {hour_8_count} spawns ({hour_8_count/len(all_spawns)*100:.1f}%)")
    
    # Building type distribution
    building_counts = {}
    for s in all_spawns:
        building_counts[s['building']] = building_counts.get(s['building'], 0) + 1
    
    print(f"\nBuilding Type Distribution:")
    for btype, count in sorted(building_counts.items(), key=lambda x: -x[1]):
        print(f"  {btype.capitalize():<15}: {count:3d} spawns ({count/len(all_spawns)*100:.1f}%)")
    
    # Constraint effectiveness
    avg_temporal_mult = sum(s['temporal'] for s in all_spawns) / len(all_spawns)
    boosted_count = sum(1 for s in all_spawns if s['temporal'] > 1.5)
    
    print(f"\nConstraint Impact:")
    print(f"  Average temporal multiplier: {avg_temporal_mult:.2f}x")
    print(f"  Boosted spawns (>1.5x): {boosted_count} ({boosted_count/len(all_spawns)*100:.1f}%)")
    print(f"  Normal spawns (0.8-1.5x): {len(all_spawns)-boosted_count} ({(len(all_spawns)-boosted_count)/len(all_spawns)*100:.1f}%)")
    
    print("\n" + "="*120)
    print("KEY INSIGHTS")
    print("="*120)
    print("""
✓ Spawns occur at ARBITRARY positions (not sequential)
✓ Spawn TIMES are weighted by hourly rates (more at 8AM than 7AM)
✓ TEMPORAL constraints boost residential areas during morning hours
✓ GEOSPATIAL constraints increase probability near high-density areas
✓ Building TYPE determines time-of-day spawn patterns
✓ Result: Realistic commuter behavior emerges from statistical constraints
    """)


if __name__ == "__main__":
    asyncio.run(main())
