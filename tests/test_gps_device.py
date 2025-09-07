#!/usr/bin/env python3
"""
Test GPS Device Simulator - connects to our test WebSocket server
"""

from datetime import datetime, timedelta, timezone
import os, time, configparser
from world.vehicle.gps_device.device import GPSDevice

def main():
    # Load secrets
    auth_token = os.getenv("AUTH_TOKEN", "test-token-123")
    interval = float(os.getenv("UPDATE_INTERVAL", 1.0))

    # Use our test server instead of the default
    server_url = "ws://localhost:5001/"
    
    print(f"🧪 Testing GPS Device Simulator")
    print(f"📡 Server: {server_url}")
    print(f"🔑 Token: {auth_token}")
    print(f"⏱️ Interval: {interval}s")
    print("-" * 50)

    # Create GPS device with unique ID
    device_id = "TEST-BUS-001"
    gps = GPSDevice(device_id, server_url, auth_token, method="ws", interval=interval)

    print(f"🚌 Starting GPS device: {device_id}")
    gps.on()

    # Feed realistic Barbados GPS telemetry data
    gps_data = [
        {
            "lat": 13.2810,  # Barbados coordinates
            "lon": -59.6463,
            "speed": 42.0,
            "heading": 143.5,
            "route": "R001",
            "vehicle_reg": "BUS001",
            "driver_id": "drv-001",
            "driver_name": {"first": "John", "last": "Driver"},
            "ts": datetime.now(timezone.utc).isoformat(),
        },
        {
            "lat": 13.2815,  # Moving north
            "lon": -59.6465,
            "speed": 45.0,
            "heading": 144.0,
            "route": "R001",
            "vehicle_reg": "BUS001",
            "driver_id": "drv-001",
            "driver_name": {"first": "John", "last": "Driver"},
            "ts": (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat(),
        },
        {
            "lat": 13.2820,  # Moving further north
            "lon": -59.6467,
            "speed": 38.0,
            "heading": 145.0,
            "route": "R001",
            "vehicle_reg": "BUS001",
            "driver_id": "drv-001",
            "driver_name": {"first": "John", "last": "Driver"},
            "ts": (datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat(),
        },
        {
            "lat": 13.2825,  # Continuing movement
            "lon": -59.6470,
            "speed": 52.0,
            "heading": 146.0,
            "route": "R001",
            "vehicle_reg": "BUS001",
            "driver_id": "drv-001",
            "driver_name": {"first": "John", "last": "Driver"},
            "ts": (datetime.now(timezone.utc) + timedelta(seconds=3)).isoformat(),
        },
        {
            "lat": 13.2830,  # Final position
            "lon": -59.6472,
            "speed": 35.0,
            "heading": 147.0,
            "route": "R001",
            "vehicle_reg": "BUS001",
            "driver_id": "drv-001",
            "driver_name": {"first": "John", "last": "Driver"},
            "ts": (datetime.now(timezone.utc) + timedelta(seconds=4)).isoformat(),
        }
    ]

    # Send GPS data with proper timing
    for i, data in enumerate(gps_data):
        print(f"📍 Sending GPS update #{i+1}: Lat {data['lat']}, Lon {data['lon']}, Speed {data['speed']} km/h")
        gps.buffer.write(data)
        time.sleep(interval)  # Wait between updates

    print("⏳ Waiting for transmission to complete...")
    time.sleep(3)  # Let worker flush remaining data
    
    print("🛑 Stopping GPS device...")
    gps.off()
    
    print("✅ GPS device test completed!")

if __name__ == "__main__":
    main()
