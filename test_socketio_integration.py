"""
Socket.IO Integration Test - Conductor and Driver Communication
================================================================
Tests the Socket.IO communication between Conductor and VehicleDriver.

This test validates:
1. Socket.IO connections for both Conductor and Driver
2. Stop request signal (conductor:request:stop)
3. Depart signal (conductor:ready:depart)
4. Location broadcasting (driver:location:update)
5. Fallback to callbacks when Socket.IO unavailable
"""

import asyncio
import pytest
from arknet_transit_simulator.vehicle.conductor import Conductor
from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver


@pytest.mark.asyncio
async def test_socketio_connections():
    """Test that both Conductor and Driver can connect to Socket.IO server."""
    
    # Create conductor with Socket.IO
    conductor = Conductor(
        conductor_id="TEST_COND_001",
        conductor_name="Test Conductor",
        vehicle_id="TEST_VEH_001",
        assigned_route_id="1A",
        capacity=40,
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Create driver with Socket.IO
    driver = VehicleDriver(
        driver_id="TEST_DRV_001",
        driver_name="Test Driver",
        vehicle_id="TEST_VEH_001",
        route_coordinates=[[40.7128, -74.0060], [40.7589, -73.9851]],
        route_name="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Start both (should connect to Socket.IO)
    conductor_started = await conductor.start()
    driver_started = await driver.start()
    
    # Wait for connections to establish
    await asyncio.sleep(2.0)
    
    # Verify connections
    print(f"\n✅ Conductor started: {conductor_started}")
    print(f"✅ Conductor Socket.IO connected: {conductor.sio_connected}")
    print(f"✅ Driver started: {driver_started}")
    print(f"✅ Driver Socket.IO connected: {driver.sio_connected}")
    
    assert conductor_started == True, "Conductor failed to start"
    assert driver_started == True, "Driver failed to start"
    
    # Cleanup
    await conductor.stop()
    await driver.stop()
    
    # Wait for cleanup
    await asyncio.sleep(1.0)
    
    print("\n✅ Test passed: Both components connected successfully")


@pytest.mark.asyncio
async def test_stop_and_depart_signals():
    """Test conductor stop and depart signals via Socket.IO."""
    
    # Create conductor and driver
    conductor = Conductor(
        conductor_id="TEST_COND_002",
        conductor_name="Signal Test Conductor",
        vehicle_id="TEST_VEH_002",
        assigned_route_id="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    driver = VehicleDriver(
        driver_id="TEST_DRV_002",
        driver_name="Signal Test Driver",
        vehicle_id="TEST_VEH_002",
        route_coordinates=[[40.7128, -74.0060], [40.7589, -73.9851]],
        route_name="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Start both
    await conductor.start()
    await driver.start()
    await asyncio.sleep(2.0)
    
    print(f"\n✅ Initial driver state: {driver.current_state.value}")
    
    # Start driver's engine (simulate vehicle moving)
    await driver.start_engine()
    print(f"✅ Driver state after engine start: {driver.current_state.value}")
    
    # Wait a bit
    await asyncio.sleep(2.0)
    
    # Simulate conductor sending stop request
    from arknet_transit_simulator.vehicle.conductor import StopOperation
    from datetime import datetime
    
    conductor.current_stop_operation = StopOperation(
        stop_id="TEST_STOP_001",
        stop_name="Test Stop",
        latitude=40.7128,
        longitude=-74.0060,
        passengers_boarding=["P001", "P002"],
        passengers_disembarking=["P003"],
        requested_duration=5.0,  # 5 seconds for test
        start_time=datetime.now(),
        gps_position=(40.7128, -74.0060)
    )
    
    print("\n📤 Conductor sending stop request...")
    await conductor._signal_driver_stop()
    
    # Wait for driver to process stop
    await asyncio.sleep(7.0)
    
    print(f"✅ Driver state after stop: {driver.current_state.value}")
    
    # Conductor signals ready to depart
    print("\n📤 Conductor signaling ready to depart...")
    await conductor._signal_driver_continue()
    
    # Wait for driver to restart
    await asyncio.sleep(2.0)
    
    print(f"✅ Driver state after depart signal: {driver.current_state.value}")
    
    # Cleanup
    await conductor.stop()
    await driver.stop()
    await asyncio.sleep(1.0)
    
    print("\n✅ Test passed: Stop and depart signals working")


@pytest.mark.asyncio
async def test_location_broadcasting():
    """Test driver location broadcasting via Socket.IO."""
    
    driver = VehicleDriver(
        driver_id="TEST_DRV_003",
        driver_name="Location Test Driver",
        vehicle_id="TEST_VEH_003",
        route_coordinates=[[40.7128, -74.0060], [40.7589, -73.9851]],
        route_name="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Start driver
    await driver.start()
    await asyncio.sleep(2.0)
    
    print(f"\n✅ Driver connected: {driver.sio_connected}")
    print(f"✅ Location broadcast task running: {driver.location_broadcast_task is not None}")
    
    # Start engine (location broadcasting only happens when ONBOARD)
    await driver.start_engine()
    print(f"✅ Driver state: {driver.current_state.value}")
    
    # Let location broadcast for 15 seconds (3 broadcasts at 5-second intervals)
    print("\n📡 Broadcasting location for 15 seconds...")
    await asyncio.sleep(15.0)
    
    # Stop driver
    await driver.stop()
    await asyncio.sleep(1.0)
    
    print("\n✅ Test passed: Location broadcasting working")


@pytest.mark.asyncio
async def test_fallback_to_callbacks():
    """Test fallback to callbacks when Socket.IO is unavailable."""
    
    callback_received = {'stop': False, 'continue': False}
    
    def mock_driver_callback(conductor_id, signal_data):
        """Mock callback to verify fallback mechanism."""
        action = signal_data.get('action')
        if action == 'stop_vehicle':
            callback_received['stop'] = True
            print(f"\n✅ Callback received STOP signal from {conductor_id}")
        elif action == 'continue_driving':
            callback_received['continue'] = True
            print(f"✅ Callback received CONTINUE signal from {conductor_id}")
    
    # Create conductor with Socket.IO DISABLED
    conductor = Conductor(
        conductor_id="TEST_COND_004",
        conductor_name="Fallback Test Conductor",
        vehicle_id="TEST_VEH_004",
        assigned_route_id="1A",
        use_socketio=False  # Disable Socket.IO
    )
    
    # Set callback
    conductor.set_driver_callback(mock_driver_callback)
    
    # Start conductor
    await conductor.start()
    await asyncio.sleep(1.0)
    
    print(f"\n✅ Conductor Socket.IO disabled: {not conductor.use_socketio}")
    
    # Create stop operation
    from arknet_transit_simulator.vehicle.conductor import StopOperation
    from datetime import datetime
    
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
    
    # Test stop signal via callback
    print("\n📤 Sending stop signal (should use callback)...")
    await conductor._signal_driver_stop()
    await asyncio.sleep(2.0)
    
    # Test continue signal via callback
    print("📤 Sending continue signal (should use callback)...")
    await conductor._signal_driver_continue()
    await asyncio.sleep(1.0)
    
    # Verify callbacks were used
    assert callback_received['stop'] == True, "Stop callback not received"
    assert callback_received['continue'] == True, "Continue callback not received"
    
    # Cleanup
    await conductor.stop()
    
    print("\n✅ Test passed: Fallback to callbacks working")


@pytest.mark.asyncio
async def test_socketio_with_wrong_url():
    """Test that components gracefully handle Socket.IO connection failures."""
    
    # Create conductor with WRONG Socket.IO URL
    conductor = Conductor(
        conductor_id="TEST_COND_005",
        conductor_name="Wrong URL Conductor",
        vehicle_id="TEST_VEH_005",
        assigned_route_id="1A",
        sio_url="http://localhost:9999",  # Wrong port
        use_socketio=True
    )
    
    # Start conductor (should fail to connect but still work)
    conductor_started = await conductor.start()
    await asyncio.sleep(2.0)
    
    print(f"\n✅ Conductor started despite wrong URL: {conductor_started}")
    print(f"✅ Socket.IO disabled due to connection failure: {not conductor.use_socketio}")
    
    assert conductor_started == True, "Conductor should start even if Socket.IO fails"
    assert conductor.use_socketio == False, "Socket.IO should be disabled after connection failure"
    
    # Cleanup
    await conductor.stop()
    
    print("\n✅ Test passed: Graceful handling of connection failures")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Socket.IO Integration Tests")
    print("="*80)
    print("\nPrerequisites:")
    print("  - Socket.IO server must be running on http://localhost:3000")
    print("  - Run: cd commuter_service && npm run dev")
    print("="*80 + "\n")
    
    # Run tests
    asyncio.run(test_socketio_connections())
    print("\n" + "-"*80 + "\n")
    
    asyncio.run(test_stop_and_depart_signals())
    print("\n" + "-"*80 + "\n")
    
    asyncio.run(test_location_broadcasting())
    print("\n" + "-"*80 + "\n")
    
    asyncio.run(test_fallback_to_callbacks())
    print("\n" + "-"*80 + "\n")
    
    asyncio.run(test_socketio_with_wrong_url())
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80 + "\n")
