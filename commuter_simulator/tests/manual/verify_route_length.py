"""
Verify Route 1 total length and check spawn distances.
"""
import asyncio
import httpx
from math import radians, sin, cos, sqrt, atan2


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    R = 6371000  # Earth radius in meters
    lat1, lon1 = radians(lat1), radians(lon1)
    lat2, lon2 = radians(lat2), radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


async def main():
    # Fetch Route 1
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:1337/api/routes?populate=*&filters[short_name][$eq]=1")
        resp.raise_for_status()
        data = resp.json()
        route = data['data'][0]
    
    # Extract coordinates
    all_coords = []
    for feature in route['geojson_data']['features']:
        coords = feature['geometry']['coordinates']
        for coord in coords:
            if isinstance(coord, str):
                lon, lat = map(float, coord.split())
            else:
                lon, lat = coord[0], coord[1]
            all_coords.append((lat, lon))
    
    # Calculate cumulative distance along route
    total_distance = 0
    distances = [0]  # First point is at 0m
    
    for i in range(1, len(all_coords)):
        prev_lat, prev_lon = all_coords[i-1]
        curr_lat, curr_lon = all_coords[i]
        segment_dist = haversine_distance(prev_lat, prev_lon, curr_lat, curr_lon)
        total_distance += segment_dist
        distances.append(total_distance)
    
    print("="*80)
    print("ROUTE 1 LENGTH ANALYSIS")
    print("="*80)
    print(f"\nTotal Route Length: {total_distance:.0f} meters ({total_distance/1000:.2f} km)")
    print(f"Total Coordinate Points: {len(all_coords)}")
    print(f"\nStart: {all_coords[0][0]:.6f}, {all_coords[0][1]:.6f} (0m)")
    print(f"End:   {all_coords[-1][0]:.6f}, {all_coords[-1][1]:.6f} ({total_distance:.0f}m)")
    
    # Check some sample spawns from the test output
    print("\n" + "="*80)
    print("VERIFYING SPAWN DISTANCES")
    print("="*80)
    
    test_spawns = [
        ("07:43", 13.280289, -59.647220, 13.266591, -59.643705, 1570, "OK - should be on route"),
        ("07:04", 13.325129, -59.616412, 13.283872, -59.643650, 5453, "SUSPICIOUS - check if exceeds route"),
        ("08:21", 13.318113, -59.627114, 13.266118, -59.643664, 6053, "SUSPICIOUS - check if exceeds route"),
        ("07:04", 13.323937, -59.617104, 13.252577, -59.642117, 8384, "VERY SUSPICIOUS - likely exceeds route"),
    ]
    
    print(f"\n{'Time':<8} {'Reported':<10} {'Actual':<10} {'Route Length':<15} {'Status':<20}")
    print("-"*80)
    
    for time_str, orig_lat, orig_lon, dest_lat, dest_lon, reported_dist, note in test_spawns:
        actual_dist = haversine_distance(orig_lat, orig_lon, dest_lat, dest_lon)
        
        # Find position of origin along route
        min_orig_dist = float('inf')
        orig_idx = 0
        for idx, (lat, lon) in enumerate(all_coords):
            dist = haversine_distance(orig_lat, orig_lon, lat, lon)
            if dist < min_orig_dist:
                min_orig_dist = dist
                orig_idx = idx
        
        # Find position of destination along route
        min_dest_dist = float('inf')
        dest_idx = 0
        for idx, (lat, lon) in enumerate(all_coords):
            dist = haversine_distance(dest_lat, dest_lon, lat, lon)
            if dist < min_dest_dist:
                min_dest_dist = dist
                dest_idx = idx
        
        # Distance along route
        if dest_idx > orig_idx:
            route_dist = distances[dest_idx] - distances[orig_idx]
            status = "ON ROUTE" if route_dist <= total_distance else "EXCEEDS ROUTE"
        else:
            route_dist = 0
            status = "BACKWARDS!"
        
        print(f"{time_str:<8} {reported_dist:<10} {actual_dist:.0f}m{'':<6} {route_dist:.0f}m{'':<10} {status:<20}")
    
    print("\n" + "="*80)
    print("PROBLEM IDENTIFIED")
    print("="*80)
    print("\nThe issue: Spawns are using straight-line (haversine) distance between origin")
    print("and destination, NOT distance along the route!")
    print(f"\nRoute length: {total_distance:.0f}m ({total_distance/1000:.2f}km)")
    print("Some spawn distances exceed this because they measure 'as the crow flies'")
    print("instead of following the actual route path.")
    print("\nFIX: Calculate distance along route path, not straight-line distance.")


if __name__ == "__main__":
    asyncio.run(main())
