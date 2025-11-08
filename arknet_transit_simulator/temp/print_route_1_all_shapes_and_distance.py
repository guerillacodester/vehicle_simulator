import requests
import sys
import math

API_BASE_URL = "http://localhost:1337"  # Change if needed
ROUTE_CODE = "1"

# Step 1: Get route details
route_resp = requests.get(f"{API_BASE_URL}/api/routes?filters[short_name][$eq]={ROUTE_CODE}")
route_resp.raise_for_status()
routes = route_resp.json().get('data', [])
if not routes:
    print(f"Route {ROUTE_CODE} not found.")
    sys.exit(1)
route = routes[0]
route_name = route.get('long_name', f'Route {ROUTE_CODE}')
print(f"Route: {route_name}")

# Step 2: Get ALL route-shapes for this route
shape_resp = requests.get(f"{API_BASE_URL}/api/route-shapes?filters[route_id][$eq]={ROUTE_CODE}")
shape_resp.raise_for_status()
route_shapes = shape_resp.json().get('data', [])
if not route_shapes:
    print(f"No route-shapes found for route {ROUTE_CODE}.")
    sys.exit(1)

all_coords = []
for shape in route_shapes:
    shape_id = shape.get('shape_id')
    print(f"Shape ID: {shape_id}")
    # Step 3: Get all shape points for this shape
    shapes_resp = requests.get(f"{API_BASE_URL}/api/shapes?filters[shape_id][$eq]={shape_id}&sort=shape_pt_sequence&pagination[pageSize]=1000")
    shapes_resp.raise_for_status()
    shape_points = shapes_resp.json().get('data', [])
    if not shape_points:
        print(f"No shape points found for shape_id {shape_id}.")
        continue
    for pt in shape_points:
        lon = pt.get('shape_pt_lon')
        lat = pt.get('shape_pt_lat')
        seq = pt.get('shape_pt_sequence')
        all_coords.append((lon, lat))
        print(f"{shape_id} seq {seq}: [{lon}, {lat}]")

# Calculate total distance for all points (in order)
def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

total_km = 0.0
for i in range(len(all_coords)-1):
    lon1, lat1 = all_coords[i]
    lon2, lat2 = all_coords[i+1]
    total_km += haversine(lon1, lat1, lon2, lat2)

print(f"\nTotal route 1 distance (ALL shapes, Strapi DB): {total_km:.3f} km")
