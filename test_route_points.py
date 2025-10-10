"""Test reverse geocoding on 10 random points from Route 1A"""
import psycopg2
import random
from reverse_geocode import ReverseGeocoder

# Database connection
conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    database='arknettransit',
    user='david',
    password='Ga25w123!'
)

cur = conn.cursor()

# Get all shape points from Route 1A
cur.execute("""
    SELECT DISTINCT s.shape_pt_lat, s.shape_pt_lon, s.shape_pt_sequence
    FROM shapes s
    JOIN route_shapes rs ON s.shape_id = rs.shape_id
    WHERE rs.route_id = '1A'
    ORDER BY s.shape_pt_sequence
""")

all_points = cur.fetchall()
cur.close()
conn.close()

print(f"Route 1A has {len(all_points)} unique shape points")
print(f"Selecting 10 random points for testing...\n")

# Pick 10 random points
random_points = random.sample(all_points, min(10, len(all_points)))

# Sort by sequence for logical order
random_points.sort(key=lambda x: x[2])

# Initialize geocoder
geocoder = ReverseGeocoder()

print("="*80)
print("TESTING 10 RANDOM POINTS ALONG ROUTE 1A")
print("="*80)

for i, (lat, lon, seq) in enumerate(random_points, 1):
    print(f"\n{'#'*80}")
    print(f"TEST POINT {i}/10 - Sequence {seq}")
    print(f"{'#'*80}")
    
    # Reverse geocode with smaller radius for cleaner output
    result = geocoder.reverse_geocode(lat, lon, max_distance_m=2000)
    
    # Brief summary
    print(f"\n📝 QUICK SUMMARY:")
    print(f"   Location: {result['location_description']}")
    if result['pois']:
        print(f"   Nearest POI: {result['pois'][0]['name']} ({result['pois'][0]['distance_m']:.0f}m)")
    if result['places']:
        print(f"   Area: {result['places'][0]['name']}")
    if result['geofences']:
        print(f"   In Geofence: {result['geofences'][0]['name']}")
    
    if i < len(random_points):
        print(f"\n{'='*80}")
        input("Press Enter for next point...")

geocoder.close()

print("\n" + "="*80)
print("✅ TESTING COMPLETE")
print("="*80)
print(f"Tested {len(random_points)} random points along Route 1A")
print("All points successfully geocoded!")
