import json
from math import radians, sin, cos, sqrt, atan2

# Haversine formula for distance between two lat/lon points
# Returns distance in kilometers
def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

with open('route_1A.geojson', 'r') as f:
    geojson = json.load(f)

coords = geojson['features'][0]['geometry']['coordinates']

# Check for large jumps between consecutive points
threshold_km = 0.5  # If any segment > 0.5km, flag it
issues = []
for i in range(len(coords)-1):
    lon1, lat1 = coords[i]
    lon2, lat2 = coords[i+1]
    dist = haversine(lon1, lat1, lon2, lat2)
    if dist > threshold_km:
        issues.append((i, dist, (lon1, lat1), (lon2, lat2)))

if issues:
    print(f"Discontinuities found (segments > {threshold_km}km):")
    for idx, dist, pt1, pt2 in issues:
        print(f"  Segment {idx}-{idx+1}: {dist:.2f} km from {pt1} to {pt2}")
else:
    print("All points are ordered and continuous (no large jumps detected).")
