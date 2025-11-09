"""
Analyze Route 1 default shape to understand the 12km distance calculation.
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
    
    # Get route info
    cursor.execute("""
        SELECT id, short_name, long_name 
        FROM routes 
        WHERE short_name = '1'
    """)
    route = cursor.fetchone()
    print(f"Route: {route['short_name']} - {route['long_name']}")
    print(f"Route numeric ID: {route['id']}")
    print()
    
    # Get default route_shape
    cursor.execute("""
        SELECT route_shape_id, shape_id, variant_code, is_default
        FROM route_shapes
        WHERE route_id = %s AND is_default = true
    """, (route['short_name'],))
    
    default_shape = cursor.fetchone()
    if not default_shape:
        print("No default shape found!")
        return
    
    print(f"Default Shape ID: {default_shape['shape_id']}")
    print(f"Variant Code: {default_shape['variant_code']}")
    print()
    
    # Get all points for default shape
    cursor.execute("""
        SELECT shape_pt_lat, shape_pt_lon, shape_pt_sequence, shape_dist_traveled
        FROM shapes
        WHERE shape_id = %s
        ORDER BY shape_pt_sequence
    """, (default_shape['shape_id'],))
    
    points = cursor.fetchall()
    print(f"Total points in default shape: {len(points)}")
    print()
    
    # Show first and last points
    first = points[0]
    last = points[-1]
    print(f"First point (seq {first['shape_pt_sequence']}): {first['shape_pt_lat']}, {first['shape_pt_lon']}")
    print(f"Last point (seq {last['shape_pt_sequence']}): {last['shape_pt_lat']}, {last['shape_pt_lon']}")
    print()
    
    # Calculate haversine distance between first and last
    start_coords = (first['shape_pt_lat'], first['shape_pt_lon'])
    end_coords = (last['shape_pt_lat'], last['shape_pt_lon'])
    straight_distance = geodesic(start_coords, end_coords).kilometers
    print(f"Haversine distance (first → last): {straight_distance:.3f} km")
    print()
    
    # Calculate cumulative path distance
    total_path_distance = 0.0
    for i in range(1, len(points)):
        prev = points[i-1]
        curr = points[i]
        prev_coords = (prev['shape_pt_lat'], prev['shape_pt_lon'])
        curr_coords = (curr['shape_pt_lat'], curr['shape_pt_lon'])
        segment_dist = geodesic(prev_coords, curr_coords).kilometers
        total_path_distance += segment_dist
    
    print(f"Cumulative path distance (along route): {total_path_distance:.3f} km")
    print()
    
    # Check if shape_dist_traveled is populated
    if first['shape_dist_traveled'] is not None and last['shape_dist_traveled'] is not None:
        print(f"GTFS shape_dist_traveled (first): {first['shape_dist_traveled']} m")
        print(f"GTFS shape_dist_traveled (last): {last['shape_dist_traveled']} m")
        gtfs_distance_km = (last['shape_dist_traveled'] - first['shape_dist_traveled']) / 1000.0
        print(f"GTFS total distance: {gtfs_distance_km:.3f} km")
    else:
        print("GTFS shape_dist_traveled not populated")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
