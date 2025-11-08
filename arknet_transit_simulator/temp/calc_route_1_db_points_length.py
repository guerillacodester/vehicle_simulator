import re
from math import radians, sin, cos, sqrt, atan2

# Read the shape points from the pasted output file
points_file = 'e:/projects/github/vehicle_simulator/arknet_transit_simulator/data/route_1_db_points.txt'
coords = []
with open(points_file, 'r') as f:
    for line in f:
        # Match lines with three columns: sequence | lat | lon
        m = re.match(r'\s*\d+\s*\|\s*([\d\.\-]+)\s*\|\s*([\d\.\-]+)', line)
        if m:
            lat = float(m.group(1))
            lon = float(m.group(2))
            coords.append((lon, lat))

# Haversine formula
def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

total = 0.0
for i in range(len(coords)-1):
    lon1, lat1 = coords[i]
    lon2, lat2 = coords[i+1]
    total += haversine(lon1, lat1, lon2, lat2)

print(f"Total route 1 DB points length: {total:.2f} km")
