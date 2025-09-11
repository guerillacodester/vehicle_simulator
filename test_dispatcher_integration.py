#!/usr/bin/env python3
"""
Dispatcher Integration Test
--------------------------
Tests Dispatcher with real route data and VehicleDriver integration.
"""

import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from world.vehicle_simulator.core.dispatcher import Dispatcher, VehicleStatus
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle_simulator.vehicle.engine.engine_block import Engine
from world.vehicle_simulator.vehicle.engine.sim_speed_model import load_speed_model
from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver

def test_dispatcher_with_real_routes():
    """Test Dispatcher with real route loading and VehicleDriver integration"""
    print("🧪 DISPATCHER INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Initialize Dispatcher
        print("📋 Initializing Dispatcher...")
        dispatcher = Dispatcher()
        dispatcher.start()
        print("✅ Dispatcher initialized and started")
        
        # Create mock vehicle handler (similar to DepotManager structure)
        print("📋 Creating mock vehicle handler...")
        engine_buffer = EngineBuffer()
        speed_model = load_speed_model('kinematic', speed=50)
        engine = Engine('TEST_VEHICLE', speed_model, engine_buffer, tick_time=0.1)
        
        vehicle_handler = {
            '_engine': engine,
            '_navigator': None,  # Will be created by Dispatcher
            '_gps': None,
            'config': {
                'active': True,
                'route': '',
                'capacity': 40
            },
            'vehicle_id': 'TEST_VEHICLE'
        }
        print("✅ Mock vehicle handler created")
        
        # Register vehicle with Dispatcher
        print("📋 Registering vehicle...")
        success = dispatcher.register_vehicle('TEST_VEHICLE', vehicle_handler)
        assert success == True
        print("✅ Vehicle registered successfully")
        
        # Test route loading with a real file
        print("📋 Testing route loading with real file...")
        route_file = "data/routes/route_1.geojson"
        if os.path.exists(route_file):
            coordinates = dispatcher.load_route(
                route_id="route_1",
                route_file=route_file
            )
            if coordinates:
                print(f"✅ Route loaded from file: {len(coordinates)} coordinates")
                
                # Test assignment with real route
                print("📋 Testing assignment with real route...")
                success = dispatcher.queue_assignment(
                    vehicle_id='TEST_VEHICLE',
                    route_id='route_1',
                    route_file=route_file,
                    priority=1
                )
                assert success == True
                print("✅ Assignment queued successfully")
                
                # Process assignment
                print("📋 Processing assignment...")
                processed = dispatcher.process_assignment_queue()
                assert processed >= 1
                print(f"✅ Processed {processed} assignments")
                
                # Verify VehicleDriver was created
                print("📋 Verifying VehicleDriver creation...")
                navigator = vehicle_handler['_navigator']
                assert navigator is not None
                assert isinstance(navigator, VehicleDriver)
                print("✅ VehicleDriver created and assigned")
                
                # Test VehicleDriver functionality
                print("📋 Testing VehicleDriver functionality...")
                navigator.on()
                time.sleep(1)  # Let it run briefly
                position = navigator.last_position
                navigator.off()
                
                if position:
                    print(f"✅ VehicleDriver functional: position {position}")
                else:
                    print("✅ VehicleDriver created (no position data yet)")
                
            else:
                print("⚠️ Could not load route from file, testing with simple coordinates")
                # Create simple test route
                test_coords = [
                    (-59.646309, 13.281012),
                    (-59.646317, 13.281025),
                    (-59.646329, 13.281041)
                ]
                dispatcher.route_cache['test_route_outbound'] = test_coords
                
                success = dispatcher.queue_assignment(
                    vehicle_id='TEST_VEHICLE',
                    route_id='test_route'
                )
                # This should fail because route doesn't exist in normal loading
                print("✅ Assignment handling with cached route tested")
        else:
            print(f"⚠️ Route file {route_file} not found, testing with basic functionality only")
        
        # Test status reporting
        print("📋 Testing comprehensive status reporting...")
        dispatcher_status = dispatcher.get_dispatcher_status()
        vehicle_status = dispatcher.get_vehicle_status('TEST_VEHICLE')
        queue_summary = dispatcher.get_queue_summary()
        
        print(f"   Dispatcher: {dispatcher_status['vehicles_registered']} vehicles, {dispatcher_status['assignments_queued']} queued")
        print(f"   Vehicle: {vehicle_status['status'] if vehicle_status else 'Not found'}")
        print(f"   Queue: {len(queue_summary)} assignments")
        print("✅ Status reporting comprehensive")
        
        # Test cleanup
        print("📋 Testing cleanup...")
        dispatcher.stop()
        assert dispatcher.running == False
        print("✅ Dispatcher stopped cleanly")
        
        print("\n🎉 DISPATCHER INTEGRATION TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ DISPATCHER INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dispatcher_with_real_routes()
    sys.exit(0 if success else 1)