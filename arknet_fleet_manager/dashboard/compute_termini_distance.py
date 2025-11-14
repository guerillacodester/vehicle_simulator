import json
import math

# Haversine formula
def haversine(lon1, lat1, lon2, lat2):
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371.0088  # mean Earth radius in kilometers
    return c * r


def parse_coord(pt):
    # pt can be [lon, lat] with strings or numbers
    lon = float(pt[0])
    lat = float(pt[1])
    return lon, lat


def sort_layer_key(layer_str):
    # layer like "1_1", "2_10" or "3_0"
    try:
        parts = layer_str.split('_')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return (major, minor)
    except Exception:
        return (9999, 9999)


with open('temp_route1.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

features = payload['data']['routes'][0]['geojson_data']['features']

# sort by properties.layer numerically
features_sorted = sorted(features, key=lambda ft: sort_layer_key(ft.get('properties', {}).get('layer', '')))

# build a continuous list of points by concatenating feature coordinates
points = []
for ft in features_sorted:
    coords = ft['geometry']['coordinates']
    for pt in coords:
        lon, lat = parse_coord(pt)
        # avoid duplicate consecutive points
        if not points or (abs(points[-1][0]-lon) > 1e-9 or abs(points[-1][1]-lat) > 1e-9):
            points.append((lon, lat))

if len(points) < 2:
    print('Not enough points to compute distance')
    exit(1)

start = points[0]
end = points[-1]

# straight-line distance between termini
straight_km = haversine(start[0], start[1], end[0], end[1])

# route length along polyline (sum of haversines)
route_km = 0.0
for i in range(1, len(points)):
    route_km += haversine(points[i-1][0], points[i-1][1], points[i][0], points[i][1])

print(f"Terminus (start) coordinate: lon={start[0]}, lat={start[1]}")
print(f"Terminus (end)   coordinate: lon={end[0]}, lat={end[1]}")
print(f"Straight-line distance between termini: {straight_km:.6f} km")
print(f"Route length by summing segments:          {route_km:.6f} km")
