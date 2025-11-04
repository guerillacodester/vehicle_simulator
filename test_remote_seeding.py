"""
Quick Test: Remote Seeding via Client Console

This test demonstrates:
1. Client connecting to remote commuter service
2. Subscribing to real-time events
3. Triggering seeding remotely
4. Receiving passenger:spawned events

Prerequisites:
- Commuter service running on http://localhost:4000
- Strapi running on http://localhost:1337
- Geospatial service running on http://localhost:6000

Usage:
    python test_remote_seeding.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from clients.commuter.connector import CommuterConnector


async def main():
    print("=" * 80)
    print("REMOTE SEEDING TEST")
    print("=" * 80)
    print()
    
    # Create connector
    connector = CommuterConnector(base_url="http://localhost:4000")
    
    event_count = 0
    
    def on_passenger_spawned(data):
        """Handle passenger spawned events"""
        nonlocal event_count
        event_count += 1
        print(f"🚶 Event #{event_count:>3}: passenger:spawned | Passenger: {data.get('passenger_id')}")
    
    # Subscribe to events
    connector.on('passenger:spawned', on_passenger_spawned)
    
    try:
        # Connect
        print("📡 Connecting to commuter service...")
        await connector.connect()
        print(f"✅ Connected to {connector.base_url}")
        
        if connector.is_websocket_connected:
            print("✅ WebSocket connected")
        else:
            print("⚠️  WebSocket not available (events will not stream)")
        print()
        
        # Subscribe to route 1
        if connector.is_websocket_connected:
            print("📡 Subscribing to Route 1 events...")
            await connector.subscribe("1")
            print("✅ Subscribed to Route 1")
            print()
        
        # Trigger seeding
        print("🌱 Triggering seeding on server...")
        print("   Route: 1")
        print("   Day: monday")
        print("   Hours: 7-8")
        print()
        
        result = await connector.seed_passengers(
            route="1",
            day="monday",
            spawn_type="route",
            start_hour=7,
            end_hour=8
        )
        
        # Wait for events to arrive
        if connector.is_websocket_connected:
            print("⏳ Waiting for events...")
            await asyncio.sleep(3)
        
        # Show results
        print()
        print("=" * 80)
        print("✅ SEEDING COMPLETE")
        print("=" * 80)
        print(f"Success:          {result['success']}")
        print(f"Route:            {result['route']}")
        print(f"Date:             {result['date']}")
        print(f"Spawn Type:       {result['spawn_type']}")
        print(f"Route Passengers: {result['route_passengers']}")
        print(f"Depot Passengers: {result['depot_passengers']}")
        print(f"Total Created:    {result['total_created']}")
        if connector.is_websocket_connected:
            print(f"Events Received:  {event_count}")
        print("=" * 80)
        print()
        
        if connector.is_websocket_connected:
            if event_count == result['total_created']:
                print("✅ All events received!")
            elif event_count > 0:
                print(f"⚠️  Received {event_count}/{result['total_created']} events")
            else:
                print("⚠️  No events received (check WebSocket connection)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print()
        print("🔌 Disconnecting...")
        await connector.disconnect()
        print("✅ Test complete")


if __name__ == "__main__":
    asyncio.run(main())
