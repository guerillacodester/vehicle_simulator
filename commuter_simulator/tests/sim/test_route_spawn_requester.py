#!/usr/bin/env python3
"""
Route Spawner Test - Lightweight Requester
===========================================

Makes HTTP request to RouteSpawnerService and streams responses in real-time.
Pure client - no spawning logic, no database access, no plugin initialization.

Usage:
  python test_route_spawn_requester.py [route_id] [day] [time] [window]
  
  route_id: Route to spawn for (default: gg3pv3z19hhm117v9xth5ezq)
  day: Day of week (default: Monday)
  time: Spawn time HH:MM:SS (default: 09:00:00)
  window: Spawn window in minutes (default: 60)

Examples:
  python test_route_spawn_requester.py
  python test_route_spawn_requester.py gg3pv3z19hhm117v9xth5ezq Monday 09:00:00 60
  python test_route_spawn_requester.py gg3pv3z19hhm117v9xth5ezq Friday 14:30:00 45
"""

import asyncio
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
import logging

import httpx


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


SPAWNER_SERVICE_URL = "http://localhost:8002"
VALID_DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


async def stream_spawns(
    route_id: str,
    day: str,
    time: str,
    window: int
):
    """
    Stream spawned passengers from RouteSpawnerService.
    
    Connects to service and prints each spawn as it arrives.
    """
    url = f"{SPAWNER_SERVICE_URL}/spawn/route/{route_id}"
    params = {
        "time": time,
        "day": day,
        "window": window
    }
    
    print("=" * 100)
    print("ROUTE SPAWNER TEST - Lightweight Requester")
    print("=" * 100)
    print(f"\n📡 Connecting to {SPAWNER_SERVICE_URL}...")
    print(f"   Route: {route_id}")
    print(f"   Day: {day}")
    print(f"   Time: {time}")
    print(f"   Window: {window} minutes\n")
    
    spawn_count = 0
    error_occurred = False
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("GET", url, params=params) as response:
                if response.status_code != 200:
                    error_text = await response.aread().decode()
                    print(f"❌ Error: {response.status_code} - {error_text}")
                    return
                
                print("✅ Connected! Streaming spawns...\n")
                
                # Read NDJSON stream
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        spawn_data = json.loads(line)
                        
                        # Check for errors
                        if "error" in spawn_data:
                            print(f"❌ Error from service: {spawn_data['error']}")
                            error_occurred = True
                            break
                        
                        # Print spawn data
                        spawn_count += 1
                        passenger_id = spawn_data.get('passenger_id', 'UNKNOWN')
                        spawn_loc = spawn_data.get('spawn_location', [0, 0])
                        dest_loc = spawn_data.get('destination_location', [0, 0])
                        
                        print(
                            f"[{spawn_count:3d}] {passenger_id:15s} | "
                            f"Board: ({spawn_loc[0]:8.4f}, {spawn_loc[1]:9.4f}) | "
                            f"Dest: ({dest_loc[0]:8.4f}, {dest_loc[1]:9.4f})"
                        )
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON: {line[:50]}... ({e})")
                        continue
                    except KeyError as e:
                        logger.warning(f"Missing field in spawn data: {e}")
                        continue
                
                if not error_occurred:
                    print(f"\n{'='*100}")
                    print(f"✅ Streaming complete! Total spawned: {spawn_count} passengers")
                    print(f"{'='*100}\n")
    
    except httpx.ConnectError:
        print(f"❌ Connection error: Cannot reach {SPAWNER_SERVICE_URL}")
        print("   Make sure RouteSpawnerService is running (python -m commuter_simulator.services.route_spawner_service)")
        sys.exit(1)
    except httpx.TimeoutException:
        print(f"❌ Timeout: Service took too long to respond")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Stream route spawns from RouteSpawnerService",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_route_spawn_requester.py
  python test_route_spawn_requester.py gg3pv3z19hhm117v9xth5ezq Monday 09:00:00 60
  python test_route_spawn_requester.py gg3pv3z19hhm117v9xth5ezq Friday 14:30:00 45
        """
    )
    
    parser.add_argument(
        'route_id',
        nargs='?',
        default='gg3pv3z19hhm117v9xth5ezq',
        help='Route to spawn for (default: gg3pv3z19hhm117v9xth5ezq)'
    )
    parser.add_argument(
        'day',
        nargs='?',
        default='Monday',
        help='Day of week (default: Monday)'
    )
    parser.add_argument(
        'time',
        nargs='?',
        default='09:00:00',
        help='Spawn time HH:MM:SS (default: 09:00:00)'
    )
    parser.add_argument(
        'window',
        nargs='?',
        type=int,
        default=60,
        help='Spawn window in minutes (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Validate day
    if args.day.lower() not in VALID_DAYS:
        print(f"❌ Invalid day: {args.day}")
        print(f"   Valid days: {', '.join(VALID_DAYS)}")
        sys.exit(1)
    
    # Validate time format
    try:
        datetime.strptime(args.time, '%H:%M:%S')
    except ValueError:
        print(f"❌ Invalid time format: {args.time}")
        print("   Use HH:MM:SS format")
        sys.exit(1)
    
    # Stream spawns
    await stream_spawns(
        route_id=args.route_id,
        day=args.day,
        time=args.time,
        window=args.window
    )


if __name__ == "__main__":
    asyncio.run(main())
