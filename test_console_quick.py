#!/usr/bin/env python3
"""
Quick console commands to test services
"""

import asyncio
import sys
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0])

from clients.fleet.fleet_console import FleetConsole


async def main():
    console = FleetConsole(api_url="http://localhost:6000")
    
    print("\n" + "="*80)
    print("🔧 CHECKING SERVICES")
    print("="*80)
    await console.cmd_services()
    
    await asyncio.sleep(2)
    
    print("\n" + "="*80)
    print("🚗 CHECKING VEHICLES")
    print("="*80)
    await console.cmd_vehicles()


if __name__ == "__main__":
    asyncio.run(main())
