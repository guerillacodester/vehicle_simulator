"""
Check which depots are connected to route 1A
"""
import httpx

def check_route_depots():
    print("=" * 80)
    print("ROUTE 1A DEPOT CONNECTIONS")
    print("=" * 80)
    
    # Get route 1A details
    response = httpx.get(
        "http://localhost:1337/api/routes",
        params={"filters[route_id][$eq]": "1A"},
        timeout=10.0
    )
    routes = response.json()["data"]
    
    if not routes:
        print("❌ Route 1A not found")
        return
    
    route = routes[0]
    
    print(f"\n📋 Route Information:")
    print(f"   ID: {route['route_id']}")
    print(f"   Name: {route['route_name']}")
    print(f"   Long Name: {route.get('route_long_name', 'N/A')}")
    print(f"   Type: {route.get('route_type', 'N/A')}")
    print(f"   Active: {route.get('is_active', False)}")
    
    # Get all depots
    response = httpx.get(
        "http://localhost:1337/api/depots",
        params={"filters[is_active][$eq]": True, "pagination[pageSize]": 100},
        timeout=10.0
    )
    depots = response.json()["data"]
    
    print(f"\n🏢 All Active Depots ({len(depots)} total):")
    for depot in depots:
        print(f"   • {depot['depot_code']}: {depot['depot_name']}")
        print(f"     Location: ({depot['latitude']}, {depot['longitude']})")
        print(f"     Routes: {depot.get('routes_served', 'N/A')}")
        print()
    
    # Get route shape to find start/end
    response = httpx.get(
        "http://localhost:1337/api/route-shapes",
        params={
            "filters[route_id][$eq]": "1A",
            "filters[is_default][$eq]": True
        },
        timeout=10.0
    )
    shapes = response.json()["data"]
    
    if shapes:
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
        
        if shape_points:
            start_point = shape_points[0]
            end_point = shape_points[-1]
            
            print("=" * 80)
            print("📍 ROUTE 1A START/END POINTS")
            print("=" * 80)
            print(f"\n🚏 Start Point (Point #1):")
            print(f"   Coordinates: ({start_point['shape_pt_lat']:.6f}, {start_point['shape_pt_lon']:.6f})")
            
            print(f"\n🏁 End Point (Point #{len(shape_points)}):")
            print(f"   Coordinates: ({end_point['shape_pt_lat']:.6f}, {end_point['shape_pt_lon']:.6f})")
            
            # Calculate distances from depots to start/end
            import math
            
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371.0
                phi1, phi2 = math.radians(lat1), math.radians(lat2)
                delta_phi = math.radians(lat2 - lat1)
                delta_lambda = math.radians(lon2 - lon1)
                a = (math.sin(delta_phi / 2) ** 2 +
                     math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                return R * c
            
            print("\n" + "=" * 80)
            print("📏 DEPOT DISTANCES TO ROUTE START/END")
            print("=" * 80)
            
            for depot in depots:
                depot_lat = depot['latitude']
                depot_lon = depot['longitude']
                
                dist_to_start = haversine(depot_lat, depot_lon, 
                                         start_point['shape_pt_lat'], 
                                         start_point['shape_pt_lon'])
                dist_to_end = haversine(depot_lat, depot_lon,
                                       end_point['shape_pt_lat'],
                                       end_point['shape_pt_lon'])
                
                min_dist = min(dist_to_start, dist_to_end)
                closest_to = "START" if dist_to_start < dist_to_end else "END"
                
                status = "✅ CONNECTED" if min_dist < 0.5 else ("⚠️ NEARBY" if min_dist < 2.0 else "❌ FAR")
                
                print(f"\n🏢 {depot['depot_code']}: {depot['depot_name']}")
                print(f"   Distance to route START: {dist_to_start:.3f} km")
                print(f"   Distance to route END: {dist_to_end:.3f} km")
                print(f"   Closest to: {closest_to} ({min_dist:.3f} km)")
                print(f"   Status: {status}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_route_depots()
