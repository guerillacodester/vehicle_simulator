"""Test full integration: Fetch capacity from Strapi → Create Conductor"""
import asyncio
from arknet_transit_simulator.services.vehicle_performance import VehiclePerformanceService
from arknet_transit_simulator.vehicle.conductor import Conductor

async def test_integration():
    """Test fetching vehicle capacity and creating conductor"""
    print("🔍 Integration Test: Strapi → VehiclePerformanceService → Conductor\n")
    
    vehicle_reg_code = "ZR102"
    
    try:
        # Step 1: Fetch vehicle performance from Strapi
        print(f"1. Fetching vehicle '{vehicle_reg_code}' from Strapi API...")
        perf = await VehiclePerformanceService.get_performance_async(vehicle_reg_code)
        print(f"   ✅ Found: capacity={perf.capacity}, max_speed={perf.max_speed_kmh} km/h")
        
        # Step 2: Create conductor with database capacity
        print(f"\n2. Creating Conductor with capacity from database...")
        conductor = Conductor(
            conductor_id="COND_001",
            conductor_name="Test Conductor",
            vehicle_id=vehicle_reg_code,
            capacity=perf.capacity,  # From database!
            assigned_route_id="1A"
        )
        print(f"   ✅ Conductor created:")
        print(f"      Vehicle: {conductor.vehicle_id}")
        print(f"      Capacity: {conductor.capacity} passengers")
        print(f"      Seats Available: {conductor.seats_available}")
        
        # Step 3: Verify no hardcoded values
        print(f"\n3. Verification:")
        assert conductor.capacity == perf.capacity, "Capacity mismatch!"
        assert conductor.capacity == 16, "Expected capacity=16 from database"
        assert conductor.capacity != 40, "Should NOT be hardcoded 40"
        assert conductor.capacity != 30, "Should NOT be hardcoded 30"
        print(f"   ✅ Capacity matches database (not hardcoded)")
        
        print(f"\n✅ Integration Test PASSED!")
        print(f"   Database capacity (16) → Conductor capacity (16)")
        print(f"   No hardcoded defaults used")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    if success:
        print("\n" + "="*70)
        print("✅ PHASE 1 COMPLETE: Vehicle Capacity Flow from Database")
        print("="*70)
        print("✓ VehiclePerformanceService fetches capacity from Strapi")
        print("✓ Conductor requires capacity (no hardcoded default)")
        print("✓ Integration: Database → Service → Conductor")
        print("\nNext: Phase 2 - Integrate conductor with passenger database")
    else:
        print("\n❌ Phase 1 incomplete")
