"""
Test spawn simulation along actual Route 1 geometry.
Shows spawns during peak hours with addresses, distances, and compute times.
"""
import asyncio
import httpx
import random
import time
from datetime import datetime
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader


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
        for idx, feature in enumerate(route['geojson_data']['features']):
            coords = feature['geometry']['coordinates']
            print(f"Processing feature {idx+1}/{len(route['geojson_data']['features'])}: {len(coords)} points...")
            for coord in coords:
                # Coordinates can be in string "lon lat" format or [lon, lat] array
                if isinstance(coord, str):
                    lon, lat = map(float, coord.split())
                else:
                    lon, lat = coord[0], coord[1]
                all_coords.append((lat, lon))
        
        return all_coords, route


async def main():
    print("="*80)
    print("ROUTE 1 SPAWN SIMULATION - PEAK HOURS")
    print("="*80)
    
    # Get Route 1 data
    print("\nFetching Route 1 geometry from database...")
    start_fetch = time.perf_counter()
    coords, route_data = await get_route_1_coordinates()
    fetch_time = (time.perf_counter() - start_fetch) * 1000
    
    start_point = coords[0]
    end_point = coords[-1]
    
    # Calculate cumulative distances along route
    print("Calculating route distances...")
    from math import radians, sin, cos, sqrt, atan2
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        lat1, lon1 = radians(lat1), radians(lon1)
        lat2, lon2 = radians(lat2), radians(lon2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    cumulative_distances = [0]
    total_route_length = 0
    for i in range(1, len(coords)):
        prev_lat, prev_lon = coords[i-1]
        curr_lat, curr_lon = coords[i]
        segment_dist = haversine(prev_lat, prev_lon, curr_lat, curr_lon)
        total_route_length += segment_dist
        cumulative_distances.append(total_route_length)
    
    print(f"Route Name: {route_data['long_name']}")
    print(f"Route Number: {route_data['short_name']}")
    print(f"Total Segments: {len(route_data['geojson_data']['features'])}")
    print(f"Total Coordinate Points: {len(coords)}")
    print(f"Route Length: {total_route_length:.0f}m ({total_route_length/1000:.2f}km)")
    print(f"Start Point: {start_point[0]:.6f}, {start_point[1]:.6f} (0m)")
    print(f"End Point: {end_point[0]:.6f}, {end_point[1]:.6f} ({total_route_length:.0f}m)")
    print(f"Fetch Time: {fetch_time:.2f}ms\n")
    
    # Initialize clients
    geo_client = GeospatialClient(base_url="http://localhost:8001")
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    
    # Get spawn configuration for Barbados
    print("Loading spawn configuration for Barbados...")
    start_config = time.perf_counter()
    spawn_config = await config_loader.get_config_by_country("Barbados")
    config_time = (time.perf_counter() - start_config) * 1000
    print(f"Config loaded in {config_time:.2f}ms\n")
    
    # Reverse geocode start and end points
    print("Reverse geocoding route endpoints...")
    start_geo = time.perf_counter()
    start_address_data = geo_client.reverse_geocode(start_point[0], start_point[1])
    end_address_data = geo_client.reverse_geocode(end_point[0], end_point[1])
    geo_time = (time.perf_counter() - start_geo) * 1000
    
    print(f"Route Start Address: {start_address_data['address']}")
    print(f"Route End Address: {end_address_data['address']}")
    print(f"Geocoding Time: {geo_time:.2f}ms\n")
    
    # Simulate spawns during morning peak (7-9 AM, Monday)
    print("="*80)
    print("MORNING PEAK SPAWN SIMULATION (7:00 AM - 9:00 AM, Monday)")
    print("="*80)
    
    # Table header
    print(f"\n{'Time':<8} {'Origin Lat/Lon':<25} {'Dest Lat/Lon':<25} {'Route Dist':<12} {'Building':<12} {'Weight':<8} {'Compute':<10}")
    print(f"{'':8} {'Origin Address':<80}")
    print(f"{'':8} {'Destination Address':<80}")
    print("-"*200)
    
    num_spawns = 15
    day_of_week = "monday"
    
    for i in range(num_spawns):
        # Random time between 7:00 and 9:00
        hour = random.randint(7, 8)
        minute = random.randint(0, 59)
        time_str = f"{hour:02d}:{minute:02d}"
        
        # Random origin point along route (first 70% of route - people boarding)
        origin_idx = random.randint(0, int(len(coords) * 0.7))
        origin_lat, origin_lon = coords[origin_idx]
        
        # Destination closer to end (last 50% of route)
        dest_idx = random.randint(int(len(coords) * 0.5), len(coords) - 1)
        dest_lat, dest_lon = coords[dest_idx]
        
        # Start timing
        spawn_start = time.perf_counter()
        
        # Get addresses
        origin_addr_data = geo_client.reverse_geocode(origin_lat, origin_lon)
        dest_addr_data = geo_client.reverse_geocode(dest_lat, dest_lon)
        
        # Get nearby buildings at origin to determine spawn weight
        buildings_data = geo_client.find_nearby_buildings(origin_lat, origin_lon, radius_meters=100)
        buildings = buildings_data.get('buildings', [])
        
        # Determine building type (use first building if available, else "residential")
        if buildings and len(buildings) > 0:
            building_type = buildings[0].get('building', 'residential')
        else:
            building_type = 'residential'
        
        # Calculate spawn probability/weight
        feature_weight = config_loader.get_building_weight(spawn_config, building_type)
        weight = config_loader.calculate_spawn_probability(
            config=spawn_config,
            feature_weight=feature_weight,
            current_hour=hour,
            day_of_week=day_of_week
        )
        
        # Calculate distance along route (not straight-line)
        route_distance_m = cumulative_distances[dest_idx] - cumulative_distances[origin_idx]
        
        compute_ms = (time.perf_counter() - spawn_start) * 1000
        
        # Print results (3 lines per spawn)
        origin_coords = f"{origin_lat:.6f}, {origin_lon:.6f}"
        dest_coords = f"{dest_lat:.6f}, {dest_lon:.6f}"
        distance_str = f"{route_distance_m:.0f}m"
        weight_str = f"{weight:.2f}"
        compute_str = f"{compute_ms:.1f}ms"
        
        print(f"{time_str:<8} {origin_coords:<25} {dest_coords:<25} {distance_str:<12} {building_type:<12} {weight_str:<8} {compute_str:<10}")
        print(f"{'':8} {origin_addr_data['address']:<80}")
        print(f"{'':8} {dest_addr_data['address']:<80}")
        print()
    
    print("\n" + "="*80)
    print("SIMULATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
