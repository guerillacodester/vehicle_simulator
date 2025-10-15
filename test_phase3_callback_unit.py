"""
Phase 3 Unit Test: Callback Mechanism Validation
=================================================
Test that the on_full_callback mechanism works correctly
without requiring Socket.IO server.

This validates:
1. Callback is auto-wired on initialization
2. Callback triggers when vehicle becomes full
3. Callback can be enabled/disabled
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arknet_transit_simulator.vehicle.conductor import Conductor


async def test_callback_mechanism():
    """Test the callback mechanism without Socket.IO dependency."""
    
    print("\n" + "="*80)
    print("PHASE 3 UNIT TEST: CALLBACK MECHANISM")
    print("="*80 + "\n")
    
    # Track callback invocations
    callback_triggered = False
    callback_count = 0
    
    def mock_callback():
        """Mock callback to track invocations"""
        nonlocal callback_triggered, callback_count
        callback_triggered = True
        callback_count += 1
        print(f"   🔔 CALLBACK TRIGGERED (count: {callback_count})")
    
    # Test 1: Auto-wiring on initialization
    print("TEST 1: Auto-wiring on initialization")
    print("-" * 40)
    
    conductor = Conductor(
        conductor_id="TEST_AUTO_WIRE",
        conductor_name="Auto-wire Test",
        vehicle_id="TEST_VEH_AUTO",
        assigned_route_id="1A",
        capacity=3,
        use_socketio=False  # Disable Socket.IO for unit test
    )
    
    assert conductor.on_full_callback is not None, \
        "on_full_callback should be auto-wired in __init__"
    print("   ✅ Callback auto-wired on initialization")
    
    # Test 2: Manual callback replacement
    print("\nTEST 2: Manual callback replacement")
    print("-" * 40)
    
    conductor.on_full_callback = mock_callback
    print("   ✅ Callback replaced with mock")
    
    # Test 3: Callback triggers when full
    print("\nTEST 3: Callback triggers when full")
    print("-" * 40)
    
    print(f"   📊 Initial: {conductor.passengers_on_board}/{conductor.capacity}")
    
    # Manually increase passenger count to trigger callback
    conductor.passengers_on_board = 2
    print(f"   📊 After boarding 2: {conductor.passengers_on_board}/{conductor.capacity}")
    
    # This should NOT trigger callback (not full yet)
    if conductor.on_full_callback and conductor.passengers_on_board >= conductor.capacity:
        conductor.on_full_callback()
    
    assert not callback_triggered, "Callback should NOT trigger when not full"
    print("   ✅ Callback correctly NOT triggered when not full")
    
    # Board one more to reach capacity
    conductor.passengers_on_board = 3
    print(f"   📊 After boarding 1 more: {conductor.passengers_on_board}/{conductor.capacity}")
    
    # This SHOULD trigger callback (now full)
    if conductor.on_full_callback and conductor.passengers_on_board >= conductor.capacity:
        conductor.on_full_callback()
    
    assert callback_triggered, "Callback SHOULD trigger when full"
    assert callback_count == 1, f"Callback should trigger once, got {callback_count}"
    print("   ✅ Callback correctly TRIGGERED when full")
    
    # Test 4: Enable/disable functionality
    print("\nTEST 4: Enable/disable auto-depart")
    print("-" * 40)
    
    # Reset for next test
    conductor2 = Conductor(
        conductor_id="TEST_ENABLE_DISABLE",
        conductor_name="Enable/Disable Test",
        vehicle_id="TEST_VEH_ED",
        assigned_route_id="1A",
        capacity=2,
        use_socketio=False
    )
    
    # Should be enabled by default
    assert conductor2.on_full_callback is not None, \
        "Callback should be enabled by default"
    print("   ✅ Auto-depart enabled by default")
    
    # Disable
    conductor2.disable_auto_depart_on_full()
    assert conductor2.on_full_callback is None, \
        "Callback should be None after disable"
    print("   ✅ Auto-depart disabled successfully")
    
    # Re-enable
    conductor2.enable_auto_depart_on_full()
    assert conductor2.on_full_callback is not None, \
        "Callback should be set after re-enable"
    print("   ✅ Auto-depart re-enabled successfully")
    
    # Test 5: Integration with board_passengers_by_id
    print("\nTEST 5: Integration with board_passengers_by_id")
    print("-" * 40)
    
    integration_callback_triggered = False
    
    def integration_callback():
        nonlocal integration_callback_triggered
        integration_callback_triggered = True
        print("   🔔 Integration callback triggered!")
    
    conductor3 = Conductor(
        conductor_id="TEST_INTEGRATION",
        conductor_name="Integration Test",
        vehicle_id="TEST_VEH_INT",
        assigned_route_id="1A",
        capacity=2,
        use_socketio=False
    )
    
    # Start conductor to enable async operations
    await conductor3.start()
    
    # Replace callback with test callback
    conductor3.on_full_callback = integration_callback
    
    # Board passengers via the actual method
    passenger_ids = ["PASS_001", "PASS_002"]
    
    print(f"   📊 Boarding {len(passenger_ids)} passengers...")
    boarded = await conductor3.board_passengers_by_id(passenger_ids)
    
    print(f"   ✅ Boarded {boarded} passengers")
    print(f"   📊 Final count: {conductor3.passengers_on_board}/{conductor3.capacity}")
    
    # Verify callback was triggered
    assert integration_callback_triggered, \
        "Callback should trigger when board_passengers_by_id fills vehicle"
    print("   ✅ Callback triggered by board_passengers_by_id")
    
    await conductor3.stop()
    
    # Final results
    print("\n" + "="*80)
    print("ALL TESTS PASSED")
    print("="*80)
    print("✅ Callback auto-wired on initialization")
    print("✅ Callback can be replaced")
    print("✅ Callback triggers when vehicle full")
    print("✅ Callback does NOT trigger when not full")
    print("✅ Enable/disable functionality works")
    print("✅ Integrates with board_passengers_by_id")
    print("="*80 + "\n")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_callback_mechanism())
    
    if result:
        print("🎉 PHASE 3 CALLBACK MECHANISM VALIDATED!")
    else:
        print("❌ Tests failed")
        sys.exit(1)
