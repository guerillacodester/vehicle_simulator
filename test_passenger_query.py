"""Test get_eligible_passengers method"""
import asyncio
from commuter_service.passenger_db import PassengerDatabase

async def test_query():
    db = PassengerDatabase()
    await db.connect()
    
    try:
        # Test query near a location
        print("🔍 Testing get_eligible_passengers...")
        print("   Location: 13.1000, -59.6000")
        print("   Route: ROUTE_1A")
        print("   Radius: 0.2 km\n")
        
        passengers = await db.get_eligible_passengers(
            vehicle_lat=13.1000,
            vehicle_lon=-59.6000,
            route_id="ROUTE_1A",
            pickup_radius_km=0.2
        )
        
        if passengers:
            print(f"✅ Found {len(passengers)} passengers:")
            for i, p in enumerate(passengers[:5], 1):  # Show first 5
                print(f"   {i}. ID: {p.get('passenger_id', 'N/A')}")
                print(f"      Priority: {p.get('priority', 'N/A')}")
                print(f"      Status: {p.get('status', 'N/A')}")
        else:
            print("ℹ️  No passengers found (this is OK if database is empty)")
            
    finally:
        await db.disconnect()

asyncio.run(test_query())
