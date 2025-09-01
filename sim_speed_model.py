#!/usr/bin/env python3
import argparse
import importlib
import json
import sys
import time
from typing import Dict, Any, Optional

# -------------------- vehicles I/O --------------------

def deploy_vehicles(path: str = "vehicles.json") -> Dict[str, Dict[str, Any]]:
    """Load the vehicles JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not data:
            raise ValueError("vehicles must be a non-empty JSON object.")
        return data
    except FileNotFoundError:
        sys.exit(f"vehicles file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in vehicles file '{path}': {e}")


def select_vehicle(vehicles: Dict[str, Dict[str, Any]]) -> str:
    """
    Choose a vehicle deterministically from vehicles:
      1) any with "default": true (if tie, lexicographically first)
      2) else any with "active": true (if tie, lexicographically first)
      3) else if only one, use it
      4) else lexicographically first ID
    """
    defaults = [vid for vid, cfg in vehicles.items() if cfg.get("default") is True]
    if defaults:
        return sorted(defaults)[0]

    actives = [vid for vid, cfg in vehicles.items() if cfg.get("active") is True]
    if actives:
        return sorted(actives)[0]

    vids = list(vehicles.keys())
    if len(vids) == 1:
        return vids[0]
    return sorted(vids)[0]

# -------------------- speed model loader --------------------

def load_speed_model(name: str, **kwargs):
    """
    Dynamically import a speed model class from world/speed_models/ by name.
    Example: name="random_walk" -> world.speed_models.random_walk_speed -> RandomWalkSpeed
    """
    module_name = f"world.speed_models.{name}_speed"
    class_name = "".join(part.capitalize() for part in name.split("_")) + "Speed"
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        return cls(**kwargs)
    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"Unknown speed model '{name}': {e}")

# -------------------- simulation --------------------

def simulate_speed_model(vehicle_config: Dict[str, Any],
                         speed_model_override: Optional[str],
                         tick_time: float):
    """Run the speed model for 1000 ticks, printing speed, total distance, and time."""
    model_name = (speed_model_override or vehicle_config.get("speed_model", "kinematic")).lower()

    kwargs = {
        "min_speed": float(vehicle_config.get("min_speed", 30)),
        "max_speed": float(vehicle_config.get("max_speed", 80)),
        "accel_limit": float(vehicle_config.get("accel_limit", 2)),
        "decel_limit": float(vehicle_config.get("decel_limit", 3)),
        "corner_slowdown": float(vehicle_config.get("corner_slowdown", 25)),
    }

    speed_model = load_speed_model(model_name, **kwargs)

    total_distance = 0.0  # km
    total_time = 0.0      # s

    for tick in range(1000):
        result = speed_model.update()

        if isinstance(result, dict):
            velocity     = result.get("velocity", 0.0)
            acceleration = result.get("acceleration", 0.0)
            velocity_dir = result.get("velocity_dir", 0.0)
            accel_dir    = result.get("accel_dir", 0.0)
        else:
            velocity     = float(result)
            acceleration = 0.0
            velocity_dir = 0.0
            accel_dir    = 0.0

        # accumulate with full precision
        total_distance += (velocity * tick_time) / 3600
        total_time += tick_time

        # human-friendly display
        if total_distance < 1.0:
            display_distance = f"{total_distance * 1000:7.1f} m"
        else:
            display_distance = f"{total_distance:7.3f} km"

        print(
            f"Tick {tick + 1:4d}: "
            f"Velocity: {velocity:6.2f} km/h | "
            f"Accel: {acceleration:6.2f} | "
            f"Heading: {velocity_dir:6.2f}° | "
            f"Steer Δ: {accel_dir:6.2f}° | "
            f"Total Distance: {display_distance} | "
            f"Total Time: {total_time:.2f} s"
        )

        time.sleep(tick_time)

    return total_distance, total_time

# -------------------- entrypoint --------------------

def main():
    parser = argparse.ArgumentParser(description="Simulate vehicle speed based on vehicles.json")
    parser.add_argument(
        "--tick", type=float, default=0.1,
        help="Tick time in seconds (default: 0.1)"
    )
    parser.add_argument(
        "--speed-model", type=str,
        help="Override speed model (e.g., 'kinematic', 'random_walk')."
    )
    parser.add_argument(
        "--vehicles", type=str, default="vehicles.json",
        help="Path to vehicles JSON (default: vehicles.json)."
    )
    parser.add_argument(
        "--vehicle-id", type=str, default=None,
        help="Specific vehicle ID from the manifest (default: auto-select)."
    )
    args = parser.parse_args()

    vehicles = deploy_vehicles(args.vehicles)

    if args.vehicle_id:
        if args.vehicle_id not in vehicles:
            sys.exit(f"Vehicle ID '{args.vehicle_id}' not found in manifest. Available: {', '.join(vehicles.keys())}")
        vehicle_id = args.vehicle_id
    else:
        vehicle_id = select_vehicle(vehicles)

    vehicle_config = vehicles[vehicle_id]

    print(f"Using vehicle: {vehicle_id}")
    print(f"Configured model: {vehicle_config.get('speed_model', 'kinematic')}"
          + (f" | Override: {args.speed_model}" if args.speed_model else ""))
    print(f"Tick: {args.tick} s\n")

    total_distance, total_time = simulate_speed_model(vehicle_config, args.speed_model, args.tick)

    # Final results with auto unit switch
    if total_distance < 1.0:
        final_distance = f"{total_distance * 1000:.1f} m"
    else:
        final_distance = f"{total_distance:.3f} km"

    print(f"\nFinal Results for Vehicle {vehicle_id}:")
    print(f"Total Distance Traveled: {final_distance}")
    print(f"Total Time Elapsed:     {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
