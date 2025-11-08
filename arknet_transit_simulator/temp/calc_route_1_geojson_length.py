import json
from math import radians, sin, cos, sqrt, atan2

def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

with open('e:/projects/github/vehicle_simulator/arknet_transit_simulator/data/route_1.geojson', 'r') as f:
    geojson = json.load(f)

coords = []
for feature in geojson['features']:
    coords.extend(feature['geometry']['coordinates'])

total = 0.0
for i in range(len(coords)-1):
    lon1, lat1 = coords[i]
    lon2, lat2 = coords[i+1]
    total += haversine(lon1, lat1, lon2, lat2)

print(f"Total route_1.geojson length: {total:.2f} km")
