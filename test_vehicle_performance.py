#!/usr/bin/env python3
"""
Diagnostic script to test vehicle performance database integration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_vehicle_performance_service():
    """Test the vehicle performance service"""
    print("🔧 Testing Vehicle Performance Service...")
    
    try:
        from world.arknet_transit_simulator.services.vehicle_performance import VehiclePerformanceService, VehiclePerformanceCharacteristics
        
        print(f"✅ Service import successful")
        print(f"📊 Database available: {VehiclePerformanceService.is_database_available()}")
        
        # Test lookup for ZR400
        print(f"\n🔍 Looking up performance for ZR400...")
        performance = VehiclePerformanceService.get_performance_by_reg_code("ZR400")
        
        print(f"📈 Performance characteristics:")
        print(f"  Max Speed: {performance.max_speed_kmh} km/h ({performance.max_speed_mps:.2f} m/s)")
        print(f"  Acceleration: {performance.acceleration_mps2} m/s²")
        print(f"  Braking: {performance.braking_mps2} m/s²")
        print(f"  Eco Mode: {performance.eco_mode}")
        print(f"  Profile: {performance.performance_profile}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing performance service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_physics_model_creation():
    """Test physics model creation with vehicle reg code"""
    print(f"\n🧪 Testing Physics Model Creation...")
    
    try:
        from world.arknet_transit_simulator.vehicle.physics.physics_speed_model import PhysicsSpeedModel
        
        # Test route coordinates (simple straight line)
        test_coords = [
            [-59.636900, 13.319443],  # Start
            [-59.637000, 13.319450],  # Middle  
            [-59.637100, 13.319460]   # End
        ]
        
        print(f"🚗 Creating physics model for ZR400...")
        model = PhysicsSpeedModel(
            route_coords=test_coords,
            target_speed_mps=25.0/3.6,
            dt=0.5,
            vehicle_reg_code="ZR400"
        )
        
        print(f"✅ Physics model created successfully")
        print(f"📊 Model performance: {model.performance}")
        
        # Test a few updates
        print(f"\n⏱️ Testing model updates...")
        for i in range(3):
            result = model.update()
            print(f"  Step {i+1}: velocity={result.get('velocity_mps', 0):.2f} m/s, phase={result.get('phase', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing physics model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Vehicle Performance Diagnostic Test")
    print("=" * 50)
    
    success1 = test_vehicle_performance_service()
    success2 = test_physics_model_creation()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All tests passed! Database integration should be working.")
    else:
        print("❌ Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure the fleet manager database is running")
        print("2. Check that ZR400 vehicle exists in database")
        print("3. Verify database migration was applied successfully")