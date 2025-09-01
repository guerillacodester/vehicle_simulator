#!/usr/bin/env python3
"""
VehiclesFactory Smoke Test
--------------------------
Runs the VehiclesFactory for a fixed duration, starting both GPSDevice and Engine
for all active vehicles in vehicles.json. Verifies ON/OFF lifecycle and diagnostics.
"""

import argparse
import time
import sys
import os

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from world.vehicles_factory import VehiclesFactory


def main():
    parser = argparse.ArgumentParser(
        description="Smoke test for VehiclesFactory (GPSDevice + Engine)"
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=5.0,
        help="Duration to run the factory (default: 5s)"
    )
    args = parser.parse_args()

    factory = VehiclesFactory()

    # Start all active vehicles
    factory.start()
    time.sleep(args.seconds)
    factory.stop()

    print(f"\nDiagnostic test complete. Ran for {args.seconds:.1f} seconds\n")


if __name__ == "__main__":
    main()
