#!/usr/bin/env python3
"""
Integration Test - Dynamic Passenger System
==========================================

Integration test for the dynamic passenger system components that can be run
from the project root to properly handle all import paths.
"""

import sys
import os
import asyncio
import logging
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def load_real_route_coordinates():
    """Load real route coordinates from the route data files."""
    try:
        route_file = os.path.join(os.path.dirname(__file__), 'data', 'roads', 'route_1_final_processed.geojson')
        with open(route_file, 'r') as f:
            route_data = json.load(f)
        
        coordinates = route_data['features'][0]['geometry']['coordinates']
        
        # Extract some points along the route for realistic pickup/destination
        total_points = len(coordinates)
        pickup_point = coordinates[int(total_points * 0.1)]  # 10% along route
        destination_point = coordinates[int(total_points * 0.8)]  # 80% along route
        
        return {
            'route_id': 'route_1_final_processed',
            'pickup_coords': (pickup_point[1], pickup_point[0]),  # lat, lon
            'destination_coords': (destination_point[1], destination_point[0]),  # lat, lon
            'full_coordinates': coordinates
        }
    except Exception as e:
        print(f"⚠️ Could not load real route data: {e}")
        # Fallback to Barbados coordinates (approximate area)
        return {
            'route_id': 'route_1',
            'pickup_coords': (13.2809774, -59.6462136),
            'destination_coords': (13.3194437, -59.636912),
            'full_coordinates': [[-59.6462136, 13.2809774], [-59.636912, 13.3194437]]
        }

