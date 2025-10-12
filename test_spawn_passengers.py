"""
Test script to manually spawn passengers and see detailed logging

This script triggers passenger spawns via Socket.IO to test the system.
"""
import asyncio
import socketio
from datetime import datetime

# Create Socket.IO client
sio = socketio.AsyncClient()

async def spawn_depot_passengers():
    """Spawn test passengers at depots"""
    print("🏢 Triggering depot passenger spawns...")
    
    # Connect to depot reservoir namespace
    await sio.connect('http://localhost:1337', namespaces=['/depot-reservoir'])
    
    # Spawn at depot
    spawn_request = {
        "depot_id": "DEPOT_SPEIGHTSTOWN",
        "route_id": "1A",
        "depot_location": {
            "lat": 13.2778,
            "lon": -59.6419
        },
        "destination": {
            "lat": 13.0969,
            "lon": -59.6143
        },
        "priority": 3,
        "count": 5  # Spawn 5 passengers
    }
    
    print(f"   Sending spawn request: {spawn_request}")
    await sio.emit('spawn_commuter', spawn_request, namespace='/depot-reservoir')
    
    # Wait for spawns to process
    await asyncio.sleep(2)
    
    await sio.disconnect()
    print("✅ Depot spawn requests sent")

async def spawn_route_passengers():
    """Spawn test passengers along routes"""
    print("🛤️  Triggering route passenger spawns...")
    
    # Connect to route reservoir namespace
    await sio.connect('http://localhost:1337', namespaces=['/route-reservoir'])
    
    # Spawn along route 1A
    spawn_requests = [
        {
            "route_id": "1A",
            "current_location": {
                "lat": 13.2500,
                "lon": -59.6300
            },
            "destination": {
                "lat": 13.1500,
                "lon": -59.6000
            },
            "direction": "OUTBOUND",
            "priority": 3
        },
        {
            "route_id": "1A",
            "current_location": {
                "lat": 13.2200,
                "lon": -59.6200
            },
            "destination": {
                "lat": 13.1800,
                "lon": -59.6100
            },
            "direction": "INBOUND",
            "priority": 2
        },
        {
            "route_id": "1A",
            "current_location": {
                "lat": 13.2000,
                "lon": -59.6150
            },
            "destination": {
                "lat": 13.1200,
                "lon": -59.5900
            },
            "direction": "OUTBOUND",
            "priority": 4
        }
    ]
    
    for i, request in enumerate(spawn_requests, 1):
        print(f"   Sending spawn request {i}/{len(spawn_requests)}: {request}")
        await sio.emit('spawn_commuter', request, namespace='/route-reservoir')
        await asyncio.sleep(0.5)  # Small delay between spawns
    
    # Wait for spawns to process
    await asyncio.sleep(2)
    
    await sio.disconnect()
    print("✅ Route spawn requests sent")

async def check_active_passengers():
    """Query active passengers from database"""
    import aiohttp
    
    print("\n📊 Querying active passengers from database...")
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:1337/api/active-passengers') as resp:
            if resp.status == 200:
                data = await resp.json()
                passengers = data.get('data', [])
                print(f"   Total passengers in DB: {len(passengers)}")
                
                if passengers:
                    print("\n   Passenger Details:")
                    for p in passengers[:5]:  # Show first 5
                        attrs = p.get('attributes', {})
                        print(f"      • {attrs.get('passenger_id')} - "
                              f"Route: {attrs.get('route_id')} - "
                              f"Status: {attrs.get('status')} - "
                              f"Location: ({attrs.get('lat'):.4f}, {attrs.get('lon'):.4f})")
                    
                    if len(passengers) > 5:
                        print(f"      ... and {len(passengers) - 5} more")
            else:
                print(f"   ❌ Failed to query passengers: {resp.status}")

async def main():
    """Run all test spawns"""
    print("=" * 80)
    print("🧪 PASSENGER SPAWNING TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test depot spawns
        await spawn_depot_passengers()
        print()
        
        # Test route spawns
        await spawn_route_passengers()
        print()
        
        # Check database
        await check_active_passengers()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("✅ Test complete - Check the Commuter Service terminal for detailed logs")
    print("=" * 80)

if __name__ == '__main__':
    asyncio.run(main())
