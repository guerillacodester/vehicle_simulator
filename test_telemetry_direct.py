#!/usr/bin/env python3
"""
Quick test to verify telemetry packet creation and transmission.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import make_packet, PacketCodec
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter


async def test_packet_creation():
    """Test that packets are created correctly with all required fields."""
    print("=== Testing Packet Creation ===")
    
    # Create a test packet
    packet = make_packet(
        device_id="DRV001",  # Use driver's license as device ID
        lat=13.2,
        lon=-59.7,
        speed=55.0,
        heading=180.0,
        route="1B", 
        vehicle_reg="ZR101",
        driver_id="DRV001",
        driver_name={"first": "John", "last": "Smith"}
    )
    
    print(f"Created packet: {packet}")
    print(f"driverId field: {packet.driverId}")
    
    # Test codec encoding
    codec = PacketCodec()
    json_str = codec.encode_text(packet)
    print(f"JSON encoded: {json_str}")
    
    # Check if driverId is in the JSON
    assert "driverId" in json_str
    assert "DRV001" in json_str
    print("✅ Packet creation and encoding works correctly")


async def test_gps_connection():
    """Test actual GPS device connection to server."""
    print("\n=== Testing GPS Device Connection ===")
    
    # Create transmitter (use correct WebSocket URL)
    transmitter = WebSocketTransmitter(
        server_url="ws://localhost:5000",
        token="test_token",
        device_id="DRV001",  # Use driver's license as device ID
        codec=PacketCodec()
    )
    
    try:
        print("Connecting to telemetry server...")
        await transmitter.connect()
        print("✅ Connected successfully!")
        
        # Create and send a test packet
        packet = make_packet(
            device_id="DRV001",  # Use driver's license as device ID
            lat=13.2,
            lon=-59.7,
            speed=55.0,
            heading=180.0,
            route="1B",
            vehicle_reg="ZR101", 
            driver_id="DRV001",
            driver_name={"first": "John", "last": "Smith"}
        )
        
        print("Sending telemetry packet...")
        await transmitter.send(packet)
        print("✅ Packet sent successfully!")
        
        # Wait a moment for server processing
        await asyncio.sleep(1)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
    finally:
        try:
            await transmitter.close()
            print("✅ Connection closed")
        except:
            pass


async def main():
    """Run packet and connection tests."""
    print("🧪 Testing GPS Device Telemetry")
    print("=" * 40)
    
    try:
        await test_packet_creation()
        await test_gps_connection()
        
        print("\n🎉 All telemetry tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))