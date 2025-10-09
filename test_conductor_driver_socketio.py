"""
Direct Conductor-Driver Socket.IO Test
======================================
Test the full communication flow: stop signals and depart signals.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arknet_transit_simulator.vehicle.conductor import Conductor
from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver


async def main():
    print("\n" + "="*80)
    print("CONDUCTOR ↔ DRIVER SOCKET.IO COMMUNICATION TEST")
    print("="*80 + "\n")
    
    # Create conductor
    print("1️⃣  Creating Conductor...")
    conductor = Conductor(
        conductor_id="TEST_COND",
        conductor_name="Test Conductor",
        vehicle_id="TEST_VEH",
        assigned_route_id="1A",
        capacity=40,
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Create driver
    print("2️⃣  Creating Driver...")
    driver = VehicleDriver(
        driver_id="TEST_DRV",
        driver_name="Test Driver",
        vehicle_id="TEST_VEH",
        route_coordinates=[
            [40.7128, -74.0060],  # Start
            [40.7589, -73.9851],  # Mid
            [40.7800, -73.9700]   # End
        ],
        route_name="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Start conductor
    print("\n3️⃣  Starting Conductor...")
    await conductor.start()
    print(f"   ✅ Conductor Socket.IO connected: {conductor.sio_connected}")
    
    # Start driver
    print("\n4️⃣  Starting Driver...")
    await driver.start()
    print(f"   ✅ Driver Socket.IO connected: {driver.sio_connected}")
    print(f"   📍 Driver state: {driver.current_state.value}")
    
    # Wait for stable connections
    print("\n⏳ Waiting for connections to stabilize (2 seconds)...")
    await asyncio.sleep(2.0)
    
    # Check location broadcasting
    print("\n5️⃣  Testing Location Broadcasting...")
    print("   (Check server console for 'driver:location:update' events)")
    await asyncio.sleep(6.0)  # Should see 1-2 location broadcasts
    
    # Test stop signal
    print("\n6️⃣  Testing STOP Signal...")
    print(f"   📊 Driver state BEFORE: {driver.current_state.value}")
    
    print("   📤 Conductor creating stop operation and sending STOP signal...")
    # Create a stop operation (this is what happens during normal operation)
    from arknet_transit_simulator.vehicle.conductor import StopOperation
    conductor.current_stop_operation = StopOperation(
        stop_id="TEST_STOP_001",
        latitude=40.7589,
        longitude=-73.9851,
        requested_duration=5.0,
        passengers_boarding=[],
        passengers_disembarking=[]
    )
    
    await conductor._signal_driver_stop()
    
    await asyncio.sleep(1.0)
    print(f"   📊 Driver state AFTER stop: {driver.current_state.value}")
    print("   ⏳ Waiting 5 seconds (stop duration)...")
    await asyncio.sleep(5.0)
    
    # Test depart signal
    print("\n7️⃣  Testing DEPART Signal...")
    print(f"   📊 Driver state BEFORE: {driver.current_state.value}")
    
    print("   📤 Conductor sending DEPART signal via Socket.IO...")
    await conductor._signal_driver_continue()
    
    await asyncio.sleep(1.0)
    print(f"   📊 Driver state AFTER depart: {driver.current_state.value}")
    
    # Verify location broadcasting resumed
    print("\n8️⃣  Verifying Location Broadcasting Resumed...")
    await asyncio.sleep(6.0)
    
    # Cleanup
    print("\n9️⃣  Cleaning up...")
    await conductor.stop()
    await driver.stop()
    await asyncio.sleep(1.0)
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE!")
    print("="*80 + "\n")
    
    print("Check the Socket.IO server console to verify:")
    print("  ✅ 'driver:location:update' events received")
    print("  ✅ 'conductor:request:stop' event received")
    print("  ✅ 'conductor:ready:depart' event received")
    print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
