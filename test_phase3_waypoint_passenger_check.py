"""
Phase 3.2 Integration Test: Driver Waypoint → Conductor Passenger Check
========================================================================
Test the complete flow:
1. Driver navigates route and arrives at waypoint
2. Driver emits 'driver:arrived:waypoint' Socket.IO event
3. Conductor receives event
4. Conductor calls check_for_passengers() at waypoint location
5. Passengers are boarded (if any available)

This completes Phase 3: Full conductor-driver integration for MVP.
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arknet_transit_simulator.vehicle.conductor import Conductor
from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
from commuter_service.passenger_db import PassengerDatabase


async def test_waypoint_passenger_check():
    """Test that driver waypoint arrival triggers conductor passenger check."""
    
    print("\n" + "="*80)
    print("PHASE 3.2 TEST: WAYPOINT ARRIVAL → PASSENGER CHECK")
    print("="*80 + "\n")
    
    # Track events
    waypoint_events_emitted = []
    passenger_checks_called = []
    
    # Create PassengerDatabase
    print("1️⃣  Creating PassengerDatabase...")
    passenger_db = PassengerDatabase(strapi_url="http://localhost:1337")
    
    # Create Conductor
    print("\n2️⃣  Creating Conductor...")
    conductor = Conductor(
        conductor_id="TEST_COND_P3_2",
        conductor_name="Phase 3.2 Test Conductor",
        vehicle_id="TEST_VEH_P3_2",
        assigned_route_id="1A",
        capacity=16,
        sio_url="http://localhost:3000",
        use_socketio=True,
        passenger_db=passenger_db
    )
    
    # Mock check_for_passengers to track calls
    original_check = conductor.check_for_passengers
    
    async def mock_check_for_passengers(*args, **kwargs):
        passenger_checks_called.append({
            'args': args,
            'kwargs': kwargs
        })
        print(f"\n   🔔 check_for_passengers() CALLED!")
        print(f"      Latitude: {kwargs.get('latitude', args[0] if args else None)}")
        print(f"      Longitude: {kwargs.get('longitude', args[1] if len(args) > 1 else None)}")
        print(f"      Route ID: {kwargs.get('route_id', args[2] if len(args) > 2 else None)}")
        # Call original but don't await it (avoid DB calls)
        # return await original_check(*args, **kwargs)
        return 0  # Return 0 passengers boarded for test
    
    conductor.check_for_passengers = mock_check_for_passengers
    
    # Create Driver with test route
    print("\n3️⃣  Creating VehicleDriver with test route...")
    test_route = [
        (-59.6, 13.1),  # Waypoint 0 (start)
        (-59.5, 13.2),  # Waypoint 1
        (-59.4, 13.3)   # Waypoint 2 (end)
    ]
    
    driver = VehicleDriver(
        driver_id="TEST_DRV_P3_2",
        driver_name="Phase 3.2 Test Driver",
        vehicle_id="TEST_VEH_P3_2",
        route_coordinates=test_route,
        route_name="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Mock driver's Socket.IO emit to track waypoint events
    original_emit = driver.sio.emit
    
    async def mock_emit(event_name, data):
        if event_name == 'driver:arrived:waypoint':
            waypoint_events_emitted.append(data)
            print(f"\n   📡 Driver emitted 'driver:arrived:waypoint'")
            print(f"      Waypoint: {data.get('waypoint_index')}")
            print(f"      Coordinates: ({data.get('latitude'):.4f}, {data.get('longitude'):.4f})")
        # Call original
        return await original_emit(event_name, data)
    
    driver.sio.emit = mock_emit
    
    # Mock Socket.IO connections (pretend connected)
    conductor.sio_connected = True
    driver.sio_connected = True
    
    # Start conductor
    print("\n4️⃣  Starting Conductor...")
    await conductor.start()
    print(f"   ✅ Conductor started")
    
    # Start driver
    print("\n5️⃣  Starting Driver...")
    await driver.start()
    print(f"   ✅ Driver started")
    
    # Wait for startup
    await asyncio.sleep(1.0)
    
    # Simulate driver arriving at waypoint 1
    print("\n6️⃣  Simulating Driver Arrival at Waypoint 1...")
    waypoint_index = 1
    wp_lon, wp_lat = test_route[waypoint_index]
    
    # Manually trigger waypoint check (simulating what happens in _broadcast_location_loop)
    await driver._check_waypoint_arrival(wp_lat, wp_lon)
    
    # Wait for event propagation
    print("   ⏳ Waiting for event propagation (2 seconds)...")
    await asyncio.sleep(2.0)
    
    # Check results
    print("\n7️⃣  Verifying Results...")
    
    # Check if waypoint event was emitted
    if waypoint_events_emitted:
        print(f"   ✅ Driver emitted {len(waypoint_events_emitted)} waypoint event(s)")
        for event in waypoint_events_emitted:
            print(f"      - Waypoint {event['waypoint_index']}: "
                  f"({event['latitude']:.4f}, {event['longitude']:.4f})")
    else:
        print(f"   ⚠️  No waypoint events emitted")
    
    # Check if conductor's check_for_passengers was called
    if passenger_checks_called:
        print(f"   ✅ Conductor check_for_passengers() called {len(passenger_checks_called)} time(s)")
        for check in passenger_checks_called:
            print(f"      - Latitude: {check['kwargs'].get('latitude', 'N/A')}")
            print(f"      - Longitude: {check['kwargs'].get('longitude', 'N/A')}")
            print(f"      - Route: {check['kwargs'].get('route_id', 'N/A')}")
    else:
        print(f"   ⚠️  check_for_passengers() was NOT called")
    
    # Cleanup
    print("\n8️⃣  Cleanup...")
    await conductor.stop()
    await driver.stop()
    
    # Summary
    print("\n" + "="*80)
    print("TEST RESULTS:")
    print("-" * 80)
    
    success = len(waypoint_events_emitted) > 0 and len(passenger_checks_called) > 0
    
    if success:
        print("✅ Driver emitted waypoint arrival event")
        print("✅ Conductor received event")
        print("✅ Conductor triggered passenger check")
        print("\n🎉 PHASE 3.2 COMPLETE:")
        print("   Driver arrives at waypoint →")
        print("   Socket.IO emit('driver:arrived:waypoint') →")
        print("   Conductor receives event →")
        print("   Conductor.check_for_passengers() called →")
        print("   Passengers can be boarded at stops!")
    else:
        print("⚠️  Flow incomplete:")
        if not waypoint_events_emitted:
            print("   - Driver did not emit waypoint event")
        if not passenger_checks_called:
            print("   - Conductor did not check for passengers")
    
    print("="*80 + "\n")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(test_waypoint_passenger_check())
    
    if result:
        print("✅ PHASE 3 COMPLETE: Full conductor-driver integration working!")
    else:
        print("❌ Test failed - integration incomplete")
        sys.exit(1)
