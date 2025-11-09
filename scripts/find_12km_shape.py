"""
Find which shape has the full 12km route for Route 1.
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
        ORDER BY is_default DESC, route_shape_id
    """)
    
    route_shapes = cursor.fetchall()
    print(f"Total route_shapes for Route 1: {len(route_shapes)}")
    print("=" * 80)
    print()
    
    # Analyze each shape
    for idx, rs in enumerate(route_shapes, 1):
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
        
        default_marker = "✓ DEFAULT" if is_default else ""
        match_12km = "⭐ ~12KM!" if 11.0 <= total_distance <= 13.0 else ""
        
        print(f"Shape #{idx} {default_marker} {match_12km}")
        print(f"  Shape ID: {shape_id}")
        print(f"  Variant: {variant}")
        print(f"  Points: {len(points)}")
        print(f"  Distance: {total_distance:.3f} km")
        print(f"  First: ({first['shape_pt_lat']:.6f}, {first['shape_pt_lon']:.6f})")
        print(f"  Last:  ({last['shape_pt_lat']:.6f}, {last['shape_pt_lon']:.6f})")
        print()
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
