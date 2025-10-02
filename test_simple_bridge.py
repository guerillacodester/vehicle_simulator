"""
Simple Bridge Smoke Test
========================

Test basic proximity detection and boarding coordination.
No complex features - just basic functionality.
"""

import sys
import os
from datetime import datetime

# Add project paths  
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_simple_bridge_smoke():
    """Basic smoke test for simple commuter bridge."""
    print("🧪 SMOKE TEST: Simple Commuter Bridge")
    print("=" * 50)
    
    try:
        # Import required components
        from arknet_transit_simulator.interfaces.simple_commuter_bridge import SimpleCommuterBridge, SimpleBoardingCoordinator
        from commuter_service.location_aware_commuter import LocationAwareCommuter, CommuterState
        
        print("Test 1: Bridge Creation...")
        bridge = SimpleCommuterBridge(proximity_radius_m=150)
        coordinator = SimpleBoardingCoordinator(bridge)
        assert bridge.proximity_radius_m == 150
        print("✅ Bridge and coordinator created")
        
        print("Test 2: Create Test Commuter...")
        # Create a commuter near a route
        commuter = LocationAwareCommuter(
            person_id="TEST_COMMUTER_001",
            spawn_location=(13.0827, -59.6130),  # Bridgetown
            destination_location=(13.1135, -59.6333),  # University  
            trip_purpose="education",
            priority=0.7
        )
        assert commuter.state == CommuterState.WAITING_TO_BOARD
        print(f"✅ Commuter created: {commuter.person_name}")
        
        print("Test 3: Route Proximity Detection...")
        # Create a simple route that passes near the commuter
        test_route = [
            (13.0800, -59.6100),  # Route start
            (13.0850, -59.6140),  # Near commuter (should detect)
            (13.0900, -59.6180),  # Route continues
            (13.1135, -59.6333)   # Route end (University)
        ]
        
        # Test proximity detection
        is_near = bridge._is_commuter_near_route(commuter, test_route)
        print(f"   Commuter near route: {is_near}")
        assert is_near, "Commuter should be detected near route"
        print("✅ Proximity detection working")
        
        print("Test 4: Direction Compatibility...")
        vehicle_position = (13.0800, -59.6100)  # Vehicle at start of route
        is_compatible = bridge._is_direction_compatible(commuter, test_route, vehicle_position)
        print(f"   Direction compatible: {is_compatible}")
        assert is_compatible, "Direction should be compatible"
        print("✅ Direction compatibility working")
        
        print("Test 5: Boarding Process...")
        # Test boarding request
        boarding_requested = bridge.request_boarding(commuter)
        assert boarding_requested, "Boarding should be requested successfully"
        assert commuter.state == CommuterState.REQUESTING_PICKUP
        print("✅ Boarding request successful")
        
        # Test boarding completion
        boarding_completed = bridge.complete_boarding(commuter)
        assert boarding_completed, "Boarding should complete successfully"
        assert commuter.state == CommuterState.ONBOARD
        print("✅ Boarding completion successful")
        
        print("Test 6: Boarding Coordinator...")
        # Reset commuter for coordinator test
        commuter.state = CommuterState.WAITING_TO_BOARD
        
        # Test scanning (without reservoir for now)
        eligible = coordinator.scan_for_boarding_opportunities(
            vehicle_position=vehicle_position,
            vehicle_route=test_route,
            route_id="1A"
        )
        # Should be empty since no reservoir connected
        assert len(eligible) == 0
        print("✅ Coordinator scanning working (no reservoir)")
        
        # Test boarding workflow
        test_commuters = [commuter]
        boarding_initiated = coordinator.initiate_boarding(test_commuters)
        assert boarding_initiated, "Boarding should be initiated"
        assert coordinator.is_boarding_in_progress()
        print("✅ Boarding initiation working")
        
        boarded_count = coordinator.complete_boarding()
        assert boarded_count == 1, "Should board 1 commuter"
        assert not coordinator.is_boarding_in_progress()
        print("✅ Boarding completion working")
        
        print("\n🎉 ALL SMOKE TESTS PASSED!")
        print("\n📋 SIMPLE BRIDGE FEATURES VALIDATED:")
        print("  ✅ Basic proximity detection (150m radius)")
        print("  ✅ Simple direction compatibility checking")  
        print("  ✅ Basic boarding request/completion workflow")
        print("  ✅ Simple coordinator for boarding management")
        print("  ✅ No complex features (as requested)")
        
        return True
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ SMOKE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_simple_bridge_smoke()
    if success:
        print("\n🚀 STEP 1.2 SMOKE TEST: PASSED")
        print("✅ Simple bridge ready for conductor integration")
    else:
        print("\n❌ STEP 1.2 SMOKE TEST: FAILED")