#!/usr/bin/env python3
"""
Test 1: Depot Manager Initialization
=====================================
This test verifies that the depot manager can be initialized successfully
and is properly connected to the Fleet Manager API.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher

async def test_depot_manager_init():
    """Test depot manager initialization only"""
    
    print("🏭 Test 1: Depot Manager Initialization")
    print("=" * 50)
    print("📋 This test verifies:")
    print("   • Depot manager can be created")
    print("   • Connection to Fleet Manager API is established")
    print("   • Depot manager reports as 'onsite' successfully")
    print()
    
    try:
        print("🔌 Step 1: Creating depot manager...")
        depot_manager = DepotManager("TestDepot")
        print("   ✅ Depot manager instance created")
        
        print("\n🔗 Step 2: Creating and setting dispatcher...")
        dispatcher = Dispatcher("TestFleetDispatcher", "http://localhost:8000")
        depot_manager.set_dispatcher(dispatcher)
        print("   ✅ Dispatcher created and assigned to depot manager")
        
        print("\n🔗 Step 3: Initializing depot manager (connecting to API)...")
        await depot_manager.initialize()
        print("   ✅ Depot manager initialized successfully")
        
        print("\n📊 Step 4: Checking depot manager status...")
        # Check if dispatcher is available
        if hasattr(depot_manager, 'dispatcher') and depot_manager.dispatcher:
            print("   ✅ Fleet dispatcher is connected")
            print(f"   📡 Dispatcher API base URL: {depot_manager.dispatcher.api_base_url}")
        else:
            print("   ❌ Fleet dispatcher is not available")
            return False
            
        print("\n🏭 Step 5: Verifying depot manager is 'onsite'...")
        # Check if depot is properly initialized and in OPEN state
        if depot_manager.initialized and str(depot_manager.current_state) == "DepotState.OPEN":
            print("   ✅ Depot manager is onsite and ready")
            print(f"   🏢 Depot state: {depot_manager.current_state}")
        else:
            print(f"   ❌ Depot manager not properly onsite - State: {depot_manager.current_state}")
            return False
        
        print("\n✅ SUCCESS: Depot manager initialization test passed!")
        print("   🎯 Depot manager is properly initialized and onsite")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: Depot manager initialization failed")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_depot_manager_init())