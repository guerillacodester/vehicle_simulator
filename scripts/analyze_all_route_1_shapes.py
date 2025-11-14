"""
Analyze ALL Route 1 shapes to find the full 12km route.
"""
import psycopg2
import psycopg2.extras
from geopy.distance import geodesic

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get ALL route_shapes for route 1
    cursor.execute("""
        SELECT route_shape_id, shape_id, variant_code, is_default
        FROM route_shapes
        WHERE route_id = '1'
        ORDER BY route_shape_id
    """)
    
    route_shapes = cursor.fetchall()
    print(f"Total route_shapes for Route 1: {len(route_shapes)}")
    print()
    
    # Analyze each shape
    shape_distances = []
    
    for rs in route_shapes:
        shape_id = rs['shape_id']
        is_default = rs['is_default']
        variant = rs['variant_code'] or "None"
        
        # Get points for this shape
        cursor.execute("""
            SELECT shape_pt_lat, shape_pt_lon, shape_pt_sequence
            FROM shapes
            WHERE shape_id = %s
            ORDER BY shape_pt_sequence
        """, (shape_id,))
        
        points = cursor.fetchall()
        
        if len(points) == 0:
            continue
        
        # Calculate cumulative distance
        total_distance = 0.0
        for i in range(1, len(points)):
            prev = points[i-1]
            curr = points[i]
            prev_coords = (prev['shape_pt_lat'], prev['shape_pt_lon'])
            curr_coords = (curr['shape_pt_lat'], curr['shape_pt_lon'])
            segment_dist = geodesic(prev_coords, curr_coords).kilometers
            total_distance += segment_dist
        
        # Get first and last coordinates
        first = points[0]
        last = points[-1]
        
        shape_info = {
            'shape_id': shape_id[:8],  # First 8 chars
            'variant': variant,
            'is_default': is_default,
            'num_points': len(points),
            'distance_km': total_distance,
            'first': (first['shape_pt_lat'], first['shape_pt_lon']),
            'last': (last['shape_pt_lat'], last['shape_pt_lon'])
        }
        
        shape_distances.append(shape_info)
    
    # Sort by distance (descending)
    shape_distances.sort(key=lambda x: x['distance_km'], reverse=True)
    
    # Display results
    print(f"{'Shape ID':10} {'Variant':12} {'Def':5} {'Points':7} {'Distance':12}")
    print("=" * 60)
    
    for info in shape_distances:
        default_marker = "✓" if info['is_default'] else ""
        print(f"{info['shape_id']:10} {info['variant']:12} {default_marker:5} {info['num_points']:7} {info['distance_km']:11.3f} km")
    
    print()
    print("=" * 60)
    
    # Find shape closest to 12km
    target_distance = 12.0
    closest_shape = min(shape_distances, key=lambda x: abs(x['distance_km'] - target_distance))
    
    print(f"\nShape closest to 12km:")
    print(f"  Shape ID: {closest_shape['shape_id']}...")
    print(f"  Variant: {closest_shape['variant']}")
    print(f"  Points: {closest_shape['num_points']}")
    print(f"  Distance: {closest_shape['distance_km']:.3f} km")
    print(f"  First: {closest_shape['first']}")
    print(f"  Last: {closest_shape['last']}")
    
    # Check if it's the default
    if not closest_shape['is_default']:
        print(f"\n⚠️  The 12km shape is NOT the default shape!")
        print(f"   The default shape only covers {[s for s in shape_distances if s['is_default']][0]['distance_km']:.3f} km")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
