#!/usr/bin/env python3
"""
Direct GPS Device Test
---------------------
Create a single GPS device and send a test packet directly.
"""

import time
import logging
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def create_and_test_gps_device():
    """Create a standalone GPS device and send a test packet"""
    try:
        # Import required components
        from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
        from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
        from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
        
        print("🛰️ Creating GPS device...")
        
        # Device configuration
        device_id = "TEST_GPS_001"
        websocket_url = "ws://localhost:5000"  # GPS telemetry server (not Fleet Manager)
        auth_token = "supersecrettoken"  # Use config.ini auth token
        
        # Create transmitter components
        codec = PacketCodec()
        transmitter = WebSocketTransmitter(
            server_url=websocket_url,
            token=auth_token,
            device_id=device_id,
            codec=codec
        )
        
        # Create plugin configuration for simulation
        plugin_config = {
            "plugin": "simulation",
            "update_interval": 1.0,
            "device_id": device_id
        }
        
        # Create GPS device
        gps_device = GPSDevice(
            device_id=device_id,
            ws_transmitter=transmitter,
            plugin_config=plugin_config
        )
        
        print(f"✅ GPS device created: {device_id}")
        print(f"🔗 WebSocket URL: {websocket_url}")
        
        # Turn on GPS device
        print("🔌 Starting GPS device...")
        gps_device.on()
        
        # Wait for device to initialize
        time.sleep(2)
        print("✅ GPS device started")
        
        # Create test packet with realistic Barbados data
        test_packet = {
            "device_id": device_id,
            "lat": 13.2810,      # Bridgetown, Barbados
            "lon": -59.6463,     # 
            "speed": 35.0,       # 35 km/h (typical for ZR van)
            "heading": 180.0,    # Heading south
            "route": "ROUTE_1",  # Route 1 
            "vehicle_reg": "ZR-TEST-001",
            "driver_id": "driver-test-001",
            "driver_name": {"first": "Test", "last": "Driver"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"\n📡 SENDING TEST PACKET:")
        print(f"   🆔 Device: {test_packet['device_id']}")
        print(f"   📍 Location: {test_packet['lat']:.6f}, {test_packet['lon']:.6f}")
        print(f"   🚗 Speed: {test_packet['speed']} km/h")
        print(f"   🧭 Heading: {test_packet['heading']}°")
        print(f"   🛣️ Route: {test_packet['route']}")
        print(f"   🚌 Vehicle: {test_packet['vehicle_reg']}")
        print(f"   ⏰ Time: {test_packet['timestamp']}")
        
        # Inject test packet into GPS buffer
        gps_device.rxtx_buffer.write(test_packet)
        print(f"\n✅ Test packet written to GPS buffer!")
        
        # Wait for transmission
        print("📤 Waiting for packet transmission...")
        time.sleep(5)
        
        # Check buffer status
        try:
            buffer_size = gps_device.rxtx_buffer.queue.qsize()
            print(f"📊 Remaining in buffer: {buffer_size} packets")
        except Exception as e:
            print(f"📊 Buffer status check failed: {e}")
        
        # Turn off GPS device
        print("🛑 Stopping GPS device...")
        gps_device.off()
        
        print("✅ Direct GPS test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct GPS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🔬 DIRECT GPS DEVICE TEST")
    print("=" * 40)
    print("This script creates a standalone GPS device")
    print("and sends a single test packet.\n")
    
    success = create_and_test_gps_device()
    
    if success:
        print("\n🎉 Direct GPS test PASSED!")
        print("📡 The test packet was sent to the WebSocket server.")
        print("🔍 Check your telemetry server logs to confirm receipt.")
    else:
        print("\n❌ Direct GPS test FAILED!")
        print("🔧 Check the error messages above and ensure:")
        print("   - WebSocket server is running on ws://localhost:8001")
        print("   - No firewall blocking the connection")
        print("   - All required modules are installed")

if __name__ == "__main__":
    main()