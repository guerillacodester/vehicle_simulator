#!/usr/bin/env python3
"""
World Vehicles Simulator
------------------------
Database-driven entry point for the vehicle simulation system.
Loads vehicles, routes, and timetables from PostgreSQL database.
"""

import logging
import sys
import os
import argparse
import time
import textwrap
import atexit
from database_vehicles_simulator import DatabaseVehiclesDepot

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

def create_parser():
    """Create argument parser with proper help messages"""
    parser = argparse.ArgumentParser(
        description="ZR Van Simulator - Database-driven public transport simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          %(prog)s --debug                     Run with debug output
          %(prog)s --tick 0.5 --seconds 30     Run for 30 seconds, update every 0.5s
          %(prog)s --no-gps                    Run without GPS transmission
          
        Data Source:
          All vehicle, route, and timetable data is loaded from the PostgreSQL database
          at arknetglobal.com. No JSON files are required.
        """)
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
        default=60.0,
        help="Simulation duration in seconds (default: 60.0)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--no-gps",
        action="store_true",
        help="Disable GPS transmission to WebSocket server"
    )
    
    return parser

def main():
    """Main simulation entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        print("🐛 Debug logging enabled")
        
    print("=" * 60)
    print("🚌 ZR Van Simulator - Database Edition")
    print("=" * 60)
    print(f"⏱️  Update Interval: {args.tick} seconds")
    print(f"⏰ Duration: {args.seconds} seconds")
    print(f"📡 GPS Transmission: {'disabled' if args.no_gps else 'enabled'}")
    print(f"🗄️ Data Source: PostgreSQL Database (arknetglobal.com)")
    print("-" * 60)
    
    depot = None
    try:
        # Initialize database-driven depot
        print("🔌 Connecting to database...")
        depot = DatabaseVehiclesDepot(tick_time=args.tick)
        
        # Start simulation
        depot.start()
        
        if args.debug:
            print(f"\n=== Simulation Started at {time.strftime('%H:%M:%S')} ===")
        
        # Main simulation loop
        start_time = time.time()
        last_status_time = 0
        
        while time.time() - start_time < args.seconds:
            depot.update()
            
            # Show status every 15 seconds
            current_time = time.time() - start_time
            if current_time - last_status_time >= 15:
                print(f"\n⏰ Time: {current_time:.1f}s")
                print(depot.get_status())
                last_status_time = current_time
            
            time.sleep(args.tick)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted by user")
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
    finally:
        if depot:
            depot.stop()
        print("-" * 60)
        if args.debug:
            print(f"=== Simulation Ended at {time.strftime('%H:%M:%S')} ===")
        print("✅ ZR Van Simulation Complete")
        
if __name__ == "__main__":
    main()
