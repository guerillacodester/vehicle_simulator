#!/usr/bin/env python3
"""
World Vehicles Simulator
------------------------
Entry point for starting and stopping the VehiclesDepot, which manages
GPSDevice and EngineBlock instances for all vehicles in the manifest.
"""

import logging
import sys
import os
import argparse
import time
from world.vehicles_depot import VehiclesDepot  # Add this import

# Configure logging
logging.basicConfig(
    format='[%(levelname)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
        default=1.0,
        help="Simulation tick interval in seconds"
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=10.0,
        help="Total simulation time in seconds"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Set root logger level for debug mode
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    depot = VehiclesDepot(manifest_path=args.manifest, tick_time=args.tick)
    depot.start()
    
    try:
        time.sleep(args.seconds)
    finally:
        depot.stop()

    print(f"\nSimulation complete. Ran for {args.seconds:.1f} seconds\n")


if __name__ == "__main__":
    main()
