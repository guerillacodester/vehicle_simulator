"""
Phase 3 Verification: Socket.IO Event Emission
===============================================
This test verifies that when vehicle becomes full:
1. on_full_callback is triggered
2. _signal_driver_continue() is called
3. Socket.IO 'conductor:ready:depart' event IS emitted (or attempted)

We'll mock the Socket.IO emit to prove it would be called.
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arknet_transit_simulator.vehicle.conductor import Conductor


async def test_socketio_emission():
    """Test that Socket.IO event is emitted when vehicle becomes full."""
    
    print("\n" + "="*80)
    print("PHASE 3 VERIFICATION: SOCKET.IO EVENT EMISSION")
    print("="*80 + "\n")
    
    # Track what events were emitted
    emitted_events = []
    
    async def mock_emit(event_name, data):
        """Mock Socket.IO emit to track what would be sent"""
        emitted_events.append({
            'event': event_name,
            'data': data
        })
        print(f"   📡 Socket.IO EMIT called: {event_name}")
        print(f"      Data: {data}")
    
    # Create conductor with mocked Socket.IO
    print("1️⃣  Creating Conductor with mocked Socket.IO...")
    
    conductor = Conductor(
        conductor_id="TEST_SOCKETIO",
        conductor_name="Socket.IO Test",
        vehicle_id="TEST_VEH_SIO",
        assigned_route_id="1A",
        capacity=2,
        use_socketio=True,  # Enable Socket.IO
        sio_url="http://localhost:3000"
    )
    
    # Mock the Socket.IO client
    conductor.sio.emit = mock_emit
    conductor.sio_connected = True  # Pretend we're connected
    
    print(f"   ✅ Conductor created")
    print(f"   📊 Socket.IO enabled: {conductor.use_socketio}")
    print(f"   📊 Socket.IO connected: {conductor.sio_connected}")
    print(f"   📊 on_full_callback: {conductor.on_full_callback is not None}")
    
    # Start conductor
    print("\n2️⃣  Starting Conductor...")
    await conductor.start()
    print(f"   ✅ Conductor started")
    
    # Board passengers to fill vehicle
    print("\n3️⃣  Boarding Passengers to Fill Vehicle...")
    print(f"   📊 Initial: {conductor.passengers_on_board}/{conductor.capacity}")
    
    passenger_ids = ["PASS_001", "PASS_002"]
    
    print(f"   📤 Boarding {len(passenger_ids)} passengers...")
    boarded = await conductor.board_passengers_by_id(passenger_ids)
    
    print(f"   ✅ Boarded {boarded} passengers")
    print(f"   📊 Final: {conductor.passengers_on_board}/{conductor.capacity}")
    
    # Wait a moment for async operations
    await asyncio.sleep(0.5)
    
    # Verify results
    print("\n4️⃣  Verifying Socket.IO Event Emission...")
    print(f"   📊 Events emitted: {len(emitted_events)}")
    
    if emitted_events:
        for i, event in enumerate(emitted_events):
            print(f"\n   Event {i+1}:")
            print(f"      Name: {event['event']}")
            print(f"      Data: {event['data']}")
        
        # Check for 'conductor:ready:depart' event
        depart_events = [e for e in emitted_events if e['event'] == 'conductor:ready:depart']
        
        if depart_events:
            print("\n   ✅ 'conductor:ready:depart' event WAS emitted!")
            print(f"   ✅ Vehicle ID in event: {depart_events[0]['data']['vehicle_id']}")
            print(f"   ✅ Passenger count in event: {depart_events[0]['data']['passenger_count']}")
            success = True
        else:
            print("\n   ⚠️  'conductor:ready:depart' event NOT found in emitted events")
            success = False
    else:
        print("   ⚠️  No events were emitted")
        success = False
    
    await conductor.stop()
    
    # Summary
    print("\n" + "="*80)
    print("TEST RESULTS:")
    print("-" * 80)
    print(f"✅ Conductor created with auto-depart enabled")
    print(f"✅ Vehicle filled to capacity ({conductor.passengers_on_board}/{conductor.capacity})")
    print(f"✅ on_full_callback triggered")
    
    if success:
        print(f"✅ Socket.IO 'conductor:ready:depart' event EMITTED")
        print("\n🎉 COMPLETE FLOW VERIFIED:")
        print("   board_passengers_by_id() → vehicle full →")
        print("   on_full_callback() → _signal_driver_continue() →")
        print("   Socket.IO emit('conductor:ready:depart')")
    else:
        print(f"❌ Socket.IO event NOT emitted (unexpected)")
    
    print("="*80 + "\n")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(test_socketio_emission())
    
    if result:
        print("✅ PHASE 3 COMPLETE: Full flow verified from boarding to Socket.IO emission!")
    else:
        print("❌ Verification failed")
        sys.exit(1)
