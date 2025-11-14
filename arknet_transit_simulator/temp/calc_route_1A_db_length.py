import subprocess
import json
from math import radians, sin, cos, sqrt, atan2

# DB connection details (edit if needed)
DB = 'arknettransit'
USER = 'david'
HOST = 'localhost'
ROUTE_SHORT_NAME = '1A'

# Get all shape_ids for route_1A
psql_cmd_ids = f"psql -h {HOST} -U {USER} -d {DB} -t -A -F',' -c \"SELECT shape_id FROM route_shapes WHERE route_id = (SELECT route_id FROM routes WHERE short_name = '{ROUTE_SHORT_NAME}')\""
result = subprocess.run(psql_cmd_ids, shell=True, capture_output=True, text=True)
shape_ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]

all_coords = []
for shape_id in shape_ids:
    psql_cmd_pts = f"psql -h {HOST} -U {USER} -d {DB} -t -A -F',' -c \"SELECT shape_pt_lat, shape_pt_lon FROM shapes WHERE shape_id = '{shape_id}' ORDER BY shape_pt_sequence\""
    result = subprocess.run(psql_cmd_pts, shell=True, capture_output=True, text=True)
    coords = []
    for line in result.stdout.splitlines():
        if line.strip():
            lat, lon = map(float, line.strip().split(','))
            coords.append((lon, lat))
    all_coords.extend(coords)

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
for i in range(len(all_coords)-1):
    lon1, lat1 = all_coords[i]
    lon2, lat2 = all_coords[i+1]
    total += haversine(lon1, lat1, lon2, lat2)

print(f"Total route_1A DB length: {total:.2f} km")
