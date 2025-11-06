#!/usr/bin/env python3
"""
Test console connected directly to simulator
"""

import asyncio
import sys
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0])

from clients.fleet.fleet_console import FleetConsole


async def main():
    # Connect directly to simulator on port 5001
    console = FleetConsole(api_url="http://localhost:5001")
    
    print("\n" + "="*80)
    print("✅ Connected to SIMULATOR directly (port 5001)")
    print("="*80)
    
    print("\n🚗 CHECKING VEHICLES")
    print("="*80)
    await console.cmd_vehicles()


if __name__ == "__main__":
    asyncio.run(main())
