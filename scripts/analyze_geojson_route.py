"""
Calculate the actual route distance from the original GeoJSON file.
"""
import json
from geopy.distance import geodesic

def main():
    # Load the GeoJSON file
    with open('arknet_transit_simulator/data/route_1.geojson', 'r') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    print(f"Total features in GeoJSON: {len(features)}")
    print()
    
    # Extract all coordinates in order
    all_coords = []
    for feature in features:
        layer = feature.get('properties', {}).get('layer', 'unknown')
        geometry = feature.get('geometry', {})
        coords = geometry.get('coordinates', [])
        
        print(f"Layer {layer}: {len(coords)} points")
        all_coords.extend(coords)
    
    print()
    print(f"Total coordinates: {len(all_coords)}")
    print()
    
    # Calculate cumulative distance
    total_distance = 0.0
    for i in range(1, len(all_coords)):
        prev = all_coords[i-1]
        curr = all_coords[i]
        # GeoJSON uses [lon, lat] format
        prev_coords = (prev[1], prev[0])  # (lat, lon)
        curr_coords = (curr[1], curr[0])
        segment_dist = geodesic(prev_coords, curr_coords).kilometers
        total_distance += segment_dist
    
    first = all_coords[0]
    last = all_coords[-1]
    
    print(f"First coordinate: [{first[0]:.6f}, {first[1]:.6f}]")
    print(f"Last coordinate:  [{last[0]:.6f}, {last[1]:.6f}]")
    print()
    print(f"🚍 Total route distance: {total_distance:.3f} km")
    print()
    
    if 11.0 <= total_distance <= 13.0:
        print("✅ This IS the ~12km route!")
    else:
        print(f"⚠️  Expected ~12km, got {total_distance:.3f} km")

if __name__ == "__main__":
    main()
