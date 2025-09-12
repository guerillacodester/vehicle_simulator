#!/usr/bin/env python3
"""
Simple GPS Packet Injection Test
--------------------------------
Quick test to inject a single telemetry packet to a GPS device.
"""

import sys
import time
import logging
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def inject_test_packet_to_vehicle(vehicle_id=None):
    """
    Inject a test packet to a specific vehicle or the first available vehicle.
    
    Args:
        vehicle_id: Specific vehicle ID, or None to use first available
    """
    try:
        # Import what we need
        from world.vehicle_simulator.core.depot_manager import DepotManager
        
        print("🚌 Creating depot manager...")
        depot = DepotManager(tick_time=1.0, enable_timetable=True)
        
        print("🔌 Starting depot...")
        depot.start()
        
        # Wait for initialization
        print("⏳ Waiting for vehicles to initialize...")
        time.sleep(3)
        
        if not depot.vehicles:
            print("❌ No vehicles found in depot")
            depot.stop()
            return False
        
        # Select vehicle
        if vehicle_id and vehicle_id in depot.vehicles:
            target_vehicle_id = vehicle_id
        else:
            target_vehicle_id = list(depot.vehicles.keys())[0]
            
        vehicle_handler = depot.vehicles[target_vehicle_id]
        gps_device = vehicle_handler['_gps']
        
        print(f"✅ Selected vehicle: {target_vehicle_id}")
        print(f"🛰️ GPS Device ID: {gps_device.device_id}")
        print(f"📡 GPS Device Active: {hasattr(gps_device, 'thread') and gps_device.thread is not None}")
        
        # Create test telemetry packet
        test_location = {
            "lat": 13.2810,   # Bridgetown, Barbados (realistic location)
            "lon": -59.6463,
            "speed": 42.5,    # Reasonable speed for ZR van
            "heading": 135.0, # Southeast direction
        }
        
        test_packet = {
            "device_id": target_vehicle_id,
            "lat": test_location["lat"],
            "lon": test_location["lon"],
            "speed": test_location["speed"],
            "heading": test_location["heading"],
            "route": "ROUTE_1",  # Route 1 (common Barbados route)
            "vehicle_reg": f"ZR-{target_vehicle_id[:8].upper()}",
            "driver_id": "test-driver-001",
            "driver_name": {"first": "Test", "last": "Driver"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"\n📡 INJECTING TEST PACKET:")
        print(f"   📍 Location: {test_packet['lat']:.6f}, {test_packet['lon']:.6f}")
        print(f"   🚗 Speed: {test_packet['speed']} km/h")
        print(f"   🧭 Heading: {test_packet['heading']}°")
        print(f"   🛣️ Route: {test_packet['route']}")
        print(f"   🚌 Vehicle: {test_packet['vehicle_reg']}")
        print(f"   👨‍✈️ Driver: {test_packet['driver_name']['first']} {test_packet['driver_name']['last']}")
        print(f"   ⏰ Time: {test_packet['timestamp']}")
        
        # Inject packet directly into GPS device buffer
        gps_device.rxtx_buffer.write(test_packet)
        print(f"\n✅ Test packet injected into GPS buffer for {target_vehicle_id}!")
        print("📤 Packet should be transmitted to WebSocket server...")
        
        # Wait a bit to allow transmission
        print("⏳ Waiting for transmission...")
        time.sleep(5)
        
        # Check buffer status
        try:
            buffer_size = gps_device.rxtx_buffer.queue.qsize()
            print(f"📊 Buffer status: {buffer_size} packets remaining")
        except:
            print("📊 Buffer status: Unknown")
        
        print("\n🛑 Stopping depot...")
        depot.stop()
        
        print("✅ Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🧪 GPS PACKET INJECTION TEST")
    print("=" * 40)
    print("This script injects a single test telemetry packet")
    print("into a GPS device from the depot.\n")
    
    # Get vehicle ID from command line if provided
    vehicle_id = None
    if len(sys.argv) > 1:
        vehicle_id = sys.argv[1]
        print(f"🎯 Target vehicle: {vehicle_id}")
    else:
        print("🎯 Target vehicle: First available")
    
    print()
    success = inject_test_packet_to_vehicle(vehicle_id)
    
    if success:
        print("\n🎉 GPS packet injection test PASSED!")
        print("📡 Check your WebSocket server logs for the transmitted packet.")
    else:
        print("\n❌ GPS packet injection test FAILED!")
        print("🔍 Check the error messages above for details.")

if __name__ == "__main__":
    main()