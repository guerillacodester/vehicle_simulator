#!/usr/bin/env python3
"""
DepotManager with Dispatcher Test
---------------------------------
Tests DepotManager with Dispatcher integration enabled.
"""

import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def test_depot_manager_with_dispatcher():
    """Test DepotManager with Dispatcher enabled"""
    print("🧪 DEPOT MANAGER + DISPATCHER INTEGRATION TEST")
    print("=" * 70)
    
    try:
        from world.vehicle_simulator.core.depot_manager import DepotManager
        
        # Test 1: Create DepotManager with Dispatcher disabled (default)
        print("📋 Testing DepotManager with Dispatcher disabled (default)...")
        depot_default = DepotManager(enable_dispatcher=False)
        assert depot_default.enable_dispatcher == False
        assert depot_default.dispatcher is None
        print("✅ DepotManager created with Dispatcher disabled")
        
        # Test 2: Create DepotManager with Dispatcher enabled
        print("📋 Testing DepotManager with Dispatcher enabled...")
        depot_with_dispatcher = DepotManager(enable_dispatcher=True)
        assert depot_with_dispatcher.enable_dispatcher == True
        assert depot_with_dispatcher.dispatcher is not None
        print("✅ DepotManager created with Dispatcher enabled")
        
        # Test 3: Check fleet status includes dispatcher info
        print("📋 Testing fleet status with dispatcher info...")
        status = depot_with_dispatcher.get_fleet_status()
        assert 'dispatcher_enabled' in status
        assert 'dispatcher_running' in status
        assert 'dispatcher_status' in status
        assert status['dispatcher_enabled'] == True
        
        # Check dispatcher-specific status
        dispatcher_status = status['dispatcher_status']
        assert dispatcher_status is not None
        assert 'running' in dispatcher_status
        assert 'vehicles_registered' in dispatcher_status
        print("✅ Fleet status includes dispatcher information")
        
        # Test 4: Start/Stop operations with dispatcher
        print("📋 Testing start/stop operations with dispatcher...")
        depot_with_dispatcher.start()
        assert depot_with_dispatcher.running == True
        
        status_after_start = depot_with_dispatcher.get_fleet_status()
        # Dispatcher should be running after start
        
        depot_with_dispatcher.stop()
        assert depot_with_dispatcher.running == False
        print("✅ Start/stop operations work with dispatcher")
        
        # Test 5: Verify no interference with default behavior
        print("📋 Testing no interference with default behavior...")
        depot_default.start()
        status_default = depot_default.get_fleet_status()
        assert status_default['dispatcher_enabled'] == False
        assert status_default['dispatcher_running'] == False
        assert status_default['dispatcher_status'] is None
        depot_default.stop()
        print("✅ Default behavior unchanged")
        
        print("\n🎉 DEPOT MANAGER + DISPATCHER INTEGRATION TEST PASSED!")
        print("✅ Dispatcher integration working correctly")
        print("✅ Backward compatibility maintained")
        print("✅ Optional feature works as expected")
        return True
        
    except Exception as e:
        print(f"\n❌ DEPOT MANAGER + DISPATCHER TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_depot_manager_with_dispatcher()
    sys.exit(0 if success else 1)