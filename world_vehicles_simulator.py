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
import textwrap
import atexit
from world.vehicles_depot import VehiclesDepot

# Configure minimal logging with our format
logging.basicConfig(
    format='%(message)s',
    level=logging.ERROR,
    force=True  # Override any existing handlers
)

def shutdown_handler():
    """Clean shutdown handler"""
    logging.shutdown()

# Register shutdown handler
atexit.register(shutdown_handler)

class SimulationFilter(logging.Filter):
    """Filter to only show vehicle state changes and critical simulation events"""
    def filter(self, record):
        # Only show specific state changes
        state_messages = [
            'initial state',
            'state: STARTING',
            'state: ACTIVE',
            'state: STOPPED',
            'final state'
        ]
        return any(msg in record.msg for msg in state_messages)

class SimulationFormatter(logging.Formatter):
    """Format simulation messages cleanly"""
    def format(self, record):
        if 'Vehicle' in record.msg and 'state' in record.msg:
            # Clean up state messages
            msg = record.msg.replace('[INFO] ', '')
            msg = msg.replace('Vehicle ', '')
            msg = msg.replace('state: ', '')
            return f"Vehicle {msg}"
        return record.msg

def create_parser():
    """Create argument parser with proper help messages"""
    parser = argparse.ArgumentParser(
        description="ZR Van Simulator - A public transport simulation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          %(prog)s --debug                     Run with debug output
          %(prog)s --tick 0.5 --seconds 10     Run for 10 seconds, update every 0.5s
          %(prog)s --timetable schedules.json  Run with custom timetable
        """)
    )
    
    parser.add_argument(
        "--manifest",
        type=str,
        default="world/vehicles.json",
        help="Vehicle manifest file path (default: world/vehicles.json)"
    )
    parser.add_argument(
        "--tick",
        type=float,
        default=1.0,
        help="Update interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=10.0,
        help="Simulation duration in seconds (default: 10.0)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--timetable",
        type=str,
        help="Timetable file path"
    )
    
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    if args.debug:
        # Configure clean logging output
        handler = logging.StreamHandler()
        handler.addFilter(SimulationFilter())
        handler.setFormatter(SimulationFormatter())
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]
        root_logger.setLevel(logging.DEBUG)
        
        print("\n=== ZR Van Simulator ===")
        print(f"Start Time: {time.strftime('%H:%M:%S')}")
        print(f"Duration: {args.seconds} seconds")
        print("-" * 50)
    
    depot = None
    try:
        depot = VehiclesDepot(
            manifest_path=args.manifest, 
            tick_time=args.tick,
            timetable_path=args.timetable
        )
        depot.start()
        time.sleep(args.seconds)
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    finally:
        if depot:
            depot.stop()
        print("-" * 50)
        if args.debug:
            print(f"\nEnd Time: {time.strftime('%H:%M:%S')}")
        print("Simulation complete.")
        
if __name__ == "__main__":
    main()
