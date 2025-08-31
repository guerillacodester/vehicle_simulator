#!/usr/bin/env python3
import argparse
import importlib
import json
import sys
import time
from typing import Dict, Any, Optional

# .\speed_model_sim.py  --tick 0.1 --speed-model aggressive

# -------------------- assignments I/O --------------------

def deploy_vehicles(path: str = "assignments.json") -> Dict[str, Dict[str, Any]]:
    """Load the assignments JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not data:
            raise ValueError("Assignments must be a non-empty JSON object.")
        return data
    except FileNotFoundError:
        sys.exit(f"Assignments file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in assignments file '{path}': {e}")


def select_vehicle(assignments: Dict[str, Dict[str, Any]]) -> str:
    """
    Choose a vehicle deterministically from assignments:
      1) any with "default": true (if tie, lexicographically first)
      2) else any with "active": true (if tie, lexicographically first)
      3) else if only one, use it
      4) else lexicographically first ID
    """
    defaults = [vid for vid, cfg in assignments.items() if cfg.get("default") is True]
    if defaults:
        return sorted(defaults)[0]

    actives = [vid for vid, cfg in assignments.items() if cfg.get("active") is True]
    if actives:
        return sorted(actives)[0]

    vids = list(assignments.keys())
    if len(vids) == 1:
        return vids[0]
    return sorted(vids)[0]


# -------------------- speed model loader --------------------

def load_speed_model(name: str, **kwargs):
    """
    Dynamically import a speed model class from speed_models/ by name.
    Example: name="random_walk" -> speed_models/random_walk_speed.py -> RandomWalkSpeed
    """
    module_name = f"speed_models.{name}_speed"
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
        speed_kmh = speed_model.update()                 # km/h
        total_distance += (speed_kmh * tick_time) / 3600 # km added this tick
        total_time += tick_time

        print(f"Tick {tick + 1:4d}: "
              f"Speed: {speed_kmh:6.2f} km/h | "
              f"Total Distance: {total_distance:7.2f} km | "
              f"Total Time: {total_time:.2f} seconds")

        time.sleep(tick_time)

    return total_distance, total_time


# -------------------- entrypoint --------------------

def main():
    parser = argparse.ArgumentParser(description="Simulate vehicle speed based on assignments.json (no vehicle ID arg).")
    parser.add_argument("--tick", type=float, required=True, help="Tick time in seconds (e.g., 0.1).")
    parser.add_argument("--speed-model", type=str, help="Override speed model (e.g., 'kinematic', 'random_walk').")
    parser.add_argument("--assignments", type=str, default="assignments.json",
                        help="Path to assignments JSON (default: assignments.json).")
    args = parser.parse_args()

    assignments = deploy_vehicles(args.assignments)
    vehicle_id = select_vehicle(assignments)
    vehicle_config = assignments[vehicle_id]

    print(f"Using vehicle: {vehicle_id}")
    print(f"Configured model: {vehicle_config.get('speed_model', 'kinematic')}"
          + (f" | Override: {args.speed_model}" if args.speed_model else ""))
    print(f"Tick: {args.tick} s\n")

    total_distance, total_time = simulate_speed_model(vehicle_config, args.speed_model, args.tick)

    print(f"\nFinal Results for Vehicle {vehicle_id}:")
    print(f"Total Distance Traveled: {total_distance:.2f} km")
    print(f"Total Time Elapsed:     {total_time:.2f} seconds")


if __name__ == "__main__":
    main()
