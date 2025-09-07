import time
import random
import argparse
import math
import json
from typing import List, Tuple

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points on Earth in km."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate compass bearing from one point to another."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing_rad = math.atan2(x, y)
    bearing_deg = (math.degrees(bearing_rad) + 360) % 360
    return bearing_deg

def load_route_coordinates(route_file: str) -> List[Tuple[float, float]]:
    """Load coordinates from a GeoJSON route file."""
    with open(route_file) as f:
        data = json.load(f)
    coordinates = []
    for feature in data["features"]:
        for coord_set in feature["geometry"]["coordinates"]:
            for coord in coord_set:
                coordinates.append(tuple(coord))
    return coordinates

def interpolate_position(lat1: float, lon1: float, lat2: float, lon2: float, fraction: float) -> Tuple[float, float]:
    """Compute an interpolated position between two coordinates."""
    return (lat1 + (lat2 - lat1) * fraction,
            lon1 + (lon2 - lon1) * fraction)

def simulate_movement(route_file: str, tick_speed: float, aggressive: bool = False) -> None:
    """
    Simulate a vehicle moving along a route, recalculating distance and bearing at each interpolation step.
    Includes per-step distance moved, bearing change, and total time elapsed for better insight.
    """
    route = load_route_coordinates(route_file)
    if not route or len(route) < 2:
        print("Route is empty or invalid.")
        return

    total_distance = 0.0
    total_time = 0.0  # Variable to track total elapsed time
    last_position = route[0]
    prev_bearing = None

    for i in range(len(route) - 1):
        lat1, lon1 = route[i]
        lat2, lon2 = route[i + 1]

        segment_distance = haversine(lat1, lon1, lat2, lon2)
        if segment_distance == 0:
            continue

        # Estimate travel time assuming base speed of 50 km/h
        time_to_travel = (segment_distance / 50.0) * 3600.0
        steps = max(int(time_to_travel / tick_speed), 1)

        for step in range(steps + 1):
            fraction = step / steps
            lat, lon = interpolate_position(lat1, lon1, lat2, lon2, fraction)

            # Speed variation if aggressive mode is enabled
            speed_kmh = random.uniform(45.0, 55.0) if aggressive else 50.0

            # Calculate distance moved based on speed and tick time (in km)
            distance_moved = (speed_kmh * tick_speed) / 3600.0  # Converts from km/h to km per tick
            total_distance += distance_moved  # Correctly accumulate total distance

            # Calculate current bearing
            current_bearing = calculate_bearing(last_position[0], last_position[1], lat, lon) if distance_moved > 0 else calculate_bearing(lat1, lon1, lat2, lon2)

            # Bearing change since last step
            if prev_bearing is None:
                bearing_change = 0.0
            else:
                diff = (current_bearing - prev_bearing + 180) % 360 - 180
                bearing_change = diff

            # Add time increment to total time (in seconds)
            total_time += tick_speed

            print(
                f"GPS Position: {lat:.6f}, {lon:.6f} | Speed: {speed_kmh:.2f} km/h | "
                f"Distance Moved: {distance_moved:.6f} km | Total Distance: {total_distance:.2f} km | "
                f"Bearing: {current_bearing:.2f}° | Bearing Change: {bearing_change:.2f}° | "
                f"Time Elapsed: {total_time:.2f}s"
            )

            last_position = (lat, lon)
            prev_bearing = current_bearing
            time.sleep(tick_speed)

    print(f"\nTotal distance traveled: {total_distance:.2f} km")
    print(f"Total time elapsed: {total_time:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate vehicle movement along a route.")
    parser.add_argument('--route', type=str, required=True, help="Path to the GeoJSON file with route coordinates.")
    parser.add_argument('--tick', type=float, default=0.1, help="Tick speed in seconds (real-time speed).")

    args = parser.parse_args()
    simulate_movement(args.route, args.tick, None)
