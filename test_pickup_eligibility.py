"""
Advanced LocationAwareCommuter Validation Test
==============================================

Comprehensive test of pickup eligibility, configuration system,
and priority-based behavior.
"""

import sys
import os
from datetime import datetime

# Add the project path
sys.path.append(os.path.dirname(__file__))


def test_pickup_eligibility_comprehensive():
    """Test the advanced pickup eligibility system."""
    print("🧪 COMPREHENSIVE TEST: Pickup Eligibility System")
    print("=" * 60)
    
    try:
        from commuter_service.location_aware_commuter import LocationAwareCommuter, CommuterState
        from commuter_service.commuter_config import CommuterBehaviorConfig, set_commuter_config
        
        # Create custom config for testing
        test_config = CommuterBehaviorConfig()
        test_config.max_walking_distance_high_priority = 150   # Shorter for high priority
        test_config.max_walking_distance_medium_priority = 250  # Medium distance
        set_commuter_config(test_config)
        
        print("Test 1: Priority-Based Walking Distance...")
        
        # High priority commuter (education)
        high_priority = LocationAwareCommuter(
            person_id="HIGH_001",
            spawn_location=(13.0827, -59.6130),
            destination_location=(13.1135, -59.6333),
            trip_purpose="education",
            priority=0.8,  # High priority
            area_type="suburban"
        )
        
        # Low priority commuter (leisure)
        low_priority = LocationAwareCommuter(
            person_id="LOW_001", 
            spawn_location=(13.0827, -59.6130),
            destination_location=(13.1135, -59.6333),
            trip_purpose="leisure",
            priority=0.2,  # Low priority
            area_type="suburban"
        )
        
        print(f"   High priority max walk: {high_priority.max_walking_distance_m}m")
        print(f"   Low priority max walk: {low_priority.max_walking_distance_m}m")
        assert high_priority.max_walking_distance_m < low_priority.max_walking_distance_m
        print("✅ Priority affects walking distance correctly")
        
        print("\nTest 2: Route Pickup Eligibility...")
        
        # Create a sample route (Bridgetown to UWI)
        sample_route = [
            (13.0827, -59.6130),  # Bridgetown
            (13.0900, -59.6200),  # Intermediate point 1
            (13.1000, -59.6250),  # Intermediate point 2
            (13.1135, -59.6333)   # UWI
        ]
        
        vehicle_position = (13.0850, -59.6180)  # Vehicle current position
        
        # Test commuter close to route
        close_commuter = LocationAwareCommuter(
            person_id="CLOSE_001",
            spawn_location=(13.0895, -59.6195),  # Very close to route point
            destination_location=(13.1135, -59.6333),
            trip_purpose="work",
            priority=0.7
        )
        
        eligibility = close_commuter.evaluate_pickup_eligibility(
            vehicle_position=vehicle_position,
            vehicle_route=sample_route,
            available_seats=3
        )
        
        print(f"   Walking distance: {eligibility.walking_distance_m:.0f}m")
        print(f"   Direction compatible: {eligibility.direction_compatible}")
        print(f"   Qualified: {eligibility.is_qualified}")
        print(f"   Priority score: {eligibility.priority_score:.2f}")
        print(f"   Reasons: {eligibility.reasons}")
        
        assert eligibility.is_qualified, "Close commuter should be qualified"
        assert eligibility.walking_distance_m < 100, "Should be very close to route"
        print("✅ Close commuter correctly qualified for pickup")
        
        print("\nTest 3: Reject Far Commuter...")
        
        # Test commuter too far from route
        far_commuter = LocationAwareCommuter(
            person_id="FAR_001",
            spawn_location=(13.0500, -59.6000),  # Far from route
            destination_location=(13.1135, -59.6333),
            trip_purpose="personal",
            priority=0.5
        )
        
        far_eligibility = far_commuter.evaluate_pickup_eligibility(
            vehicle_position=vehicle_position,
            vehicle_route=sample_route,
            available_seats=3
        )
        
        print(f"   Walking distance: {far_eligibility.walking_distance_m:.0f}m")
        print(f"   Qualified: {far_eligibility.is_qualified}")
        print(f"   Reasons: {far_eligibility.reasons}")
        
        assert not far_eligibility.is_qualified, "Far commuter should be rejected"
        assert far_eligibility.walking_distance_m > far_commuter.max_walking_distance_m
        print("✅ Far commuter correctly rejected")
        
        print("\nTest 4: Area Type Configuration...")
        
        # Test different area types
        urban_commuter = LocationAwareCommuter(
            person_id="URB_001",
            spawn_location=(13.0827, -59.6130),
            destination_location=(13.0830, -59.6135),  # Very close destination
            trip_purpose="personal",
            priority=0.5,
            area_type="urban"  # Precise urban stops
        )
        
        rural_commuter = LocationAwareCommuter(
            person_id="RUR_001", 
            spawn_location=(13.0827, -59.6130),
            destination_location=(13.0830, -59.6135),
            trip_purpose="personal",
            priority=0.5,
            area_type="rural"  # Flexible rural stops
        )
        
        print(f"   Urban disembark threshold: {urban_commuter.disembark_threshold_m}m")
        print(f"   Rural disembark threshold: {rural_commuter.disembark_threshold_m}m")
        assert rural_commuter.disembark_threshold_m > urban_commuter.disembark_threshold_m
        print("✅ Area type affects disembark thresholds correctly")
        
        print("\nTest 5: Priority Explanations...")
        
        priorities_to_test = [0.1, 0.5, 0.8, 0.95]
        for priority in priorities_to_test:
            test_commuter = LocationAwareCommuter(
                person_id=f"PRI_{priority}",
                spawn_location=(13.0827, -59.6130),
                destination_location=(13.1135, -59.6333), 
                trip_purpose="test",
                priority=priority
            )
            print(f"   Priority {priority}: {test_commuter.priority_explanation}")
        
        print("✅ Priority explanations working")
        
        print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("\n📊 CONFIGURATION SUMMARY:")
        print(f"   High priority max walk: {test_config.max_walking_distance_high_priority}m")
        print(f"   Medium priority max walk: {test_config.max_walking_distance_medium_priority}m") 
        print(f"   Urban disembark threshold: {test_config.disembark_threshold_urban}m")
        print(f"   Rural disembark threshold: {test_config.disembark_threshold_rural}m")
        
        return True
        
    except Exception as e:
        print(f"❌ COMPREHENSIVE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pickup_eligibility_comprehensive()
    if success:
        print("\n🚀 STEP 1.1 VALIDATION: COMPLETE")
        print("✅ LocationAwareCommuter ready for integration")
        print("✅ Configuration system working")
        print("✅ Priority-based behavior validated")
        print("✅ Pickup eligibility system operational")
    else:
        print("\n❌ VALIDATION FAILED - Check implementation")