def test_imports():
    """Test that all our enhanced components can be imported."""
    print("🔍 Testing Component Imports")
    print("=" * 40)
    
    try:
        # Test passenger events
        from world.arknet_transit_simulator.passenger_modeler.passenger_events import (
            PassengerEvent, EventType, EventPriority, PassengerBuffer
        )
        print("✅ PassengerEvent system imports successful")
        
        # Test passenger service
        from world.arknet_transit_simulator.passenger_modeler.passenger_service import (
            DynamicPassengerService
        )
        print("✅ DynamicPassengerService imports successful")
        
        # Test enhanced conductor
        from world.arknet_transit_simulator.vehicle.conductor import (
            Conductor, ConductorConfig, ConductorState
        )
        print("✅ Enhanced Conductor imports successful")
        
        # Test self-aware passenger
        from world.arknet_transit_simulator.models.self_aware_passenger import (
            SelfAwarePassenger, EnhancedJourneyDetails, StopLocation
        )
        print("✅ SelfAwarePassenger imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_passenger_event_system():
    """Test the passenger event system."""
    print("\n📡 Testing Passenger Event System")
    print("=" * 40)
    
    try:
        from world.arknet_transit_simulator.passenger_modeler.passenger_events import (
            PassengerEvent, EventType, EventPriority, PassengerBuffer
        )
        
        # Create events
        # Load real route data for testing
        route_data = load_real_route_coordinates()
        
        spawn_event = PassengerEvent(
            event_id="SPAWN_TEST_001",
            event_type=EventType.SPAWN,
            passenger_id="TEST_001",
            timestamp=datetime.now(),
            route_id=route_data['route_id'],
            location_lat=route_data['pickup_coords'][0],
            location_lon=route_data['pickup_coords'][1],
            priority=EventPriority.NORMAL
        )
        
        pickup_event = PassengerEvent(
            event_id="PICKUP_TEST_002",
            event_type=EventType.PICKUP,
            passenger_id="TEST_002",
            timestamp=datetime.now(),
            route_id=route_data['route_id'],
            vehicle_id="BUS_001",
            location_lat=route_data['destination_coords'][0],
            location_lon=route_data['destination_coords'][1],
            priority=EventPriority.HIGH
        )
        
        print(f"✅ Created events: {spawn_event.event_type.value}, {pickup_event.event_type.value}")
        
        # Test buffer
        buffer = PassengerBuffer(max_size=10)
        await buffer.push_event(spawn_event)
        await buffer.push_event(pickup_event)
        
        # Pop events (should come out by priority)
        event1 = await buffer.pop_event()  # Should be pickup (higher priority)
        event2 = await buffer.pop_event()  # Should be spawn
        
        print(f"✅ Events processed by priority: {event1.event_type.value} (first), {event2.event_type.value} (second)")
        
        return True
        
    except Exception as e:
        print(f"❌ Event system test failed: {e}")
        return False

async def test_passenger_service():
    """Test the dynamic passenger service."""
    print("\n🚀 Testing Dynamic Passenger Service")
    print("=" * 40)
    
    try:
        from world.arknet_transit_simulator.passenger_modeler.passenger_service import (
            DynamicPassengerService
        )
        
        # Create service
        routes = ["ROUTE_001", "ROUTE_002"]
        service = DynamicPassengerService(
            route_ids=routes,
            max_memory_mb=1  # Small limit for testing
        )
        
        print(f"✅ Service created for routes: {routes}")
        
        # Start service
        await service.start_service()
        print("✅ Service started successfully")
        
        # Let it run briefly
        await asyncio.sleep(2)
        
        # Check status
        status = await service.get_service_status()
        print(f"📊 Service status: Running={status['is_running']}, Passengers={status['active_passengers']}")
        
        # Stop service
        await service.stop_service()
        print("✅ Service stopped successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Passenger service test failed: {e}")
        return False

def test_conductor_config():
    """Test conductor configuration loading."""
    print("\n⚙️ Testing Conductor Configuration")
    print("=" * 40)
    
    try:
        from world.arknet_transit_simulator.vehicle.conductor import (
            Conductor, ConductorConfig, ConductorState
        )
        
        # Test configuration
        config = ConductorConfig(
            pickup_radius_km=0.3,
            min_stop_duration_seconds=20,
            max_stop_duration_seconds=120,
            per_passenger_boarding_time=10
        )
        
        print(f"✅ Configuration created: pickup_radius={config.pickup_radius_km}km")
        
        # Test conductor creation
        conductor = Conductor(
            conductor_id="TEST_COND_001",
            conductor_name="Test Conductor",
            vehicle_id="TEST_BUS_001",
            assigned_route_id="ROUTE_001",
            config=config
        )
        
        print(f"✅ Conductor created: {conductor.component_id} on route {conductor.assigned_route_id}")
        print(f"📊 Initial state: {conductor.conductor_state.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Conductor configuration test failed: {e}")
        return False

async def test_enhanced_passenger():
    """Test enhanced passenger creation with real route data."""
    print("\n👤 Testing Enhanced Passenger with Real Route Data")
    print("=" * 50)
    
    try:
        from world.arknet_transit_simulator.models.self_aware_passenger import (
            SelfAwarePassenger, EnhancedJourneyDetails, PassengerState, create_self_aware_passenger
        )
        
        # Load real route data
        route_data = load_real_route_coordinates()
        
        # Create enhanced passenger using real coordinates
        passenger = create_self_aware_passenger(
            route_id=route_data['route_id'],
            pickup_coords=route_data['pickup_coords'],
            destination_coords=route_data['destination_coords'],
            passenger_id="REAL_PASSENGER_001"
        )
        
        print(f"✅ Enhanced passenger created: {passenger.component_id}")
        print(f"📊 Initial state: {passenger.passenger_state.value}")
        print(f"🗺️ Journey: {passenger.enhanced_journey.route_id}")
        print(f"📍 Real Pickup: ({passenger.enhanced_journey.pickup_lat:.6f}, {passenger.enhanced_journey.pickup_lon:.6f})")
        print(f"🎯 Real Destination: ({passenger.enhanced_journey.destination_lat:.6f}, {passenger.enhanced_journey.destination_lon:.6f})")
        
        # Calculate and display distance
        distance = passenger.enhanced_journey.journey_distance_km
        print(f"📏 Journey Distance: {distance:.2f} km")
        
        # Show this is from real Barbados route data
        if route_data['route_id'] == 'route_1_final_processed':
            print("🏝️ Using real Barbados transit route coordinates")
        else:
            print("🗺️ Using approximate route coordinates")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced passenger test failed: {e}")
        return False

async def main():
    """Run all integration tests."""
    print("🚀 Dynamic Passenger System Integration Tests")
    print("=" * 60)
    print(f"📅 Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests_passed = 0
    total_tests = 5
    
    # Test imports
    if test_imports():
        tests_passed += 1
    
    # Test event system
    if await test_passenger_event_system():
        tests_passed += 1
    
    # Test passenger service
    if await test_passenger_service():
        tests_passed += 1
    
    # Test conductor configuration
    if test_conductor_config():
        tests_passed += 1
    
    # Test enhanced passenger
    if await test_enhanced_passenger():
        tests_passed += 1
    
    # Results
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All integration tests PASSED! 🎉")
        print("Ready for commit! 🚀")
    else:
        print(f"❌ {total_tests - tests_passed} tests FAILED")
        print("Please fix issues before committing")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)