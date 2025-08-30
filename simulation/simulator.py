import time
from geodesy.geodesy import haversine, calculate_bearing
from routes.route_loader import load_route_coordinates
from interpolation.interpolator import interpolate_position
from deprecated_sim_speed_model import load_speed_model

def simulate_movement(route_file: str,
                      tick_speed: float,
                      speed_model_name: str = "kinematic",
                      model_kwargs: dict = None) -> None:
    """
    Simulate movement along a route using a pluggable speed model.
    """
    route = load_route_coordinates(route_file)
    if not route or len(route) < 2:
        print("Route is empty or invalid.")
        return

    # Load the speed model dynamically
    model_kwargs = model_kwargs or {}
    speed_model = load_speed_model(speed_model_name, **model_kwargs)

    total_distance, total_time = 0.0, 0.0
    last_position = route[0]
    prev_bearing = None

    for i in range(len(route) - 1):
        lat1, lon1 = route[i]
        lat2, lon2 = route[i + 1]

        segment_distance = haversine(lat1, lon1, lat2, lon2)
        if segment_distance == 0:
            continue

        time_to_travel = (segment_distance / 50.0) * 3600.0
        steps = max(int(time_to_travel / tick_speed), 1)

        for step in range(steps + 1):
            fraction = step / steps
            lat, lon = interpolate_position(lat1, lon1, lat2, lon2, fraction)

            # Use the speed model
            speed_kmh = speed_model.update()

            # Convert to km moved in this tick
            distance_moved = (speed_kmh * tick_speed) / 3600.0
            total_distance += distance_moved

            current_bearing = calculate_bearing(last_position[0], last_position[1], lat, lon)
            bearing_change = 0.0 if prev_bearing is None else (current_bearing - prev_bearing + 180) % 360 - 180

            total_time += tick_speed
            print(f"GPS: {lat:.6f},{lon:.6f} | Spd: {speed_kmh:.2f} km/h | "
                  f"StepDist: {distance_moved:.6f} km | TotDist: {total_distance:.2f} km | "
                  f"Hdg: {current_bearing:.2f}° | ΔHdg: {bearing_change:.2f}° | "
                  f"T+{total_time:.2f}s")

            last_position, prev_bearing = (lat, lon), current_bearing
            time.sleep(tick_speed)

    print(f"Total distance: {total_distance:.2f} km | Total time: {total_time:.2f}s")
