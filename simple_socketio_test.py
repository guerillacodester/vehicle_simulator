"""
Simple Socket.IO Connection Test
=================================
Just tests if Conductor and Driver can connect to Socket.IO server.
No user input required.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arknet_transit_simulator.vehicle.conductor import Conductor
from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver


async def main():
    print("\n" + "="*80)
    print("SIMPLE SOCKET.IO CONNECTION TEST")
    print("="*80 + "\n")
    
    print("Creating Conductor...")
    conductor = Conductor(
        conductor_id="SIMPLE_TEST_COND",
        conductor_name="Simple Test Conductor",
        vehicle_id="SIMPLE_TEST_VEH",
        assigned_route_id="1A",
        capacity=40,
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    print("Creating Driver...")
    driver = VehicleDriver(
        driver_id="SIMPLE_TEST_DRV",
        driver_name="Simple Test Driver",
        vehicle_id="SIMPLE_TEST_VEH",
        route_coordinates=[[40.7128, -74.0060], [40.7589, -73.9851]],
        route_name="1A",
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    print("\nStarting Conductor...")
    await conductor.start()
    
    print("Starting Driver...")
    await driver.start()
    
    print("\nWaiting for connections (3 seconds)...")
    await asyncio.sleep(3.0)
    
    print("\n" + "="*80)
    print("CONNECTION STATUS")
    print("="*80)
    print(f"\nConductor Socket.IO connected: {conductor.sio_connected}")
    print(f"Driver Socket.IO connected: {driver.sio_connected}")
    print(f"Driver state: {driver.current_state.value}")
    
    if conductor.sio_connected and driver.sio_connected:
        print("\n✅ SUCCESS: Both components connected to Socket.IO!")
        
        # Test location broadcasting
        print("\nStarting engine for location broadcast test...")
        await driver.start_engine()
        print(f"Driver state: {driver.current_state.value}")
        
        print("\nBroadcasting location for 10 seconds...")
        print("(Check Socket.IO server console for location updates)")
        await asyncio.sleep(10.0)
        
    else:
        print("\n❌ FAILED: Socket.IO connections not established")
        print("Make sure Socket.IO server is running: python test_socketio_server.py")
    
    print("\nCleaning up...")
    await conductor.stop()
    await driver.stop()
    await asyncio.sleep(1.0)
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
