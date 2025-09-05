#!/usr/bin/env python3
"""
World Vehicles Simulator
------------------------
Entry point for starting and stopping the VehiclesDepot, which manages
GPSDevice and EngineBlock instances for all vehicles in the manifest.
"""

import argparse
import sys
import os
import time

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from world.vehicle_depot.depot_manager import VehiclesDepot


def main():
    parser = argparse.ArgumentParser(description="World Vehicles Simulator")
    parser.add_argument(
        "--manifest",
        type=str,
        default="world/vehicles.json",
        help="Path to vehicles manifest (default: world/vehicles.json)",
    )
    parser.add_argument(
        "--tick",
        type=float,
        default=0.1,
        help="Tick interval in seconds (default: 0.1)",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=5.0,
        help="How long to run the simulator (default: 5s)",
    )
    args = parser.parse_args()

    # Create VehiclesDepot with corrected arguments
    depot = VehiclesDepot(
        manifest_path=args.manifest,
        tick_time=args.tick,
    )

    # Start all active vehicles
    depot.start()
    time.sleep(args.seconds)
    depot.stop()

    print(f"\nSimulation complete. Ran for {args.seconds:.1f} seconds\n")


if __name__ == "__main__":
    main()
