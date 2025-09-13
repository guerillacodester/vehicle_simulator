#!/usr/bin/env python3
"""
Test script to verify VehicleDriver and Conductor person state management.

Tests that the new BasePerson state management works properly for person components.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
from world.vehicle_simulator.vehicle.conductor import Conductor
from world.vehicle_simulator.vehicle.engine.engine_block import Engine
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.core.states import PersonState, DeviceState


class MockSpeedModel:
    """Mock speed model for testing."""
    def update(self):
        return {"velocity": 50.0}  # 50 km/h


class MockTransmitter:
    """Mock WebSocket transmitter."""
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


async def test_vehicle_driver_person_state():
    """Test VehicleDriver person state management."""
    print("\n=== Testing VehicleDriver Person State Management ===")
    
    # Create mock components
    buffer = EngineBuffer(size=10)
    model = MockSpeedModel()
    engine = Engine("ZR101", model, buffer, tick_time=0.1)
    gps_device = GPSDevice("DRV001", MockTransmitter())  # Use driver's license as device ID
    
    # Create route coordinates (simple square)
    route_coords = [
        (-59.6, 13.1),  # Start
        (-59.5, 13.1),  # East
        (-59.5, 13.2),  # North  
        (-59.6, 13.2),  # West
        (-59.6, 13.1)   # Back to start
    ]
    
    # Create vehicle driver
    driver = VehicleDriver(
        driver_id="DRV001",
        driver_name="John Smith", 
        vehicle_id="ZR101",
        route_coordinates=route_coords,
        engine_buffer=buffer
    )
    
    # Set vehicle components for driver to control
    driver.set_vehicle_components(engine=engine, gps_device=gps_device)
    
    # Test initial state
    print(f"Initial driver state: {driver.current_state}")
    print(f"Driver available: {driver.is_available()}")
    print(f"Driver present: {driver.is_present()}")
    assert driver.current_state == PersonState.OFFSITE
    assert not driver.is_available()
    assert not driver.is_present()
    
    # Test driver arrives and boards vehicle
    print("Driver arriving and boarding vehicle...")
    success = await driver.arrive()
    print(f"Boarding successful: {success}")
    print(f"Driver state: {driver.current_state}")
    print(f"Engine state: {engine.current_state}")
    print(f"GPS state: {gps_device.current_state}")
    
    assert success
    assert driver.current_state == PersonState.ONSITE
    assert driver.is_available()
    assert driver.is_present()
    # Engine and GPS should be ON since driver started them
    assert engine.current_state == DeviceState.ON
    # GPS might be ERROR due to no plugin, but that's expected
    
    # Wait a bit for components to run
    await asyncio.sleep(0.5)
    
    # Test driver departs and disembarks
    print("Driver departing and disembarking...")
    success = await driver.depart()
    print(f"Disembarking successful: {success}")
    print(f"Driver state: {driver.current_state}")
    print(f"Engine state: {engine.current_state}")
    print(f"GPS state: {gps_device.current_state}")
    
    assert success
    assert driver.current_state == PersonState.OFFSITE
    assert not driver.is_available()
    assert not driver.is_present()
    # Engine and GPS should be OFF since driver stopped them
    assert engine.current_state == DeviceState.OFF
    assert gps_device.current_state == DeviceState.OFF
    
    # Test person status
    status = driver.get_person_status()
    print(f"Driver status: {status}")
    assert status["person_name"] == "John Smith"
    assert status["component_id"] == "DRV001"
    assert status["component_type"] == "VehicleDriver"
    
    print("✅ VehicleDriver person state management tests passed!")


async def test_conductor_person_state():
    """Test Conductor person state management."""
    print("\n=== Testing Conductor Person State Management ===")
    
    # Create conductor
    conductor = Conductor(
        conductor_id="CON001",
        conductor_name="Jane Doe",
        vehicle_id="ZR101",
        capacity=40
    )
    
    # Test initial state
    print(f"Initial conductor state: {conductor.current_state}")
    print(f"Conductor available: {conductor.is_available()}")
    print(f"Conductor present: {conductor.is_present()}")
    assert conductor.current_state == PersonState.OFFSITE
    assert not conductor.is_available()
    
    # Test conductor arrives
    print("Conductor arriving for duty...")
    success = await conductor.arrive()
    print(f"Arrival successful: {success}")
    print(f"Conductor state: {conductor.current_state}")
    
    assert success
    assert conductor.current_state == PersonState.ONSITE
    assert conductor.is_available()
    assert conductor.is_present()
    
    # Test conductor passenger management
    print("Testing passenger management...")
    conductor.start_boarding()
    assert conductor.is_boarding_active()
    
    boarded = conductor.board_passengers(10)
    assert boarded
    assert conductor.get_passenger_count() == 10
    assert conductor.get_available_seats() == 30
    
    # Test conductor goes unavailable
    print("Conductor going unavailable...")
    success = await conductor.go_unavailable("Emergency")
    print(f"Unavailable transition: {success}")
    print(f"Conductor state: {conductor.current_state}")
    
    assert success
    assert conductor.current_state == PersonState.UNAVAILABLE
    assert not conductor.is_available()
    
    # Test return to duty
    print("Conductor returning to duty...")
    success = await conductor.return_to_duty()
    assert success
    assert conductor.current_state == PersonState.ONSITE
    assert conductor.is_available()
    
    # Test conductor departs
    print("Conductor departing...")
    success = await conductor.depart()
    print(f"Departure successful: {success}")
    print(f"Conductor state: {conductor.current_state}")
    
    assert success
    assert conductor.current_state == PersonState.OFFSITE
    
    # Test person status
    status = conductor.get_person_status()
    print(f"Conductor person status: {status}")
    assert status["person_name"] == "Jane Doe"
    assert status["component_id"] == "CON001"
    assert status["component_type"] == "Conductor"
    
    # Test conductor-specific status
    conductor_status = conductor.get_passenger_status()
    print(f"Conductor work status: {conductor_status}")
    assert conductor_status["vehicle_id"] == "ZR101"
    assert conductor_status["passengers"] == 10
    
    print("✅ Conductor person state management tests passed!")


async def main():
    """Run all person state management tests."""
    print("🧪 Testing Person Component State Management")
    print("=" * 60)
    
    try:
        await test_vehicle_driver_person_state()
        await test_conductor_person_state()
        
        print("\n🎉 All person component state management tests passed!")
        print("✅ BasePerson integration successful")
        print("✅ PersonState transitions working")
        print("✅ VehicleDriver controls vehicle components properly")
        print("✅ Conductor passenger management working")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))