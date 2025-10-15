"""Test that Conductor requires capacity parameter"""
from arknet_transit_simulator.vehicle.conductor import Conductor

def test_capacity_required():
    """Verify capacity is required"""
    print("🔍 Test: Conductor without capacity should fail...")
    
    try:
        # This should fail - missing required parameter
        conductor = Conductor(
            conductor_id="TEST",
            conductor_name="Test",
            vehicle_id="TEST_VEH"
            # Missing: capacity
        )
        print("❌ FAILED: Conductor created without capacity!")
        return False
    except TypeError as e:
        print(f"✅ SUCCESS: Conductor rejected (as expected)")
        print(f"   Error: {e}")
        return True

def test_capacity_provided():
    """Verify conductor works with capacity"""
    print("\n🔍 Test: Conductor with capacity=16...")
    
    try:
        conductor = Conductor(
            conductor_id="TEST",
            conductor_name="Test",
            vehicle_id="TEST_VEH",
            capacity=16  # Explicit capacity
        )
        print(f"✅ SUCCESS: Conductor created with capacity={conductor.capacity}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    test1 = test_capacity_required()
    test2 = test_capacity_provided()
    
    if test1 and test2:
        print("\n✅ Step 2 Complete: Conductor requires capacity parameter (no default)")
    else:
        print("\n❌ Step 2 Failed")
