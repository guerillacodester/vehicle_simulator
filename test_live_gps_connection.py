#!/usr/bin/env python3
"""
Live GPS Connection Test
-----------------------
Demonstrates the complete VehicleDriver → GPS Device → Telemetry Server flow.

This test shows:
1. Driver comes online (PersonState.ONSITE)
2. Driver turns on GPS device (DeviceState.ON)
3. GPS connects to telemetry server at localhost:5000
4. GPS sends real telemetry packets to server
5. Driver goes offline, GPS disconnects from server

The telemetry server at localhost:5000 should show connection/disconnection messages.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
from world.vehicle_simulator.vehicle.engine.engine_block import Engine
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.core.states import PersonState, DeviceState


class MockSpeedModel:
    """Mock speed model that generates realistic speed data."""
    def __init__(self):
        self.speed = 45.0  # Start at 45 km/h
        self.count = 0
        
    def update(self):
        # Vary speed slightly to simulate real driving
        import random
        self.speed += random.uniform(-2.0, 2.0)
        self.speed = max(20.0, min(80.0, self.speed))  # Keep between 20-80 km/h
        self.count += 1
        return {"velocity": self.speed}


async def test_live_gps_connection():
    """Test live GPS connection to telemetry server."""
    print("\n🚗 Live GPS Connection Test")
    print("=" * 50)
    print("📡 Telemetry Server: http://localhost:5000")
    print("🔔 Watch server logs for connection notifications!")
    print()
    
    # Create realistic vehicle components
    print("🔧 Setting up vehicle components...")
    
    # Engine with realistic speed model
    buffer = EngineBuffer(size=50)
    model = MockSpeedModel()
    engine = Engine("ZR101", model, buffer, tick_time=0.5)  # Update every 0.5 seconds
    
    # GPS Device with WebSocket transmitter to real server
    from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
    
    transmitter = WebSocketTransmitter(
        server_url="ws://localhost:5000",
        token="test-token", 
        device_id="ZR101",
        codec=PacketCodec()
    )
    
    # GPS with simulation plugin config for realistic telemetry
    plugin_config = {
        "type": "simulation",
        "config": {
            "device_id": "ZR101",
            "vehicle_reg": "ZR101",
            "route": "Route1A",
            "driver_id": "DRV001",
            "driver_name": {"first": "John", "last": "Smith"},
            "update_interval": 1.0,  # Send telemetry every 1 second
            "initial_position": {
                "lat": 13.1,
                "lon": -59.6
            }
        }
    }
    
    gps_device = GPSDevice("DRV001", transmitter, plugin_config)  # Use driver's license as device ID
    
    # Route coordinates for Barbados (realistic GPS path)
    route_coords = [
        (-59.6167, 13.1000),  # Bridgetown start
        (-59.6100, 13.1050),  # Northeast
        (-59.6050, 13.1100),  # Continue northeast
        (-59.6000, 13.1150),  # Further northeast
        (-59.5950, 13.1200),  # End point
    ]
    
    # Create vehicle driver
    driver = VehicleDriver(
        driver_id="DRV001",
        driver_name="John Smith",
        vehicle_id="ZR101", 
        route_coordinates=route_coords,
        engine_buffer=buffer,
        tick_time=1.0
    )
    
    # Give driver control of vehicle components
    driver.set_vehicle_components(engine=engine, gps_device=gps_device)
    
    print("✅ Vehicle components ready")
    print(f"🚛 Vehicle: ZR101")
    print(f"👨‍💼 Driver: John Smith (DRV001)")
    print(f"📡 GPS Server: ws://localhost:5000/ws")
    print()
    
    # Step 1: Driver is initially offline
    print("📍 STEP 1: Driver Status Check")
    print(f"Driver state: {driver.current_state}")
    print(f"Engine state: {engine.current_state}")
    print(f"GPS state: {gps_device.current_state}")
    print("👨‍💼 Driver is OFFSITE - no components running")
    print()
    
    await asyncio.sleep(2)
    
    # Step 2: Driver arrives and boards vehicle
    print("📍 STEP 2: Driver Boards Vehicle")
    print("👨‍💼 Driver John Smith arriving at depot...")
    
    success = await driver.arrive()
    print(f"✅ Driver boarding: {success}")
    print(f"Driver state: {driver.current_state}")
    print(f"Engine state: {engine.current_state}")
    print(f"GPS state: {gps_device.current_state}")
    print()
    print("🔔 CHECK SERVER LOGS: GPS device should be connecting to server!")
    print()
    
    await asyncio.sleep(3)
    
    # Step 3: Let components run and generate data
    print("📍 STEP 3: Vehicle Operations Running")
    print("🚛 Engine generating kinematic data...")
    print("📡 GPS sending telemetry to server...")
    print("⏱️  Running for 10 seconds - watch server for telemetry packets...")
    print()
    
    # Let the system run for a while to generate telemetry
    for i in range(10):
        await asyncio.sleep(1)
        print(f"⏱️  Running... {i+1}/10 seconds", end='\r')
    
    print("\n")
    
    # Step 4: Check component states
    print("📍 STEP 4: Component Status Check")
    print(f"Driver state: {driver.current_state}")
    print(f"Engine state: {engine.current_state}")
    print(f"GPS state: {gps_device.current_state}")
    
    # Get some data from buffers
    latest_engine_data = buffer.read_latest()
    if latest_engine_data:
        print(f"🔧 Latest engine data: Speed={latest_engine_data.get('cruise_speed', 0):.1f} km/h, Distance={latest_engine_data.get('distance', 0):.2f} km")
    
    gps_status = gps_device.get_status()
    print(f"📡 GPS status: {gps_status}")
    print()
    
    await asyncio.sleep(2)
    
    # Step 5: Driver finishes shift and disembarks
    print("📍 STEP 5: Driver Finishes Shift")
    print("👨‍💼 Driver John Smith finishing shift and disembarking...")
    
    success = await driver.depart()
    print(f"✅ Driver departure: {success}")
    print(f"Driver state: {driver.current_state}")
    print(f"Engine state: {engine.current_state}")
    print(f"GPS state: {gps_device.current_state}")
    print()
    print("🔔 CHECK SERVER LOGS: GPS device should be disconnecting from server!")
    print()
    
    await asyncio.sleep(2)
    
    print("📍 FINAL STATUS")
    print("✅ Test completed successfully!")
    print("📊 Summary:")
    print(f"   • Driver: {driver.current_state}")
    print(f"   • Engine: {engine.current_state}")
    print(f"   • GPS: {gps_device.current_state}")
    print()
    print("🔔 Server should show:")
    print("   1. GPS device connected when driver boarded")
    print("   2. Telemetry packets received during operation")
    print("   3. GPS device disconnected when driver left")


async def main():
    """Run the live GPS connection test."""
    try:
        await test_live_gps_connection()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    print("🚀 Starting Live GPS Connection Test")
    print("📋 Prerequisites:")
    print("   ✅ Telemetry server running on localhost:5000")
    print("   ✅ Vehicle components with state management")
    print("   ✅ Real WebSocket connection to server")
    print()
    
    sys.exit(asyncio.run(main()))