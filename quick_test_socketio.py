"""
Quick Socket.IO Test - No pytest required
==========================================
Simple test to verify Conductor and Driver Socket.IO communication.
"""

import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arknet_transit_simulator.vehicle.conductor import Conductor, StopOperation
from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
from datetime import datetime


async def test_basic_connection():
    """Test basic Socket.IO connection."""
    print("\n" + "="*80)
    print("TEST 1: Basic Socket.IO Connection")
    print("="*80 + "\n")
    
    # Create conductor
    conductor = Conductor(
        conductor_id="QUICK_TEST_COND",
        conductor_name="Quick Test Conductor",
        vehicle_id="QUICK_TEST_VEH",
        assigned_route_id="1A",
        capacity=40,
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Create driver
    driver = VehicleDriver(
        driver_id="QUICK_TEST_DRV",
        driver_name="Quick Test Driver",
        vehicle_id="QUICK_TEST_VEH",
        route_coordinates=[[40.7128, -74.0060], [40.7589, -73.9851], [40.7800, -73.9700]],
        route_name="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    print("📤 Starting Conductor...")
    conductor_started = await conductor.start()
    print(f"   ✅ Conductor started: {conductor_started}")
    
    print("\n📤 Starting Driver...")
    driver_started = await driver.start()
    print(f"   ✅ Driver started: {driver_started}")
    
    # Wait for connections
    print("\n⏳ Waiting for Socket.IO connections (3 seconds)...")
    await asyncio.sleep(3.0)
    
    print(f"\n📊 Connection Status:")
    print(f"   Conductor Socket.IO connected: {conductor.sio_connected}")
    print(f"   Driver Socket.IO connected: {driver.sio_connected}")
    print(f"   Driver state: {driver.current_state.value}")
    
    if conductor.sio_connected and driver.sio_connected:
        print("\n✅ TEST PASSED: Both components connected to Socket.IO")
    else:
        print("\n❌ TEST FAILED: Socket.IO connections not established")
        print("   Make sure Socket.IO server is running on http://localhost:3000")
        print("   Run: python test_socketio_server.py")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await conductor.stop()
    await driver.stop()
    await asyncio.sleep(1.0)
    
    return conductor.sio_connected and driver.sio_connected


async def test_stop_and_depart():
    """Test stop request and depart signal."""
    print("\n" + "="*80)
    print("TEST 2: Stop Request and Depart Signal")
    print("="*80 + "\n")
    
    # Create components
    conductor = Conductor(
        conductor_id="STOP_TEST_COND",
        conductor_name="Stop Test Conductor",
        vehicle_id="STOP_TEST_VEH",
        assigned_route_id="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    driver = VehicleDriver(
        driver_id="STOP_TEST_DRV",
        driver_name="Stop Test Driver",
        vehicle_id="STOP_TEST_VEH",
        route_coordinates=[[40.7128, -74.0060], [40.7589, -73.9851]],
        route_name="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Start both
    await conductor.start()
    await driver.start()
    await asyncio.sleep(2.0)
    
    print(f"📊 Initial driver state: {driver.current_state.value}")
    
    # Start engine
    print("\n🚗 Starting driver's engine...")
    await driver.start_engine()
    print(f"   ✅ Driver state: {driver.current_state.value}")
    
    await asyncio.sleep(2.0)
    
    # Create stop operation
    print("\n📋 Creating stop operation...")
    conductor.current_stop_operation = StopOperation(
        stop_id="QUICK_STOP",
        stop_name="Quick Test Stop",
        latitude=40.7128,
        longitude=-74.0060,
        passengers_boarding=["P001", "P002"],
        passengers_disembarking=["P003"],
        requested_duration=3.0,  # 3 seconds
        start_time=datetime.now(),
        gps_position=(40.7128, -74.0060)
    )
    
    print("📤 Conductor sending STOP request...")
    await conductor._signal_driver_stop()
    
    # Wait for stop to complete
    print("⏳ Waiting for stop operation (5 seconds)...")
    await asyncio.sleep(5.0)
    
    print(f"\n📊 Driver state after stop: {driver.current_state.value}")
    
    # Send depart signal
    print("\n📤 Conductor sending DEPART signal...")
    await conductor._signal_driver_continue()
    
    # Wait for restart
    await asyncio.sleep(2.0)
    
    print(f"📊 Driver state after depart: {driver.current_state.value}")
    
    # Verify state transitions
    success = driver.current_state.value == "ONBOARD"
    
    if success:
        print("\n✅ TEST PASSED: Stop and depart signals working")
    else:
        print("\n❌ TEST FAILED: Driver did not return to ONBOARD state")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await conductor.stop()
    await driver.stop()
    await asyncio.sleep(1.0)
    
    return success


async def test_location_broadcasting():
    """Test driver location broadcasting."""
    print("\n" + "="*80)
    print("TEST 3: Location Broadcasting")
    print("="*80 + "\n")
    
    driver = VehicleDriver(
        driver_id="LOC_TEST_DRV",
        driver_name="Location Test Driver",
        vehicle_id="LOC_TEST_VEH",
        route_coordinates=[[40.7128, -74.0060], [40.7589, -73.9851], [40.7800, -73.9700]],
        route_name="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Start driver
    await driver.start()
    await asyncio.sleep(2.0)
    
    print(f"📊 Driver connected: {driver.sio_connected}")
    print(f"📊 Location broadcast task: {driver.location_broadcast_task is not None}")
    
    # Start engine (location broadcasting requires ONBOARD state)
    print("\n🚗 Starting engine...")
    await driver.start_engine()
    print(f"   ✅ Driver state: {driver.current_state.value}")
    
    # Let it broadcast
    print("\n📡 Broadcasting location for 12 seconds (should see 2-3 broadcasts)...")
    print("   Check the Socket.IO server console for location updates")
    await asyncio.sleep(12.0)
    
    success = driver.sio_connected and driver.current_state.value == "ONBOARD"
    
    if success:
        print("\n✅ TEST PASSED: Location broadcasting active")
        print("   (Check server console to verify location updates were received)")
    else:
        print("\n❌ TEST FAILED: Location broadcasting not working")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await driver.stop()
    await asyncio.sleep(1.0)
    
    return success


async def test_fallback():
    """Test fallback to callbacks."""
    print("\n" + "="*80)
    print("TEST 4: Fallback to Callbacks")
    print("="*80 + "\n")
    
    callback_received = {'stop': False, 'continue': False}
    
    def mock_callback(conductor_id, data):
        action = data.get('action')
        if action == 'stop_vehicle':
            callback_received['stop'] = True
            print(f"   ✅ Callback received: STOP signal")
        elif action == 'continue_driving':
            callback_received['continue'] = True
            print(f"   ✅ Callback received: CONTINUE signal")
    
    # Create conductor with Socket.IO DISABLED
    conductor = Conductor(
        conductor_id="FALLBACK_COND",
        conductor_name="Fallback Conductor",
        vehicle_id="FALLBACK_VEH",
        assigned_route_id="1A",
        use_socketio=False  # Disable Socket.IO
    )
    
    conductor.set_driver_callback(mock_callback)
    
    await conductor.start()
    await asyncio.sleep(1.0)
    
    print(f"📊 Socket.IO disabled: {not conductor.use_socketio}")
    
    # Create stop operation
    conductor.current_stop_operation = StopOperation(
        stop_id="FALLBACK_STOP",
        stop_name="Fallback Stop",
        latitude=40.7128,
        longitude=-74.0060,
        passengers_boarding=["P001"],
        passengers_disembarking=[],
        requested_duration=1.0,
        start_time=datetime.now(),
        gps_position=(40.7128, -74.0060)
    )
    
    print("\n📤 Sending stop signal (should use callback)...")
    await conductor._signal_driver_stop()
    await asyncio.sleep(1.0)
    
    print("\n📤 Sending continue signal (should use callback)...")
    await conductor._signal_driver_continue()
    await asyncio.sleep(1.0)
    
    success = callback_received['stop'] and callback_received['continue']
    
    if success:
        print("\n✅ TEST PASSED: Callback fallback working")
    else:
        print("\n❌ TEST FAILED: Callbacks not received")
    
    await conductor.stop()
    
    return success


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SOCKET.IO INTEGRATION QUICK TESTS")
    print("="*80)
    print("\n⚠️  PREREQUISITE: Socket.IO server must be running")
    print("   Run in another terminal: python test_socketio_server.py")
    print("\n" + "="*80 + "\n")
    
    input("Press Enter to start tests...")
    
    results = {}
    
    # Run tests
    try:
        results['connection'] = await test_basic_connection()
    except Exception as e:
        print(f"\n❌ Connection test failed with error: {e}")
        results['connection'] = False
    
    if results['connection']:
        try:
            results['stop_depart'] = await test_stop_and_depart()
        except Exception as e:
            print(f"\n❌ Stop/depart test failed with error: {e}")
            results['stop_depart'] = False
        
        try:
            results['location'] = await test_location_broadcasting()
        except Exception as e:
            print(f"\n❌ Location test failed with error: {e}")
            results['location'] = False
    else:
        print("\n⚠️  Skipping remaining tests due to connection failure")
        results['stop_depart'] = False
        results['location'] = False
    
    try:
        results['fallback'] = await test_fallback()
    except Exception as e:
        print(f"\n❌ Fallback test failed with error: {e}")
        results['fallback'] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\n  1. Connection Test:      {'✅ PASS' if results['connection'] else '❌ FAIL'}")
    print(f"  2. Stop/Depart Test:     {'✅ PASS' if results['stop_depart'] else '❌ FAIL'}")
    print(f"  3. Location Test:        {'✅ PASS' if results['location'] else '❌ FAIL'}")
    print(f"  4. Fallback Test:        {'✅ PASS' if results['fallback'] else '❌ FAIL'}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print("\n" + "="*80 + "\n")
    
    if passed == total:
        print("🎉 All tests PASSED!")
    else:
        print("⚠️  Some tests FAILED - review output above")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
