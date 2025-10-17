"""
Verify spawn and destination points are ON route 1A
"""
import math
import httpx

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points on Earth in km."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def verify_points_on_route():
    # Fetch route shape
    response = httpx.get(
        "http://localhost:1337/api/route-shapes",
        params={"filters[route_id][$eq]": "1A", "filters[is_default][$eq]": True},
        timeout=10.0
    )
    shapes = response.json()["data"]
    shape_id = shapes[0]["shape_id"]
    
    response = httpx.get(
        "http://localhost:1337/api/shapes",
        params={
            "filters[shape_id][$eq]": shape_id,
            "sort": "shape_pt_sequence",
            "pagination[pageSize]": 1000
        },
        timeout=10.0
    )
    shape_points = response.json()["data"]
    route_coords = [(pt["shape_pt_lat"], pt["shape_pt_lon"]) for pt in shape_points]
    
    # Test points from latest spawn
    spawn_point = (13.2678, -59.6268)
    dest_point = (13.3138, -59.6389)
    
    print("=" * 80)
    print("VERIFYING POINTS ARE ON ROUTE 1A")
    print("=" * 80)
    
    # Find closest route point to spawn
    min_spawn_dist = float('inf')
    closest_spawn_idx = -1
    for i, (lat, lon) in enumerate(route_coords):
        dist = haversine(spawn_point[0], spawn_point[1], lat, lon)
        if dist < min_spawn_dist:
            min_spawn_dist = dist
            closest_spawn_idx = i
    
    # Find closest route point to destination
    min_dest_dist = float('inf')
    closest_dest_idx = -1
    for i, (lat, lon) in enumerate(route_coords):
        dist = haversine(dest_point[0], dest_point[1], lat, lon)
        if dist < min_dest_dist:
            min_dest_dist = dist
            closest_dest_idx = i
    
    print(f"\n📍 Spawn Point: {spawn_point}")
    print(f"   Closest route point #{closest_spawn_idx}: ({route_coords[closest_spawn_idx][0]:.6f}, {route_coords[closest_spawn_idx][1]:.6f})")
    print(f"   Distance from route: {min_spawn_dist*1000:.1f} meters")
    print(f"   {'✅ ON ROUTE' if min_spawn_dist < 0.01 else '❌ OFF ROUTE'}")
    
    print(f"\n🎯 Destination Point: {dest_point}")
    print(f"   Closest route point #{closest_dest_idx}: ({route_coords[closest_dest_idx][0]:.6f}, {route_coords[closest_dest_idx][1]:.6f})")
    print(f"   Distance from route: {min_dest_dist*1000:.1f} meters")
    print(f"   {'✅ ON ROUTE' if min_dest_dist < 0.01 else '❌ OFF ROUTE'}")
    
    # Calculate distance ALONG the route
    cumulative = [0.0]
    for i in range(len(route_coords) - 1):
        dist = haversine(route_coords[i][0], route_coords[i][1], 
                        route_coords[i+1][0], route_coords[i+1][1])
        cumulative.append(cumulative[-1] + dist)
    
    spawn_dist_along = cumulative[closest_spawn_idx]
    dest_dist_along = cumulative[closest_dest_idx]
    
    print(f"\n📏 Distance Along Route:")
    print(f"   Spawn at: {spawn_dist_along:.3f} km ({spawn_dist_along/cumulative[-1]*100:.1f}% of route)")
    print(f"   Destination at: {dest_dist_along:.3f} km ({dest_dist_along/cumulative[-1]*100:.1f}% of route)")
    print(f"   Trip distance (along route): {abs(dest_dist_along - spawn_dist_along):.3f} km")
    print(f"   Direct distance (as crow flies): {haversine(*spawn_point, *dest_point):.3f} km")
    print(f"\n📊 Route total length: {cumulative[-1]:.3f} km")
    print("=" * 80)

if __name__ == "__main__":
    verify_points_on_route()
