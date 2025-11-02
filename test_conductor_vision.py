#!/usr/bin/env python3
"""
Conductor Vision Test - See What the Conductor Sees
===================================================

This script demonstrates the conductor's "eyes" throughout a journey:
1. What passengers are at the depot (before departure)
2. Boarding decisions and driver communication
3. Passengers discovered along the route
4. Stop/start signals to driver

Prerequisites:
- Strapi running (localhost:1337)
- Passengers seeded for route (use commuter_service/seed.py)
- GPSCentCom server running (localhost:5000)

Usage:
    # Seed passengers first
    python commuter_service/seed.py --route 1 --day monday --start-hour 7 --end-hour 9 --type route
    
    # Run conductor vision test
    python test_conductor_vision.py --route 1 --duration 300
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from arknet_transit_simulator.simulator import CleanVehicleSimulator
from arknet_transit_simulator.config.config_loader import ConfigLoader

# Configure colored logging
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for conductor vision."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    
    CONDUCTOR_COLOR = '\033[1;34m'  # Bold Blue
    DRIVER_COLOR = '\033[1;33m'     # Bold Yellow
    PASSENGER_COLOR = '\033[1;32m'  # Bold Green
    RESET = '\033[0m'
    
    def format(self, record):
        # Color by log level
        color = self.COLORS.get(record.levelname, '')
        
        # Special coloring for conductor messages
        if 'Conductor' in record.getMessage():
            color = self.CONDUCTOR_COLOR
        elif 'Driver' in record.getMessage():
            color = self.DRIVER_COLOR
        elif 'passenger' in record.getMessage().lower():
            color = self.PASSENGER_COLOR
        
        # Format message with color
        log_fmt = f"{color}%(asctime)s | %(levelname)-8s | %(message)s{self.RESET}"
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)


async def test_conductor_vision(route_id: str = "1", duration: int = 300):
    """
    Run conductor vision test.
    
    Args:
        route_id: Route to monitor
        duration: Test duration in seconds (default 5 minutes)
    """
    print("=" * 80)
    print("🚌 CONDUCTOR VISION TEST - See What the Conductor Sees")
    print("=" * 80)
    print()
    print(f"Route: {route_id}")
    print(f"Duration: {duration} seconds ({duration / 60:.1f} minutes)")
    print()
    print("=" * 80)
    print()
    
    # Load GPS config
    config_loader = ConfigLoader()
    gps_config = config_loader.get_gps_config()
    
    # Create simulator
    sim = CleanVehicleSimulator(
        api_url=None,  # Auto-load from config
        enable_boarding_after=5.0,  # Enable boarding after 5 seconds
        gps_config=gps_config
    )
    
    # Initialize
    print("🔧 Initializing simulator...")
    if not await sim.initialize():
        print("❌ Initialization failed")
        return 1
    
    print("✅ Simulator initialized")
    print()
    print("=" * 80)
    print("📋 INITIAL STATE - What Conductor Sees at Depot")
    print("=" * 80)
    print()
    
    # Query depot passengers before departure
    await asyncio.sleep(2)  # Wait for conductor initialization
    
    # Start simulation
    print()
    print("=" * 80)
    print("🚀 Starting Journey - Watch Conductor's Eyes")
    print("=" * 80)
    print()
    print("Legend:")
    print("  🔵 Conductor actions (Blue)")
    print("  🟡 Driver actions (Yellow)")
    print("  🟢 Passenger events (Green)")
    print()
    print("=" * 80)
    print()
    
    # Run simulation
    await sim.run(duration=duration)
    
    print()
    print("=" * 80)
    print("✅ Test Complete")
    print("=" * 80)
    
    return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Test conductor vision - see what conductor sees during journey"
    )
    parser.add_argument(
        '--route',
        type=str,
        default="1",
        help='Route ID to monitor (default: 1)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=300,
        help='Test duration in seconds (default: 300 = 5 minutes)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Configure logging with colors
    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Filter to show only conductor-relevant logs
    class ConductorFilter(logging.Filter):
        """Show conductor, driver, passenger, and system logs."""
        def filter(self, record):
            msg = record.getMessage().lower()
            # Show conductor/driver/passenger/system messages
            if any(keyword in msg for keyword in [
                'conductor', 'driver', 'passenger', 'board', 'alight',
                'depot', 'route', 'stop', 'start', 'engine', 'gps',
                'eligible', 'pickup', 'seats', 'full', 'empty'
            ]):
                return True
            # Hide noise
            return record.levelname in ['WARNING', 'ERROR', 'CRITICAL']
    
    # Only apply filter if not in debug mode
    if not args.debug:
        handler.addFilter(ConductorFilter())
    
    # Run test
    try:
        exit_code = asyncio.run(test_conductor_vision(
            route_id=args.route,
            duration=args.duration
        ))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
