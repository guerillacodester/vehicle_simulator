"""
SMOKE TEST: Location-Aware Commuter
==================================
Test-Driven Development approach for Step 1.1

This smoke test defines the expected behavior BEFORE implementation.
"""

import sys
import os
import math
from datetime import datetime

# Add the project path
sys.path.append(os.path.dirname(__file__))

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance in meters between two points."""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def test_location_aware_commuter_smoke():
    """SMOKE TEST: Basic functionality that must work."""
    print("🧪 SMOKE TEST: Location-Aware Commuter")
    print("=" * 50)
    
    try:
        # Import the component we're about to create
        from commuter_service.location_aware_commuter import LocationAwareCommuter, CommuterState
        
        # Test 1: Basic creation
        print("Test 1: Basic Creation...")
        commuter = LocationAwareCommuter(
            person_id="TEST_001",
            spawn_location=(13.0827, -59.6130),  # Bridgetown, Barbados
            destination_location=(13.1135, -59.6333),  # University of West Indies
            trip_purpose="education",
            priority=0.8,  # High priority for education
            area_type="suburban",  # Suburban Barbados setting
            personality="standard"  # Normal patience level
        )
        assert commuter.person_id == "TEST_001"
        assert commuter.current_position == (13.0827, -59.6130)
        assert commuter.destination_position == (13.1135, -59.6333)
        print("✅ Creation successful")
        
        # Test 2: Distance calculation
        print("Test 2: Distance Calculation...")
        distance = commuter.distance_to_destination()
        expected_distance = haversine_distance(13.0827, -59.6130, 13.1135, -59.6333)
        assert abs(distance - expected_distance) < 10  # Within 10 meters
        print(f"✅ Distance: {distance:.0f}m (expected ~{expected_distance:.0f}m)")
        
        # Test 3: Not at destination initially
        print("Test 3: Destination Detection (Far)...")
        assert not commuter.is_at_destination()
        assert commuter.state == CommuterState.WAITING_TO_BOARD
        print("✅ Correctly not at destination")
        
        # Test 4: Move close to destination
        print("Test 4: Destination Detection (Near)...")
        commuter.update_position(13.1134, -59.6332)  # Very close to destination
        distance_close = commuter.distance_to_destination()
        print(f"   New distance: {distance_close:.0f}m")
        assert commuter.is_at_destination()  # Should be within threshold
        print("✅ Correctly detected at destination")
        
        # Test 5: State management
        print("Test 5: State Management...")
        commuter.board_vehicle()
        assert commuter.state == CommuterState.ONBOARD
        
        commuter.request_disembark()
        assert commuter.state == CommuterState.REQUESTING_DISEMBARK
        print("✅ State transitions working")
        
        print("\n🎉 ALL SMOKE TESTS PASSED!")
        return True
        
    except ImportError as e:
        print(f"❌ EXPECTED: Module not yet implemented ({e})")
        return False
    except Exception as e:
        print(f"❌ SMOKE TEST FAILED: {e}")
        return False


if __name__ == "__main__":
    success = test_location_aware_commuter_smoke()
    if success:
        print("\n✅ READY FOR NEXT STEP")
    else:
        print("\n⚠️  IMPLEMENTATION NEEDED")