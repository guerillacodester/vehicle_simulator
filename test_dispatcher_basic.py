#!/usr/bin/env python3
"""
Dispatcher Smoke Test
--------------------
Basic functionality test for the new Dispatcher class.
"""

import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from world.vehicle_simulator.core.dispatcher import Dispatcher, VehicleStatus
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer

def test_dispatcher_basic_functionality():
    """Test basic Dispatcher functionality"""
    print("🧪 DISPATCHER SMOKE TEST")
    print("=" * 50)
    
    try:
        # Test 1: Dispatcher creation
        print("📋 Testing Dispatcher creation...")
        dispatcher = Dispatcher()
        status = dispatcher.get_dispatcher_status()
        assert status['running'] == False
        assert status['vehicles_registered'] == 0
        print("✅ Dispatcher created successfully")
        
        # Test 2: Start/Stop operations
        print("📋 Testing start/stop operations...")
        dispatcher.start()
        assert dispatcher.running == True
        dispatcher.stop()
        assert dispatcher.running == False
        print("✅ Start/stop operations working")
        
        # Test 3: Vehicle registration
        print("📋 Testing vehicle registration...")
        mock_vehicle_handler = {
            '_engine': None,
            '_navigator': None,
            '_gps': None,
            'config': {'active': True},
            'vehicle_id': 'TEST_VEHICLE'
        }
        
        success = dispatcher.register_vehicle('TEST_VEHICLE', mock_vehicle_handler)
        assert success == True
        assert 'TEST_VEHICLE' in dispatcher.vehicles
        print("✅ Vehicle registration working")
        
        # Test 4: Route loading (should fail gracefully without routes)
        print("📋 Testing route loading...")
        coordinates = dispatcher.load_route('nonexistent_route')
        assert coordinates is None  # Expected to fail gracefully
        print("✅ Route loading handles missing routes gracefully")
        
        # Test 5: Assignment queuing (should fail due to missing route)
        print("📋 Testing assignment queuing...")
        success = dispatcher.queue_assignment('TEST_VEHICLE', 'nonexistent_route')
        assert success == False  # Expected to fail due to missing route
        print("✅ Assignment queuing handles missing routes gracefully")
        
        # Test 6: Status reporting
        print("📋 Testing status reporting...")
        status = dispatcher.get_dispatcher_status()
        assert status['vehicles_registered'] == 1
        assert status['assignments_queued'] == 0
        
        vehicle_status = dispatcher.get_vehicle_status('TEST_VEHICLE')
        assert vehicle_status is not None
        assert vehicle_status['vehicle_id'] == 'TEST_VEHICLE'
        print("✅ Status reporting working")
        
        # Test 7: Vehicle unregistration
        print("📋 Testing vehicle unregistration...")
        success = dispatcher.unregister_vehicle('TEST_VEHICLE')
        assert success == True
        assert 'TEST_VEHICLE' not in dispatcher.vehicles
        print("✅ Vehicle unregistration working")
        
        print("\n🎉 ALL DISPATCHER TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ DISPATCHER TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dispatcher_basic_functionality()
    sys.exit(0 if success else 1)