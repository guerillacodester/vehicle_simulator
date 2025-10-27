import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
conn = psycopg2.connect(
    dbname="arknettransit",
    user="david",
    password="Ga25w123!",
    host="localhost",
    port=5432
)

cursor = conn.cursor(cursor_factory=RealDictCursor)

# Get Route 1
cursor.execute("SELECT * FROM routes WHERE short_name = '1'")
route = cursor.fetchone()

# Parse the GeoJSON FeatureCollection
geojson = route['geojson_data']

print(f"\nRoute 1: {route['short_name']} - {route['long_name']}")
print(f"Type: {geojson['type']}")
print(f"Number of features (segments): {len(geojson['features'])}\n")

# Calculate total distance from segment costs
total_distance_meters = 0
for i, feature in enumerate(geojson['features']):
    cost = feature['properties'].get('cost', 0)
    layer = feature['properties'].get('layer', 'unknown')
    total_distance_meters += cost
    print(f"Segment {i+1:2d} (layer {layer:3s}): {cost:8.2f} meters")

print(f"\n{'='*50}")
print(f"Total Route Distance: {total_distance_meters:.2f} meters")
print(f"                      {total_distance_meters/1000:.2f} kilometers")
print(f"{'='*50}")

cursor.close()
conn.close()
