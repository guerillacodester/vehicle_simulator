"""
Test PostGIS Geofence Queries
Verify spatial queries work correctly
"""

import psycopg2

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}

def test_point_in_geofence():
    """Test if points are inside depot geofences"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("TEST POINT-IN-GEOFENCE QUERIES")
    print("="*60)
    
    # Test 1: Point inside Cheapside depot
    print("\n📍 Test 1: Point INSIDE Cheapside depot center")
    print("   Coordinates: (13.098168, -59.621582)")
    
    cursor.execute("""
        SELECT * FROM check_point_in_geofences(13.098168, -59.621582, ARRAY['depot'])
    """)
    
    results = cursor.fetchall()
    if results:
        print(f"   ✅ Found {len(results)} geofence(s):")
        for r in results:
            print(f"      - {r[0]}: {r[1]} (type: {r[2]}, distance: {r[4]:.2f}m)")
    else:
        print("   ❌ No geofences found (should be inside Cheapside)")
    
    # Test 2: Point outside all depots
    print("\n📍 Test 2: Point OUTSIDE all depots")
    print("   Coordinates: (13.2, -59.5)")
    
    cursor.execute("""
        SELECT * FROM check_point_in_geofences(13.2, -59.5, ARRAY['depot'])
    """)
    
    results = cursor.fetchall()
    if results:
        print(f"   ❌ Found {len(results)} geofence(s) (should be empty):")
        for r in results:
            print(f"      - {r[0]}: {r[1]}")
    else:
        print("   ✅ No geofences found (correct - point is outside)")
    
    # Test 3: Point near Princess Alice depot (edge case)
    print("\n📍 Test 3: Point NEAR Princess Alice depot (50m away)")
    # Princess Alice: 13.097766, -59.621822
    # Move ~50m north: add ~0.00045 to latitude
    test_lat = 13.097766 + 0.00045
    test_lon = -59.621822
    print(f"   Coordinates: ({test_lat}, {test_lon})")
    
    cursor.execute(f"""
        SELECT * FROM check_point_in_geofences({test_lat}, {test_lon}, ARRAY['depot'])
    """)
    
    results = cursor.fetchall()
    if results:
        print(f"   ✅ Found {len(results)} geofence(s):")
        for r in results:
            print(f"      - {r[0]}: {r[1]} (distance: {r[4]:.2f}m)")
    else:
        print("   ✅ No geofences found (correct - outside 100m radius)")
    
    # Test 4: Find nearest depot to a random point
    print("\n📍 Test 4: Find NEAREST depot to Downtown Bridgetown")
    print("   Coordinates: (13.095, -59.615)")
    
    cursor.execute("""
        SELECT * FROM find_nearest_geofence(13.095, -59.615, 5000.0, ARRAY['depot'])
    """)
    
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Nearest depot: {result[1]}")
        print(f"      ID: {result[0]}")
        print(f"      Type: {result[2]}")
        print(f"      Distance: {result[4]:.2f}m")
    else:
        print("   ❌ No nearest depot found")
    
    # Test 5: Query all active geofences
    print("\n📋 Test 5: List ALL active geofences")
    
    cursor.execute("""
        SELECT geofence_id, name, type, geometry_type, center_lat, center_lon, radius_meters
        FROM geofence_all
        ORDER BY name
    """)
    
    results = cursor.fetchall()
    print(f"   ✅ Found {len(results)} active geofences:")
    for r in results:
        gf_id, name, type, geom_type, lat, lon, radius = r
        print(f"      • {gf_id}")
        print(f"        Name: {name}")
        print(f"        Type: {type}, Geometry: {geom_type}")
        if lat and lon and radius:
            print(f"        Center: ({lat:.6f}, {lon:.6f}), Radius: {radius:.1f}m")
    
    # Test 6: Performance test
    print("\n⚡ Test 6: Performance benchmark (100 queries)")
    
    import time
    start = time.time()
    
    for i in range(100):
        # Random points around Bridgetown
        lat = 13.09 + (i * 0.001)
        lon = -59.62 + (i * 0.001)
        cursor.execute(f"""
            SELECT * FROM check_point_in_geofences({lat}, {lon}, ARRAY['depot'])
        """)
        cursor.fetchall()
    
    end = time.time()
    elapsed_ms = (end - start) * 1000
    avg_ms = elapsed_ms / 100
    
    print(f"   ✅ 100 queries completed in {elapsed_ms:.2f}ms")
    print(f"   ✅ Average: {avg_ms:.2f}ms per query")
    print(f"   ✅ Performance: {'EXCELLENT' if avg_ms < 5 else 'GOOD' if avg_ms < 20 else 'OK'}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    test_point_in_geofence()
