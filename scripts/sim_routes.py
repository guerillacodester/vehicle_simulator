import argparse
import os
import json
import math
from typing import List, Tuple

from world.routes.route_loader import load_route_coordinates

# Haversine formula to calculate distance between two coordinates (in km)
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371  # Radius of the Earth in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c  # Distance in kilometers

# Bearing formula to calculate the bearing between two coordinates (in degrees)
def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    
    initial_bearing = math.atan2(x, y)
    
    # Convert the bearing from radians to degrees and normalize it
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360  # Normalize to 0-360 degrees
    
    return compass_bearing

def main():
    # Argument parsing to get the route file
    parser = argparse.ArgumentParser(description="Load and print GPS coordinates with distance, bearing, and deltas from a GeoJSON route file.")
    parser.add_argument('--routes', type=str, required=True, help="Path to the GeoJSON file with route coordinates.")
    args = parser.parse_args()

    # Check if the file exists
    if not os.path.exists(args.routes):
        print(f"Error: The specified route file '{args.routes}' does not exist.")
        return

    # Load the coordinates from the provided GeoJSON route file
    coordinates = load_route_coordinates(args.routes)

    # Variables for cumulative distance
    total_distance = 0.0

    # Print header for clarity
    print(f"{'Lat1, Lon1':<30} {'Lat2, Lon2':<30} {'Dist (km)':<12} {'Bearing (deg)':<16} {'Bearing Delta (deg)':<18} {'Lat Delta':<12} {'Lon Delta':<12} {'Total Dist (km)':<15}")
    
    for i in range(len(coordinates) - 1):
        lat1, lon1 = coordinates[i]
        lat2, lon2 = coordinates[i + 1]
        
        # Calculate distance and bearing between the current and next coordinate
        dist = haversine(lat1, lon1, lat2, lon2)
        brng = bearing(lat1, lon1, lat2, lon2)
        
        # Calculate bearing delta (change in direction between n and n+2)
        if i + 2 < len(coordinates):
            lat3, lon3 = coordinates[i + 2]
            bearing_delta = bearing(lat2, lon2, lat3, lon3) - brng
        else:
            bearing_delta = 0.0  # No bearing delta if there's no n+2
        
        # Calculate lat/lon deltas
        lat_delta = lat2 - lat1
        lon_delta = lon2 - lon1
        
        # Add to total distance
        total_distance += dist
        
        # Print formatted output for each row
        print(f"{lat1:<14.6f}, {lon1:<14.6f} {lat2:<14.6f}, {lon2:<14.6f} {dist:<12.2f} {brng:<16.2f} {bearing_delta:<18.2f} {lat_delta:<12.6f} {lon_delta:<12.6f} {total_distance:<15.2f}")

if __name__ == "__main__":
    main()
