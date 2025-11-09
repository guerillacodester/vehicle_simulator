"""
Analyze the Strapi API response to calculate the actual route distance.
"""
import requests
from geopy.distance import geodesic

STRAPI_URL = "http://localhost:1337"
ROUTE_ID = 14  # Route 1 in Strapi

def main():
    # Fetch route from Strapi API
    response = requests.get(f"{STRAPI_URL}/api/routes/{ROUTE_ID}")
    
    if response.status_code != 200:
        print(f"Error: HTTP {response.status_code}")
        return
    
    data = response.json()
    
    # Debug: print structure
    print("Response structure:")
    print(f"  Keys: {list(data.keys())}")
    
    route_wrapper = data.get('data')
    
    if not route_wrapper:
        print("No route data found")
        return
    
    # Extract attributes
    route = route_wrapper.get('attributes', {})
    
    print(f"\nRoute: {route.get('short_name')} - {route.get('long_name')}")
    print()
    
    # Get geometry
    geometry = route.get('geometry')
    if not geometry:
        print("No geometry found")
        return
    
    geom_type = geometry.get('type')
    coordinates = geometry.get('coordinates', [])
    
    print(f"Geometry Type: {geom_type}")
    print(f"Total Coordinates: {len(coordinates)}")
    print()
    
    if len(coordinates) == 0:
        print("No coordinates found")
        return
    
    # Show first and last coordinates
    first = coordinates[0]
    last = coordinates[-1]
    
    print(f"First coordinate: [{first[0]}, {first[1]}]")
    print(f"Last coordinate:  [{last[0]}, {last[1]}]")
    print()
    
    # Calculate haversine distance between first and last
    start_coords = (first[1], first[0])  # (lat, lon)
    end_coords = (last[1], last[0])
    straight_distance = geodesic(start_coords, end_coords).kilometers
    
    print(f"Haversine distance (first → last): {straight_distance:.3f} km")
    print()
    
    # Calculate cumulative path distance along the route
    total_path_distance = 0.0
    for i in range(1, len(coordinates)):
        prev = coordinates[i-1]
        curr = coordinates[i]
        prev_coords = (prev[1], prev[0])  # (lat, lon)
        curr_coords = (curr[1], curr[0])
        segment_dist = geodesic(prev_coords, curr_coords).kilometers
        total_path_distance += segment_dist
    
    print(f"🚍 Cumulative path distance (following route): {total_path_distance:.3f} km")
    print()
    
    if total_path_distance >= 11.0 and total_path_distance <= 13.0:
        print("✅ This matches the expected ~12km route distance!")
    else:
        print(f"⚠️  Expected ~12km, but calculated {total_path_distance:.3f} km")

if __name__ == "__main__":
    main()
