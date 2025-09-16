#!/usr/bin/env python3
"""
Test Enhanced Conductor
=======================

Demonstrates enhanced conductor capabilities including passenger monitoring,
driver communication, GPS state preservation, and intelligent stop management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Set up the path to import from the correct modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from conductor import Conductor, ConductorConfig, ConductorState
from ..models.self_aware_passenger import SelfAwarePassenger, EnhancedJourneyDetails

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class MockDriver:
    """Mock driver to demonstrate conductor-driver communication."""
    
    def __init__(self):
        self.signals_received = []
        self.engine_on = True
        self.current_position = (40.7589, -73.9851)  # Times Square
        
    def receive_signal(self, conductor_id: str, signal_data: dict):
        """Receive signal from conductor."""
        self.signals_received.append({
            'conductor_id': conductor_id,
            'signal': signal_data,
            'timestamp': datetime.now()
        })
        
        action = signal_data.get('action')
        if action == 'stop_vehicle':
            self.engine_on = False
            duration = signal_data.get('duration', 30)
            print(f"🚌 DRIVER: Engine OFF - Stopping for {duration:.0f} seconds")
            if signal_data.get('preserve_gps'):
                print(f"📍 DRIVER: GPS position preserved: {signal_data.get('gps_position')}")
                
        elif action == 'continue_driving':
            self.engine_on = True
            print(f"🚌 DRIVER: Engine ON - Continuing route")
            if signal_data.get('restore_gps'):
                restored_pos = signal_data.get('gps_position')
                print(f"📍 DRIVER: GPS position restored: {restored_pos}")
                if restored_pos:
                    self.current_position = restored_pos


class MockDepot:
    """Mock depot to simulate passenger queries."""
    
    def __init__(self):
        self.passengers_by_route = {}
        
    def add_passenger(self, route_id: str, passenger: SelfAwarePassenger):
        """Add passenger to depot tracking."""
        if route_id not in self.passengers_by_route:
            self.passengers_by_route[route_id] = []
        self.passengers_by_route[route_id].append(passenger)
        
    def get_passengers_for_route(self, route_id: str) -> List[SelfAwarePassenger]:
        """Get passengers waiting for specific route."""
        return self.passengers_by_route.get(route_id, [])


class MockPassengerService:
    """Mock passenger service to handle events."""
    
    def __init__(self):
        self.events_received = []
        
    def receive_event(self, event):
        """Receive event from conductor."""
        self.events_received.append(event)
        print(f"📡 SERVICE: Received event - {event}")


async def test_basic_conductor_operations():
    """Test basic enhanced conductor operations."""
    print("\n🔍 Testing Basic Enhanced Conductor Operations")
    print("=" * 60)
    
    # Create enhanced conductor
    config = ConductorConfig(
        pickup_radius_km=0.5,
        min_stop_duration_seconds=10,
        max_stop_duration_seconds=60,
        per_passenger_boarding_time=5,
        monitoring_interval_seconds=1
    )
    
    conductor = Conductor(
        conductor_id="COND_001",
        conductor_name="Test Conductor",
        vehicle_id="BUS_001",
        assigned_route_id="ROUTE_001",
        capacity=40,
        config=config
    )
    
    # Set up mock systems
    driver = MockDriver()
    depot = MockDepot()
    service = MockPassengerService()
    
    conductor.set_driver_callback(driver.receive_signal)
    conductor.set_depot_callback(depot.get_passengers_for_route)
    conductor.set_passenger_service_callback(service.receive_event)
    
    # Start conductor
    await conductor.start()
    print(f"✅ Conductor started - State: {conductor.conductor_state.value}")
    
    # Update vehicle position
    await conductor.update_vehicle_position(40.7589, -73.9851)
    print(f"📍 Vehicle position updated: {conductor.current_vehicle_position}")
    
    # Create test passenger near vehicle
    journey = EnhancedJourneyDetails(
        route_id="ROUTE_001",
        pickup_lat=40.7590,  # Very close to vehicle
        pickup_lon=-73.9850,
        destination_lat=40.7505,
        destination_lon=-73.9934
    )
    
    passenger = SelfAwarePassenger(
        passenger_id="TEST_PASS_001",
        journey=journey
    )
    
    depot.add_passenger("ROUTE_001", passenger)
    print(f"👤 Added passenger {passenger.component_id} to depot")
    
    # Let conductor monitor for a few seconds
    await asyncio.sleep(3)
    
    # Check conductor status
    status = conductor.get_enhanced_status()
    print(f"\n📊 Conductor Status:")
    for key, value in status.items():
        if key != 'config':  # Skip config details for brevity
            print(f"  {key}: {value}")
    
    # Stop conductor
    await conductor.stop()
    print(f"🛑 Conductor stopped")
    
    # Show driver signals received
    print(f"\n🚌 Driver received {len(driver.signals_received)} signals:")
    for i, signal in enumerate(driver.signals_received):
        print(f"  {i+1}. {signal['signal']['action']} from {signal['conductor_id']}")


async def test_stop_request_handling():
    """Test passenger stop request handling."""
    print("\n🛑 Testing Stop Request Handling")
    print("=" * 50)
    
    # Create conductor
    conductor = Conductor(
        conductor_id="COND_002",
        conductor_name="Stop Handler",
        vehicle_id="BUS_002",
        assigned_route_id="ROUTE_002",
        capacity=40
    )
    
    driver = MockDriver()
    conductor.set_driver_callback(driver.receive_signal)
    
    await conductor.start()
    await conductor.update_vehicle_position(40.7614, -73.9776)
    
    # Simulate passenger stop request
    await conductor.receive_stop_request("PASS_002", "Stop request for destination")
    print(f"🚏 Stop request received - State: {conductor.conductor_state.value}")
    
    # Let the stop operation complete
    await asyncio.sleep(3)
    
    print(f"📊 Final conductor state: {conductor.conductor_state.value}")
    print(f"🚌 Driver engine status: {'ON' if driver.engine_on else 'OFF'}")
    
    await conductor.stop()


async def test_gps_preservation():
    """Test GPS position preservation during stops."""
    print("\n📍 Testing GPS Position Preservation")
    print("=" * 50)
    
    conductor = Conductor(
        conductor_id="COND_003",
        conductor_name="GPS Tester",
        vehicle_id="BUS_003",
        assigned_route_id="ROUTE_003"
    )
    
    driver = MockDriver()
    conductor.set_driver_callback(driver.receive_signal)
    
    await conductor.start()
    
    # Update position multiple times
    positions = [
        (40.7589, -73.9851),  # Times Square
        (40.7614, -73.9776),  # Moving
        (40.7505, -73.9934)   # Empire State Building
    ]
    
    for i, (lat, lon) in enumerate(positions):
        await conductor.update_vehicle_position(lat, lon)
        print(f"📍 Position {i+1}: ({lat:.4f}, {lon:.4f})")
        
        if i == 1:  # Trigger stop at middle position
            await conductor.receive_stop_request("PASS_003", "Test stop")
            
        await asyncio.sleep(1)
    
    # Check if GPS was preserved correctly
    if conductor.preserved_gps_position:
        print(f"💾 Preserved GPS: {conductor.preserved_gps_position}")
    
    if driver.signals_received:
        stop_signal = next((s for s in driver.signals_received if s['signal']['action'] == 'stop_vehicle'), None)
        if stop_signal and stop_signal['signal'].get('preserve_gps'):
            print(f"✅ GPS preservation requested in driver signal")
    
    await conductor.stop()


async def test_capacity_management():
    """Test vehicle capacity management."""
    print("\n👥 Testing Capacity Management")
    print("=" * 40)
    
    # Create conductor with small capacity for testing
    conductor = Conductor(
        conductor_id="COND_004",
        conductor_name="Capacity Tester",
        vehicle_id="BUS_004",
        assigned_route_id="ROUTE_004",
        capacity=5  # Small capacity for testing
    )
    
    await conductor.start()
    
    # Test boarding passengers up to capacity
    print(f"Initial capacity: {conductor.get_capacity()}")
    
    for i in range(7):  # Try to board more than capacity
        success = conductor.board_passengers(1)
        current = conductor.get_passenger_count()
        available = conductor.get_available_seats()
        status = "✅" if success else "❌"
        
        print(f"{status} Passenger {i+1}: {current}/{conductor.capacity} (Available: {available})")
        
        if conductor.is_full():
            print(f"🚌 Vehicle FULL!")
            break
    
    # Test alighting
    print(f"\n🚪 Testing passenger alighting:")
    alighted = conductor.alight_passengers(3)
    print(f"👋 {alighted} passengers alighted")
    print(f"📊 Current: {conductor.get_passenger_count()}/{conductor.capacity}")
    
    await conductor.stop()


async def main():
    """Run all enhanced conductor tests."""
    print("🚀 Starting Enhanced Conductor Tests")
    print("=" * 70)
    
    try:
        await test_basic_conductor_operations()
        await test_stop_request_handling()
        await test_gps_preservation()
        await test_capacity_management()
        
        print("\n✅ All enhanced conductor tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())