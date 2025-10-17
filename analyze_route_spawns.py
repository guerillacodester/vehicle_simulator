"""
Analyze route 1A spawn locations and distances along the route.
"""
import sys
import math
from typing import List, Tuple
import httpx

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points on Earth in km."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_closest_point_on_route(spawn_lat: float, spawn_lon: float, route_points: List[Tuple[float, float]]) -> Tuple[int, float, float]:
    """
    Find the closest point on the route to the spawn location.
    Returns: (segment_index, distance_along_route_km, distance_to_route_km)
    """
    min_distance = float('inf')
    closest_segment = 0
    distance_to_segment = 0.0
    
    for i in range(len(route_points)):
        lat, lon = route_points[i]
        dist = haversine(spawn_lat, spawn_lon, lat, lon)
        if dist < min_distance:
            min_distance = dist
            closest_segment = i
            distance_to_segment = dist
    
    # Calculate cumulative distance along route up to this point
    distance_along = 0.0
    for i in range(closest_segment):
        lat1, lon1 = route_points[i]
        lat2, lon2 = route_points[i + 1]
        distance_along += haversine(lat1, lon1, lat2, lon2)
    
    return closest_segment, distance_along, distance_to_segment

def analyze_route():
    """Fetch route 1A from API and analyze spawn locations."""
    
    print("=" * 80)
    print("ROUTE 1A SPAWN LOCATION ANALYSIS")
    print("=" * 80)
    
    # Fetch route data from Strapi
    print("\n[1/3] Fetching route 1A from API...")
    
    try:
        # Get route
        response = httpx.get(
            "http://localhost:1337/api/routes",
            params={"filters[route_id][$eq]": "1A", "filters[is_active][$eq]": True},
            timeout=10.0
        )
        routes = response.json()["data"]
        
        if not routes:
            print("❌ Route 1A not found")
            return
        
        route = routes[0]
        print(f"✅ Found route: {route['route_name']}")
        
        # Get default shape
        response = httpx.get(
            "http://localhost:1337/api/route-shapes",
            params={
                "filters[route_id][$eq]": "1A",
                "filters[is_default][$eq]": True
            },
            timeout=10.0
        )
        shapes = response.json()["data"]
        
        if not shapes:
            print("❌ No default shape found for route 1A")
            return
        
        shape_id = shapes[0]["shape_id"]
        print(f"✅ Found default shape: {shape_id}")
        
        # Get shape points
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
        print(f"✅ Loaded {len(shape_points)} shape points")
        
    except Exception as e:
        print(f"❌ Error fetching route data: {e}")
        return
    
    # Extract coordinates
    route_coords = [(pt["shape_pt_lat"], pt["shape_pt_lon"]) for pt in shape_points]
    
    # Calculate total route distance
    print("\n[2/3] Calculating route metrics...")
    total_distance = 0.0
    for i in range(len(route_coords) - 1):
        lat1, lon1 = route_coords[i]
        lat2, lon2 = route_coords[i + 1]
        total_distance += haversine(lat1, lon1, lat2, lon2)
    
    print(f"📏 Total route distance: {total_distance:.2f} km")
    print(f"📍 Start: ({route_coords[0][0]:.4f}, {route_coords[0][1]:.4f})")
    print(f"📍 End: ({route_coords[-1][0]:.4f}, {route_coords[-1][1]:.4f})")
    
    # Analyze spawn locations from logs
    print("\n[3/3] Analyzing spawn locations...")
    print("-" * 80)
    
    spawns = [
        # From commuter_startup.log
        {"id": "COM_046B", "spawn": (13.2669, -59.6257), "dest": (13.3116, -59.6368), "dir": "OUTBOUND"},
        {"id": "COM_6036", "spawn": (13.3216, -59.6025), "dest": (13.3161, -59.6399), "dir": "OUTBOUND"},
    ]
    
    for i, spawn in enumerate(spawns, 1):
        spawn_lat, spawn_lon = spawn["spawn"]
        dest_lat, dest_lon = spawn["dest"]
        
        # Find closest point on route for spawn
        segment_idx, dist_along, dist_to_route = find_closest_point_on_route(
            spawn_lat, spawn_lon, route_coords
        )
        
        # Find closest point for destination
        dest_segment_idx, dest_dist_along, dest_dist_to_route = find_closest_point_on_route(
            dest_lat, dest_lon, route_coords
        )
        
        # Calculate trip distance
        trip_distance = haversine(spawn_lat, spawn_lon, dest_lat, dest_lon)
        route_distance = dest_dist_along - dist_along
        
        print(f"\n🎯 SPAWN #{i} | ID: {spawn['id']}")
        print(f"   Direction: {spawn['dir']}")
        print(f"   📍 Spawn Location: ({spawn_lat:.4f}, {spawn_lon:.4f})")
        print(f"      → Distance along route: {dist_along:.2f} km ({(dist_along/total_distance)*100:.1f}% of route)")
        print(f"      → Distance from route: {dist_to_route*1000:.0f} meters")
        print(f"      → Nearest shape point: #{segment_idx}")
        print(f"   🎯 Destination: ({dest_lat:.4f}, {dest_lon:.4f})")
        print(f"      → Distance along route: {dest_dist_along:.2f} km ({(dest_dist_along/total_distance)*100:.1f}% of route)")
        print(f"      → Distance from route: {dest_dist_to_route*1000:.0f} meters")
        print(f"      → Nearest shape point: #{dest_segment_idx}")
        print(f"   📏 Trip Metrics:")
        print(f"      → Direct distance: {trip_distance:.2f} km")
        print(f"      → Route distance: {route_distance:.2f} km")
        print(f"      → Direction on route: {'Forward' if route_distance > 0 else 'Backward'}")
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total route length: {total_distance:.2f} km")
    print(f"Route spawns analyzed: {len(spawns)}")
    print(f"Both spawns are heading {'OUTBOUND' if all(s['dir'] == 'OUTBOUND' for s in spawns) else 'mixed directions'}")
    print("=" * 80)

if __name__ == "__main__":
    analyze_route()
