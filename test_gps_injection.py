#!/usr/bin/env python3
"""
GPS Telemetry Test Injection Script
-----------------------------------
Send test telemetry packets to GPS devices in the running depot system.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_method_1_direct_buffer_write():
    """Method 1: Direct buffer write to a running depot vehicle"""
    print("🧪 METHOD 1: Direct Buffer Write")
    print("=" * 50)
    
    try:
        # Import DepotManager to access running vehicles
        from world.vehicle_simulator.core.depot_manager import DepotManager
        
        # Create depot instance
        depot = DepotManager(tick_time=1.0, enable_timetable=True)
        depot.start()
        
        # Wait a moment for vehicles to initialize
        time.sleep(2)
        
        if not depot.vehicles:
            print("❌ No vehicles found in depot")
            return False
            
        # Get first vehicle
        vehicle_id = list(depot.vehicles.keys())[0]
        vehicle_handler = depot.vehicles[vehicle_id]
        gps_device = vehicle_handler['_gps']
        
        print(f"✅ Found vehicle: {vehicle_id}")
        print(f"🛰️ GPS Device: {gps_device.device_id}")
        
        # Create test telemetry packet
        test_packet = {
            "device_id": vehicle_id,
            "lat": 13.2810,  # Bridgetown, Barbados
            "lon": -59.6463,
            "speed": 25.5,
            "heading": 45.0,
            "route": "TEST_ROUTE_001",
            "vehicle_reg": f"TEST-{vehicle_id[:8]}",
            "driver_id": "test-driver",
            "driver_name": {"first": "Test", "last": "Driver"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"📡 Injecting test packet:")
        print(f"   📍 Location: {test_packet['lat']:.4f}, {test_packet['lon']:.4f}")
        print(f"   🚗 Speed: {test_packet['speed']} km/h")
        print(f"   🧭 Heading: {test_packet['heading']}°")
        
        # Write directly to GPS device buffer
        gps_device.rxtx_buffer.write(test_packet)
        print("✅ Test packet written to GPS buffer!")
        
        # Wait to allow transmission
        time.sleep(3)
        
        depot.stop()
        return True
        
    except Exception as e:
        logger.error(f"❌ Method 1 failed: {e}")
        return False

def test_method_2_simulation_plugin():
    """Method 2: Using the simulation plugin interface"""
    print("\n🧪 METHOD 2: Simulation Plugin Interface")
    print("=" * 50)
    
    try:
        from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
        from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
        from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
        
        # Create GPS device
        device_id = "TEST_VEHICLE_001"
        codec = PacketCodec()
        transmitter = WebSocketTransmitter(
            server_url="ws://localhost:8001",
            token="test_token",
            device_id=device_id,
            codec=codec
        )
        
        # Plugin configuration for simulation
        plugin_config = {
            "plugin": "simulation",
            "update_interval": 1.0,
            "device_id": device_id
        }
        
        gps_device = GPSDevice(
            device_id=device_id,
            ws_transmitter=transmitter,
            plugin_config=plugin_config
        )
        
        print(f"✅ Created GPS device: {device_id}")
        
        # Turn on GPS device
        gps_device.on()
        print("🛰️ GPS device activated")
        
        # Create test packet
        test_packet = {
            "device_id": device_id,
            "lat": 13.2820,  # Slightly different location
            "lon": -59.6470,
            "speed": 35.0,
            "heading": 90.0,
            "route": "TEST_ROUTE_002",
            "vehicle_reg": "TEST-002",
            "driver_id": "test-driver-2",
            "driver_name": {"first": "Test", "last": "Driver2"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"📡 Injecting test packet:")
        print(f"   📍 Location: {test_packet['lat']:.4f}, {test_packet['lon']:.4f}")
        print(f"   🚗 Speed: {test_packet['speed']} km/h")
        
        # Inject packet
        gps_device.rxtx_buffer.write(test_packet)
        print("✅ Test packet injected via simulation plugin!")
        
        # Wait for transmission
        time.sleep(5)
        
        # Turn off GPS device
        gps_device.off()
        print("🛑 GPS device stopped")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Method 2 failed: {e}")
        return False

def test_method_3_multiple_packets():
    """Method 3: Send multiple test packets simulating vehicle movement"""
    print("\n🧪 METHOD 3: Multiple Packet Simulation")
    print("=" * 50)
    
    try:
        from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
        from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
        from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
        
        # Create GPS device
        device_id = "TEST_MOBILE_001"
        codec = PacketCodec()
        transmitter = WebSocketTransmitter(
            server_url="ws://localhost:8001",
            token="test_token",
            device_id=device_id,
            codec=codec
        )
        
        plugin_config = {
            "plugin": "simulation",
            "update_interval": 0.5,  # Faster updates
            "device_id": device_id
        }
        
        gps_device = GPSDevice(
            device_id=device_id,
            ws_transmitter=transmitter,
            plugin_config=plugin_config
        )
        
        print(f"✅ Created mobile GPS device: {device_id}")
        gps_device.on()
        
        # Simulate vehicle movement along a route
        route_points = [
            (13.2810, -59.6463, 20.0, 0.0),    # Starting point
            (13.2815, -59.6460, 25.0, 45.0),   # Moving northeast
            (13.2820, -59.6455, 30.0, 90.0),   # Moving east
            (13.2825, -59.6450, 35.0, 135.0),  # Moving southeast
            (13.2830, -59.6445, 40.0, 180.0),  # Moving south
        ]
        
        print(f"🛣️ Simulating movement along {len(route_points)} points...")
        
        for i, (lat, lon, speed, heading) in enumerate(route_points):
            test_packet = {
                "device_id": device_id,
                "lat": lat,
                "lon": lon,
                "speed": speed,
                "heading": heading,
                "route": "TEST_ROUTE_MOBILE",
                "vehicle_reg": "MOBILE-001",
                "driver_id": "mobile-driver",
                "driver_name": {"first": "Mobile", "last": "Driver"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            print(f"   📍 Point {i+1}: {lat:.4f}, {lon:.4f} | Speed: {speed} km/h | Heading: {heading}°")
            
            # Inject packet
            gps_device.rxtx_buffer.write(test_packet)
            
            # Wait between packets
            time.sleep(2)
        
        print("✅ Mobile simulation complete!")
        
        # Wait for final transmission
        time.sleep(3)
        gps_device.off()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Method 3 failed: {e}")
        return False

def main():
    """Run all test methods"""
    print("🚀 GPS TELEMETRY INJECTION TEST SUITE")
    print("=" * 60)
    print("This script tests different ways to inject telemetry data")
    print("into GPS devices for transmission to the Fleet Manager.\n")
    
    results = []
    
    # Test Method 1: Direct buffer write to depot vehicle
    results.append(("Direct Buffer Write", test_method_1_direct_buffer_write()))
    
    # Test Method 2: Simulation plugin interface
    results.append(("Simulation Plugin", test_method_2_simulation_plugin()))
    
    # Test Method 3: Multiple packet simulation
    results.append(("Multiple Packets", test_method_3_multiple_packets()))
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    for method, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{method:<20} {status}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("🎉 All GPS injection methods working!")
    else:
        print("⚠️ Some methods failed - check logs for details")

if __name__ == "__main__":
    main()