#!/usr/bin/env python3
"""
Engine Smoke Test
-----------------
Runs the Engine for a fixed duration using a real vehicle from vehicles.json.
Outputs formatted diagnostics (speed, distance, time, heading placeholder).
"""

import argparse
import json
import time
import sys
import os

# Ensure project root is on sys.path so "world" is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from world.vehicle.engine.engine_block import Engine
from world.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle.engine.sim_speed_model import load_speed_model


def main():
    parser = argparse.ArgumentParser(
        description="Run a diagnostic engine simulation for a vehicle in vehicles.json"
    )
    parser.add_argument(
        "--vehicle-id",
        type=str,
        help="Vehicle ID to simulate (must exist in world/vehicles.json)",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=10.0,
        help="Duration to run the simulation (default: 10s)",
    )
    args = parser.parse_args()

    if not args.vehicle_id:
        print("Usage example:\n")
        print("  ./world/vehicle/engine/engine_smoketest.py --vehicle-id ZR1101 --seconds 5\n")
        sys.exit(1)

    # --- Step 1: Load vehicles.json ---
    vehicles_path = os.path.join(os.path.dirname(__file__), "../../vehicles.json")
    vehicles_abs = os.path.abspath(vehicles_path)

    if not os.path.exists(vehicles_abs):
        print(f"[ERROR] vehicles.json not found at {vehicles_abs}")
        sys.exit(1)

    with open(vehicles_abs, "r", encoding="utf-8") as f:
        vehicles = json.load(f)

    if args.vehicle_id not in vehicles:
        print(f"[ERROR] Vehicle ID '{args.vehicle_id}' not found in vehicles.json")
        sys.exit(1)

    vehicle_cfg = vehicles[args.vehicle_id]

    # --- Step 2: Initialize model, buffer, and engine ---
    buffer = EngineBuffer()
    model = load_speed_model(vehicle_cfg["speed_model"], **vehicle_cfg)
    engine = Engine(args.vehicle_id, model, buffer, tick_time=0.1)

    # --- Step 3: Run for requested duration ---
    engine.on()
    time.sleep(args.seconds)
    engine.off()

    # --- Step 4: Print diagnostics ---
    print(f"\nDiagnostic test. Ran for {args.seconds:.1f} seconds\n")
    while len(buffer) > 0:
        entry = buffer.read()

        velocity = entry["cruise_speed"]
        total_distance = entry["distance"]
        total_time = entry["time"]
        velocity_dir = 0.0  # placeholder until navigation provides heading

        if total_distance < 1.0:
            display_distance = f"{total_distance * 1000:7.1f} m"
        else:
            display_distance = f"{total_distance:7.3f} km"

        print(
            f"{args.vehicle_id} | "
            f"Speed: {velocity:6.2f} km/h | "
            f"Heading: {velocity_dir:6.2f}° | "
            f"Distance: {display_distance} | "
            f"Time: {total_time:.2f} s"
        )


if __name__ == "__main__":
    main()
