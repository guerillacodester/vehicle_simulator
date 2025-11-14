import requests
import sys

API_BASE_URL = "http://localhost:1337"  # Change if your Strapi API runs elsewhere
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

# Step 2: Get default route-shape
shape_resp = requests.get(f"{API_BASE_URL}/api/route-shapes?filters[route_id][$eq]={ROUTE_CODE}&filters[is_default][$eq]=true")
shape_resp.raise_for_status()
route_shapes = shape_resp.json().get('data', [])
if not route_shapes:
    print(f"No default route-shape found for route {ROUTE_CODE}.")
    sys.exit(1)
shape_id = route_shapes[0].get('shape_id')
print(f"Shape ID: {shape_id}")

# Step 3: Get all shape points ordered by sequence
shapes_resp = requests.get(f"{API_BASE_URL}/api/shapes?filters[shape_id][$eq]={shape_id}&sort=shape_pt_sequence&pagination[pageSize]=1000")
shapes_resp.raise_for_status()
shape_points = shapes_resp.json().get('data', [])
if not shape_points:
    print(f"No shape points found for shape_id {shape_id}.")
    sys.exit(1)

# Step 4: Print all coordinates
print("Route 1 coordinates from Strapi DB:")
for pt in shape_points:
    lon = pt.get('shape_pt_lon')
    lat = pt.get('shape_pt_lat')
    seq = pt.get('shape_pt_sequence')
    print(f"{seq}: [{lon}, {lat}]")
