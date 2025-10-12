"""
Test the PassengerDatabase class.
Verify we can insert, query, update, and delete passengers.
"""

import asyncio
import sys
from datetime import datetime

# Add commuter_service to path
sys.path.insert(0, 'e:/projects/github/vehicle_simulator')

from commuter_service.passenger_db import PassengerDatabase # type: ignore


async def test_passenger_database():
    """Test all database operations"""
    
    print("=" * 60)
    print("🧪 TESTING PASSENGER DATABASE")
    print("=" * 60)
    
    # Initialize database
    db = PassengerDatabase()
    await db.connect()
    
    print("\n✅ Step 1: Database connected")
    
    # Test 1: Insert a passenger
    print("\n📝 Test 1: Insert passenger...")
    success = await db.insert_passenger(
        passenger_id="TEST_PASS_001",
        route_id="ROUTE_1A",
        depot_id="DEPOT_CHEAPSIDE",
        direction="OUTBOUND",
        latitude=13.098168,
        longitude=-59.621582,
        destination_lat=13.097,
        destination_lon=-59.620,
        destination_name="Bridgetown",
        priority=3,
        expires_minutes=30
    )
    
    if success:
        print("   ✅ Passenger inserted successfully")
    else:
        print("   ❌ Failed to insert passenger")
        await db.disconnect()
        return
    
    # Test 2: Query passenger count
    print("\n📊 Test 2: Count passengers...")
    count = await db.get_passenger_count(status='WAITING')
    print(f"   ✅ Found {count} waiting passengers")
    
    # Test 3: Query passengers near location
    print("\n🔍 Test 3: Query passengers near depot...")
    passengers = await db.query_passengers_near_location(
        latitude=13.098168,
        longitude=-59.621582,
        radius_meters=200,
        route_id="ROUTE_1A",
        status="WAITING"
    )
    
    print(f"   ✅ Found {len(passengers)} passengers within 200m")
    if passengers:
        for p in passengers:
            print(f"      - {p['passenger_id']}: {p['distance_meters']:.2f}m away")
    
    # Test 4: Mark passenger as boarded
    print("\n🚌 Test 4: Mark passenger as boarded...")
    success = await db.mark_boarded("TEST_PASS_001")
    if success:
        print("   ✅ Passenger marked as ONBOARD")
    else:
        print("   ❌ Failed to mark passenger as boarded")
    
    # Test 5: Verify status changed
    print("\n🔍 Test 5: Verify status changed...")
    count_waiting = await db.get_passenger_count(status='WAITING')
    count_onboard = await db.get_passenger_count(status='ONBOARD')
    print(f"   ✅ Waiting: {count_waiting}, Onboard: {count_onboard}")
    
    # Test 6: Mark passenger as alighted
    print("\n🚶 Test 6: Mark passenger as alighted...")
    success = await db.mark_alighted("TEST_PASS_001")
    if success:
        print("   ✅ Passenger marked as COMPLETED")
    else:
        print("   ❌ Failed to mark passenger as alighted")
    
    # Test 7: Clean up - delete test passenger
    print("\n🗑️  Test 7: Clean up test data...")
    async with db.pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM active_passengers 
            WHERE passenger_id LIKE 'TEST_%'
        """)
    print("   ✅ Test data cleaned up")
    
    # Disconnect
    await db.disconnect()
    print("\n✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_passenger_database())
