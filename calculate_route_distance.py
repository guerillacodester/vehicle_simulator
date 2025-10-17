"""
Calculate the total distance of route 1A from shape points.
"""
import math
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

def calculate_route_distance():
    """Fetch route 1A shape points and calculate total distance."""
    
    print("=" * 80)
    print("ROUTE 1A TOTAL DISTANCE CALCULATION")
    print("=" * 80)
    
    try:
        # Get default shape for route 1A
        print("\n[1/2] Fetching route 1A shape...")
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
        print("[2/2] Fetching shape points...")
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
        
        # Extract coordinates
        route_coords = [(pt["shape_pt_lat"], pt["shape_pt_lon"]) for pt in shape_points]
        
        # Calculate total distance
        print("\n" + "=" * 80)
        print("📏 DISTANCE CALCULATION")
        print("=" * 80)
        
        total_distance = 0.0
        longest_segment = 0.0
        shortest_segment = float('inf')
        
        print(f"\n{'Segment':<10} {'From Point':<25} {'To Point':<25} {'Distance (km)':<15}")
        print("-" * 80)
        
        for i in range(len(route_coords) - 1):
            lat1, lon1 = route_coords[i]
            lat2, lon2 = route_coords[i + 1]
            segment_distance = haversine(lat1, lon1, lat2, lon2)
            total_distance += segment_distance
            
            if segment_distance > longest_segment:
                longest_segment = segment_distance
            if segment_distance < shortest_segment and segment_distance > 0:
                shortest_segment = segment_distance
            
            # Print every 10th segment to avoid too much output
            if i % 10 == 0 or i == len(route_coords) - 2:
                print(f"{i+1:<10} ({lat1:.4f}, {lon1:.4f}) → ({lat2:.4f}, {lon2:.4f}) {segment_distance:.3f}")
        
        print("-" * 80)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 ROUTE 1A SUMMARY")
        print("=" * 80)
        print(f"\n🚏 Total Shape Points:      {len(shape_points)}")
        print(f"📏 Total Route Distance:    {total_distance:.2f} km ({total_distance*1000:.0f} meters)")
        print(f"📍 Start Point:             ({route_coords[0][0]:.6f}, {route_coords[0][1]:.6f})")
        print(f"📍 End Point:               ({route_coords[-1][0]:.6f}, {route_coords[-1][1]:.6f})")
        print(f"📊 Average Segment Length:  {total_distance/(len(route_coords)-1)*1000:.0f} meters")
        print(f"📊 Longest Segment:         {longest_segment*1000:.0f} meters")
        print(f"📊 Shortest Segment:        {shortest_segment*1000:.0f} meters")
        print(f"⏱️  Est. Drive Time:         ~{total_distance/40*60:.0f} minutes (at 40 km/h avg)")
        print(f"⏱️  Est. Drive Time (fast):  ~{total_distance/50*60:.0f} minutes (at 50 km/h avg)")
        
        # Direct distance (as the crow flies)
        direct_distance = haversine(route_coords[0][0], route_coords[0][1], 
                                   route_coords[-1][0], route_coords[-1][1])
        print(f"\n🦅 Direct Distance (crow):  {direct_distance:.2f} km")
        print(f"📐 Route Efficiency:        {(direct_distance/total_distance)*100:.1f}% (lower = more winding)")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    calculate_route_distance()
