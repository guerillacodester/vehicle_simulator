#!/usr/bin/env python3
"""
Test script to verify Engine and GPS Device state management integration.

Tests that the new BaseComponent state management works properly while maintaining
backward compatibility with existing on/off methods.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from world.vehicle_simulator.vehicle.engine.engine_block import Engine
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.core.states import DeviceState


class MockSpeedModel:
    """Mock speed model for testing."""
    def update(self):
        return {"velocity": 50.0}  # 50 km/h


async def test_engine_state_management():
    """Test Engine component with state management."""
    print("\n=== Testing Engine State Management ===")
    
    # Create engine with buffer
    buffer = EngineBuffer(size=10)
    model = MockSpeedModel()
    engine = Engine("TEST001", model, buffer, tick_time=0.1)
    
    # Test initial state
    print(f"Initial state: {engine.current_state}")
    print(f"Is active: {engine.is_active()}")
    assert engine.current_state == DeviceState.OFF
    assert not engine.is_active()
    
    # Test async start
    print("Starting engine with async method...")
    success = await engine.start()
    print(f"Start successful: {success}")
    print(f"Current state: {engine.current_state}")
    print(f"Is active: {engine.is_active()}")
    assert success
    assert engine.current_state == DeviceState.ON
    assert engine.is_active()
    
    # Wait a bit to let engine run
    await asyncio.sleep(0.5)
    
    # Test stop
    print("Stopping engine with async method...")
    success = await engine.stop()
    print(f"Stop successful: {success}")
    print(f"Current state: {engine.current_state}")
    print(f"Is active: {engine.is_active()}")
    assert success
    assert engine.current_state == DeviceState.OFF
    assert not engine.is_active()
    
    # Test legacy on/off methods (sync)
    print("Testing legacy on() method...")
    result = engine.on()
    print(f"Legacy on() result: {result}")
    # Give time for the async task to complete
    await asyncio.sleep(0.1)
    print(f"Current state: {engine.current_state}")
    assert engine.current_state == DeviceState.ON
    
    await asyncio.sleep(0.2)
    
    print("Testing legacy off() method...")
    result = engine.off()
    print(f"Legacy off() result: {result}")
    # Give time for the async task to complete
    await asyncio.sleep(0.1)
    print(f"Current state: {engine.current_state}")
    assert engine.current_state == DeviceState.OFF
    
    print("✅ Engine state management tests passed!")


async def test_gps_device_state_management():
    """Test GPS Device component with state management."""
    print("\n=== Testing GPS Device State Management ===")
    
    # Create mock transmitter
    class MockTransmitter:
        async def connect(self):
            pass
        async def send(self, packet):
            pass
        async def close(self):
            pass
        def request_close(self):
            pass
        def force_close(self):
            pass
    
    transmitter = MockTransmitter()
    
    # Create GPS device without plugin config (to avoid complex setup)
    gps_device = GPSDevice("DRV001", transmitter)  # Use driver's license as device ID
    
    # Test initial state
    print(f"Initial state: {gps_device.current_state}")
    print(f"Is active: {gps_device.is_active()}")
    assert gps_device.current_state == DeviceState.OFF
    assert not gps_device.is_active()
    
    # Test start (without plugin, should fail gracefully)
    print("Attempting to start GPS device...")
    success = await gps_device.start()
    print(f"Start result: {success}")
    print(f"Current state: {gps_device.current_state}")
    # May fail due to no plugin, but state should be managed
    
    # Test stop
    print("Stopping GPS device...")
    success = await gps_device.stop()
    print(f"Stop result: {success}")
    print(f"Current state: {gps_device.current_state}")
    assert gps_device.current_state == DeviceState.OFF
    
    # Test get_status method
    status = gps_device.get_status()
    print(f"Device status: {status}")
    assert status["component_id"] == "TEST001"
    assert status["component_type"] == "GPSDevice"
    assert status["state_type"] == "DeviceState"
    
    print("✅ GPS Device state management tests passed!")


async def main():
    """Run all state management tests."""
    print("🧪 Testing Vehicle Component State Management")
    print("=" * 50)
    
    try:
        await test_engine_state_management()
        await test_gps_device_state_management()
        
        print("\n🎉 All component state management tests passed!")
        print("✅ BaseComponent integration successful")
        print("✅ DeviceState transitions working")
        print("✅ Backward compatibility maintained")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))