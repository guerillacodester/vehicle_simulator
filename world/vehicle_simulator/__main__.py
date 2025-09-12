"""Package entrypoint for clean vehicle simulator.

Usage examples:
  python -m world.vehicle_simulator --mode display
  python -m world.vehicle_simulator --mode depot --duration 60
"""
from __future__ import annotations
import argparse
import asyncio
import logging
import sys

from .simulator import CleanVehicleSimulator

log = logging.getLogger("vehicle_simulator.entry")


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="python -m world.vehicle_simulator",
                                description="Clean Vehicle Simulator (depot + dispatcher only)")
    p.add_argument('--mode', choices=['display', 'depot'], default='display', help='Mode to run')
    p.add_argument('--duration', type=float, default=None, help='Duration in seconds (depot mode)')
    p.add_argument('--api-url', type=str, default='http://localhost:8000', help='Fleet Manager API base URL')
    p.add_argument('--debug', action='store_true', help='Enable debug logging')
    return p.parse_args(argv)


async def run_display(sim: CleanVehicleSimulator):
    print("=" * 72)
    print("VEHICLE-DRIVER-ROUTE ASSIGNMENT EVIDENCE")
    print("=" * 72)
    assignments = await sim.get_vehicle_assignments()
    if not assignments:
        print("No assignments available (API may be down or empty).")
        return
    print(f"Found {len(assignments)} assignments:\n")
    for idx, a in enumerate(assignments, 1):
        print(f"Assignment {idx}:")
        print(f"  Vehicle: {a.vehicle_reg_code}")
        print(f"  Driver : {a.driver_name}")
        print(f"  Route  : {a.route_name}")
        route = await sim.get_route_info(a.route_id)
        if route and route.geometry:
            count = route.coordinate_count or (len(route.geometry.get('coordinates', [])) if isinstance(route.geometry, dict) else 'Unknown')
            print(f"  GPS Points: {count}")
        else:
            print("  GPS Points: (none)")
        print()


async def main_async(argv=None):
    args = parse_args(argv)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

    sim = CleanVehicleSimulator(api_url=args.api_url)
    if not await sim.initialize():
        print("Initialization failed. Exiting.")
        return 1

    if args.mode == 'display':
        await run_display(sim)
        await sim.shutdown()
        return 0
    else:  # depot mode
        await sim.run(duration=args.duration)
        return 0


def main():  # pragma: no cover
    try:
        exit_code = asyncio.run(main_async())
    except KeyboardInterrupt:
        print("Interrupted by user")
        exit_code = 130
    sys.exit(exit_code)


if __name__ == '__main__':  # pragma: no cover
    main()
