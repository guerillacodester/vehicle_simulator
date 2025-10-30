#!/usr/bin/env python3
"""
Test GPS Device Reconnection Behavior

This script demonstrates that GPS devices automatically reconnect
to the GPSCentCom server when the connection is lost and restored.

Usage:
    1. Start this script (GPS server doesn't need to be running)
    2. The GPS device will try to connect and retry when unavailable
    3. Start the GPS server: python gpscentcom_server/server_main.py
    4. Watch the device connect automatically
    5. Stop the GPS server
    6. Watch the device detect disconnection and retry
    7. Restart the GPS server
    8. Watch the device reconnect automatically

Expected Behavior:
    - Device continues operating even when server is down
    - Device automatically reconnects when server becomes available
    - No data loss up to buffer capacity (1000 items)
    - Suitable for real hardware deployment with network interruptions
"""

import asyncio
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from arknet_transit_simulator.vehicle.gps_device.device import GPSDevice
from arknet_transit_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from arknet_transit_simulator.vehicle.gps_device.radio_module.packet import PacketCodec


def test_reconnection():
    """Test GPS device reconnection behavior."""
    
    print("=" * 70)
    print("GPS Device Reconnection Test")
    print("=" * 70)
    print()
    print("This test demonstrates automatic reconnection when GPS server")
    print("goes down and comes back up.")
    print()
    print("Instructions:")
    print("  1. This script will start a GPS device")
    print("  2. If GPS server is not running, it will keep retrying")
    print("  3. Start GPS server: python gpscentcom_server/server_main.py")
    print("  4. Watch device connect automatically")
    print("  5. Stop GPS server and watch device detect disconnection")
    print("  6. Restart GPS server and watch device reconnect")
    print()
    print("Press Ctrl+C to stop the test")
    print("=" * 70)
    print()
    
    # Create GPS device with simulation plugin
    device_id = "TEST-GPS-001"
    server_url = "ws://localhost:5000"
    token = "test-token"
    
    # Create transmitter
    transmitter = WebSocketTransmitter(
        server_url=server_url,
        token=token,
        device_id=device_id,
        codec=PacketCodec()
    )
    
    # Create GPS device with simulation plugin
    gps_device = GPSDevice(
        device_id=device_id,
        ws_transmitter=transmitter,
        plugin_config={
            "plugin": "simulation",
            "update_interval": 2.0,
            "device_id": device_id
        }
    )
    
    # Create some fake vehicle state for simulation
    class FakeVehicleState:
        def __init__(self):
            self.lat = 35.0844
            self.lon = -106.6504
            self.speed = 45.0
            self.heading = 90.0
            self.route = "TEST-ROUTE"
            self.vehicle_id = "TEST-VEHICLE"
            self.driver_id = "TEST-DRIVER"
    
    # Set vehicle state for simulation plugin
    gps_device.set_vehicle_state(FakeVehicleState())
    
    try:
        # Start GPS device
        print(f"📡 Starting GPS device: {device_id}")
        print(f"   Server: {server_url}")
        print(f"   Update interval: 2.0 seconds")
        print()
        
        gps_device.on()
        
        print("✅ GPS device started")
        print()
        print("The device will now:")
        print("  - Try to connect to GPS server")
        print("  - Retry every 5 seconds if server is down")
        print("  - Automatically reconnect if connection drops")
        print("  - Continue generating telemetry data")
        print()
        print("Monitoring... (Press Ctrl+C to stop)")
        print("-" * 70)
        print()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print()
        print("-" * 70)
        print("🛑 Stopping GPS device...")
        gps_device.off()
        print("✅ GPS device stopped cleanly")
        print()
        print("Test complete!")
        print("=" * 70)


if __name__ == "__main__":
    test_reconnection()
