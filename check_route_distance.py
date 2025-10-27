import requests
import json
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r

# Get Route 1
r = requests.get('http://localhost:1337/api/routes?filters[short_name][$eq]=1&populate=*')
route = r.json()['data'][0]

print(f"Route: {route.get('short_name')} - {route.get('long_name')}")
print(f"Start: {route.get('start_location')}")
print(f"End: {route.get('end_location')}")
print(f"Segment length (DB): {route.get('segment_length_km')} km")

# Get geometry
geojson_data = route.get('geojson_data')
print(f"\ngeojson_data type: {type(geojson_data)}")
print(f"geojson_data exists: {geojson_data is not None}")

if geojson_data:
    if isinstance(geojson_data, dict):
        print(f"geojson_data keys: {geojson_data.keys()}")
        coords = geojson_data.get('geometry', {}).get('coordinates', [])
    else:
        print(f"geojson_data value: {str(geojson_data)[:200]}")
        geojson = json.loads(geojson_data)
        coords = geojson.get('geometry', {}).get('coordinates', [])
else:
    print("NO geojson_data!")
    coords = []
print(f"\nGeometry points: {len(coords)}")

# Calculate actual distance
total_distance = 0
for i in range(1, len(coords)):
    lon1, lat1 = coords[i-1]
    lon2, lat2 = coords[i]
    total_distance += haversine(lon1, lat1, lon2, lat2)

print(f"\nCalculated distance: {total_distance:.0f} meters ({total_distance/1000:.2f} km)")
if coords:
    print(f"First point: {coords[0]}")
    print(f"Last point: {coords[-1]}")
else:
    print("No coordinates!")
