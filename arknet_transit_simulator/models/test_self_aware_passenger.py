#!/usr/bin/env python3
"""
Test Self-Aware Passenger
==========================

Demonstrates enhanced passenger capabilities including GPS tracking,
stop monitoring, conductor communication, and multi-route journeys.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from self_aware_passenger import (
    SelfAwarePassenger, 
    EnhancedJourneyDetails, 
    StopLocation, 
    ConnectionPlan,
    PassengerState,
    create_self_aware_passenger
)

# Add the parent directory to import path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from passenger_modeler.passenger_events import PassengerEvent


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class MockConductor:
    """Mock conductor to demonstrate passenger-conductor communication."""
    
    def __init__(self):
        self.stop_requests = []
        
    def receive_stop_request(self, passenger_id: str, message: str):
        """Receive stop request from passenger."""
        self.stop_requests.append({
            'passenger_id': passenger_id,
            'message': message,
            'timestamp': datetime.now()
        })
        print(f"🚌 CONDUCTOR: Received stop request from {passenger_id}: {message}")


class MockPassengerService:
    """Mock passenger service to demonstrate event handling."""
    
    def __init__(self):
        self.events = []
        
    def receive_event(self, event: PassengerEvent):
        """Receive event from passenger."""
        self.events.append(event)
        print(f"📡 SERVICE: Received {event.event_type.value} event from {event.passenger_id}")


async def test_basic_journey():
    """Test basic single-route journey with GPS tracking."""
    print("\n🔍 Testing Basic Self-Aware Journey")
    print("=" * 50)
    
    # Create passenger with single route
    passenger = create_self_aware_passenger(
        route_id="ROUTE_001",
        pickup_coords=(40.7589, -73.9851),  # Times Square
        destination_coords=(40.7505, -73.9934),  # Empire State Building
        passenger_id="TEST_001"
    )
    
    # Set up communication
    conductor = MockConductor()
    service = MockPassengerService()
    
    passenger.set_conductor_callback(conductor.receive_stop_request)
    passenger.set_event_callback(service.receive_event)
    
    # Start passenger
    await passenger.start()
    print(f"✅ Passenger {passenger.component_id} started - State: {passenger.passenger_state.value}")
    
    # Simulate boarding
    await passenger.board_vehicle("BUS_001", "ROUTE_001")
    print(f"🚌 Passenger boarded - State: {passenger.passenger_state.value}")
    
    # Simulate GPS updates (approaching destination)
    gps_points = [
        (40.7580, -73.9860),  # Starting position
        (40.7570, -73.9880),  # Moving closer
        (40.7550, -73.9900),  # Getting closer
        (40.7520, -73.9920),  # Very close (should trigger stop request)
        (40.7505, -73.9934)   # At destination
    ]
    
    for i, (lat, lon) in enumerate(gps_points):
        await passenger.update_gps_position(lat, lon)
        print(f"📍 GPS Update {i+1}: ({lat:.4f}, {lon:.4f}) - State: {passenger.passenger_state.value}")
        await asyncio.sleep(1)  # Small delay between updates
        
    # Simulate disembarking
    await passenger.disembark_vehicle("BUS_001")
    print(f"🚪 Passenger disembarked - State: {passenger.passenger_state.value}")
    
    # Display results
    print(f"\n📊 Journey Summary:")
    summary = passenger.get_enhanced_summary()
    for key, value in summary.items():
        if value is not None:
            print(f"  {key}: {value}")
            
    print(f"\n🚌 Conductor received {len(conductor.stop_requests)} stop requests")
    print(f"📡 Service received {len(service.events)} events")
    
    await passenger.stop()


async def test_multi_route_journey():
    """Test multi-route journey with connections."""
    print("\n🔄 Testing Multi-Route Journey with Connections")
    print("=" * 50)
    
    # Create transfer stop
    transfer_stop = StopLocation(
        stop_id="TRANSFER_001",
        stop_name="Main Transfer Hub",
        latitude=40.7614,
        longitude=-73.9776,
        route_ids=["ROUTE_001", "ROUTE_002"]
    )
    
    # Create connection plan
    connection = ConnectionPlan(
        from_route_id="ROUTE_001",
        to_route_id="ROUTE_002", 
        transfer_stop=transfer_stop,
        max_wait_time=timedelta(minutes=10)
    )
    
    # Create journey with connection
    journey = EnhancedJourneyDetails(
        route_id="ROUTE_001",
        pickup_lat=40.7589,
        pickup_lon=-73.9851,
        destination_lat=40.7829,
        destination_lon=-73.9654,
        connections=[connection]
    )
    
    passenger = SelfAwarePassenger(
        passenger_id="MULTI_001",
        journey=journey
    )
    
    # Set up communication
    conductor = MockConductor()
    service = MockPassengerService()
    
    passenger.set_conductor_callback(conductor.receive_stop_request)
    passenger.set_event_callback(service.receive_event)
    
    await passenger.start()
    print(f"✅ Multi-route passenger started - Current route: {passenger.enhanced_journey.current_route_id}")
    
    # First leg of journey
    await passenger.board_vehicle("BUS_001", "ROUTE_001")
    
    # Simulate GPS updates approaching transfer
    await passenger.update_gps_position(40.7614, -73.9776)  # At transfer stop
    
    # Disembark for connection
    await passenger.disembark_vehicle("BUS_001")
    print(f"🔄 At transfer stop - State: {passenger.passenger_state.value}")
    
    # Simulate waiting and boarding next vehicle
    await asyncio.sleep(2)
    await passenger.board_vehicle("BUS_002", "ROUTE_002")
    
    # Continue to final destination
    await passenger.update_gps_position(40.7829, -73.9654)  # At final destination
    await passenger.disembark_vehicle("BUS_002")
    
    print(f"🏁 Multi-route journey complete - State: {passenger.passenger_state.value}")
    
    # Display results
    summary = passenger.get_enhanced_summary()
    print(f"📊 Final route index: {summary['current_route_index']}")
    print(f"📊 Connections used: {summary['has_connections']}")
    
    await passenger.stop()


async def test_timeout_handling():
    """Test connection timeout handling."""
    print("\n⏰ Testing Connection Timeout Handling")
    print("=" * 50)
    
    # Create connection with short timeout
    transfer_stop = StopLocation("TIMEOUT_STOP", "Timeout Test Stop", 40.7614, -73.9776)
    connection = ConnectionPlan(
        from_route_id="ROUTE_001",
        to_route_id="ROUTE_002",
        transfer_stop=transfer_stop,
        max_wait_time=timedelta(seconds=3)  # Very short for testing
    )
    
    journey = EnhancedJourneyDetails(
        route_id="ROUTE_001",
        pickup_lat=40.7589,
        pickup_lon=-73.9851,
        destination_lat=40.7829,
        destination_lon=-73.9654,
        connections=[connection]
    )
    
    passenger = SelfAwarePassenger(passenger_id="TIMEOUT_001", journey=journey)
    service = MockPassengerService()
    passenger.set_event_callback(service.receive_event)
    
    await passenger.start()
    await passenger.board_vehicle("BUS_001", "ROUTE_001")
    
    # Disembark at transfer (starts waiting)
    await passenger.disembark_vehicle("BUS_001")
    print(f"⏳ Waiting for connection - State: {passenger.passenger_state.value}")
    
    # Wait for timeout
    await asyncio.sleep(4)
    print(f"⏰ After timeout - State: {passenger.passenger_state.value}")
    
    # Check if timeout event was generated
    timeout_events = [e for e in service.events if e.event_type.value == "timeout"]
    print(f"📡 Timeout events generated: {len(timeout_events)}")
    
    await passenger.stop()


async def main():
    """Run all passenger tests."""
    print("🚀 Starting Self-Aware Passenger Tests")
    print("=" * 60)
    
    try:
        await test_basic_journey()
        await test_multi_route_journey()
        await test_timeout_handling()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())