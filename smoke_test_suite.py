#!/usr/bin/env python3
"""
Smoke Test Suite for Vehicle Simulator Refactoring
--------------------------------------------------
Comprehensive smoke tests to ensure no functionality breaks during 
the Navigator->VehicleDriver and VehiclesDepot->DepotManager refactoring.

This test suite validates:
1. Core component initialization
2. Telemetry pipeline integrity  
3. Database connectivity
4. Vehicle lifecycle operations
5. GPS transmission functionality
"""

import sys
import os
import time
import threading
import traceback
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'world'))

# Test imports - these should all work
try:
    from world.vehicle_simulator.core.depot_manager import DepotManager
    from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
    from world.vehicle_simulator.vehicle.engine.engine_block import Engine
    from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
    from world.vehicle_simulator.providers.data_provider import FleetDataProvider
    print("✅ All core imports successful")
except ImportError as e:
    print(f"❌ CRITICAL: Import failure - {e}")
    sys.exit(1)

class SmokeTestSuite:
    def __init__(self):
        self.test_results = {}
        self.depot = None
        self.start_time = datetime.now()
        
    def run_all_tests(self):
        """Run complete smoke test suite"""
        print("🧪 VEHICLE SIMULATOR SMOKE TEST SUITE")
        print("=" * 50)
        print(f"Started: {self.start_time}")
        print()
        
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Depot Initialization", self.test_depot_initialization),
            ("Vehicle Creation", self.test_vehicle_creation),
            ("VehicleDriver Functionality", self.test_navigator_functionality),
            ("Engine Operations", self.test_engine_operations),
            ("GPS Device Operations", self.test_gps_device_operations),
            ("Telemetry Pipeline", self.test_telemetry_pipeline),
            ("Full System Integration", self.test_full_system_integration),
            ("Graceful Shutdown", self.test_graceful_shutdown)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"🧪 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    print(f"✅ PASS: {test_name}")
                    self.test_results[test_name] = "PASS"
                    passed += 1
                else:
                    print(f"❌ FAIL: {test_name}")
                    self.test_results[test_name] = "FAIL"
                    failed += 1
            except Exception as e:
                print(f"💥 ERROR: {test_name} - {str(e)}")
                print(traceback.format_exc())
                self.test_results[test_name] = f"ERROR: {str(e)}"
                failed += 1
            print()
        
        # Final report
        self.print_final_report(passed, failed)
        return failed == 0
    
    def test_database_connection(self):
        """Test database and API connectivity"""
        try:
            # Test data provider initialization
            data_provider = FleetDataProvider("http://localhost:8000")
            
            # Check API status (don't require connection for smoke test)
            api_status = data_provider.get_api_status()
            print(f"   API Status: {api_status}")
            
            return True
        except Exception as e:
            print(f"   Database connection error: {e}")
            return False
    
    def test_depot_initialization(self):
        """Test depot initialization without starting operations"""
        try:
            self.depot = DepotManager(tick_time=1.0)
            
            # Check basic properties
            assert hasattr(self.depot, 'vehicles')
            assert hasattr(self.depot, 'data_provider')
            assert hasattr(self.depot, 'scheduler')
            
            print(f"   Vehicles loaded: {len(self.depot.vehicles)}")
            print(f"   Routes available: {len(self.depot.routes)}")
            
            return True
        except Exception as e:
            print(f"   Depot initialization error: {e}")
            return False
    
    def test_vehicle_creation(self):
        """Test vehicle component creation"""
        if not self.depot:
            print("   Depot not initialized")
            return False
        
        try:
            vehicle_count = len(self.depot.vehicles)
            if vehicle_count == 0:
                print("   No vehicles to test")
                return True
            
            # Test first vehicle components
            first_vehicle_id = list(self.depot.vehicles.keys())[0]
            vehicle_handler = self.depot.vehicles[first_vehicle_id]
            
            # Check required components
            assert '_engine' in vehicle_handler
            assert '_gps' in vehicle_handler
            assert 'config' in vehicle_handler
            
            # VehicleDriver might be None if no route assigned
            navigator = vehicle_handler.get('_navigator')
            print(f"   Vehicle {first_vehicle_id}: Engine={vehicle_handler['_engine'] is not None}, "
                  f"GPS={vehicle_handler['_gps'] is not None}, VehicleDriver={navigator is not None}")
            
            return True
        except Exception as e:
            print(f"   Vehicle creation error: {e}")
            return False
    
    def test_navigator_functionality(self):
        """Test vehicle driver initialization and basic functionality"""
        try:
            # Test navigator with sample route
            test_route = [
                (-59.6464, 13.2810),  # Bridgetown
                (-59.6400, 13.2850),  # Sample point
                (-59.6350, 13.2900)   # Sample endpoint
            ]
            
            navigator = VehicleDriver(
                vehicle_id="SMOKE_TEST",
                route_coordinates=test_route,
                tick_time=0.1,
                mode="geodesic",
                direction="outbound"
            )
            
            # Check properties
            assert navigator.vehicle_id == "SMOKE_TEST"
            assert len(navigator.route) == 3
            assert navigator.total_route_length > 0
            
            print(f"   VehicleDriver created: route_length={navigator.total_route_length:.3f}km")
            
            return True
        except Exception as e:
            print(f"   Navigator functionality error: {e}")
            return False
    
    def test_engine_operations(self):
        """Test engine initialization and basic operations"""
        if not self.depot:
            return False
        
        try:
            vehicles_with_engines = [v for v in self.depot.vehicles.values() if v.get('_engine')]
            if not vehicles_with_engines:
                print("   No vehicles with engines to test")
                return True
            
            # Test first engine
            vehicle_handler = vehicles_with_engines[0]
            engine = vehicle_handler['_engine']
            
            # Check engine properties
            assert hasattr(engine, 'on')
            assert hasattr(engine, 'off')
            assert hasattr(engine, '_running')
            
            print(f"   Engine test: vehicle_id={engine.vehicle_id}, running={engine._running}")
            
            return True
        except Exception as e:
            print(f"   Engine operations error: {e}")
            return False
    
    def test_gps_device_operations(self):
        """Test GPS device initialization and basic operations"""
        if not self.depot:
            return False
        
        try:
            vehicles_with_gps = [v for v in self.depot.vehicles.values() if v.get('_gps')]
            if not vehicles_with_gps:
                print("   No vehicles with GPS devices to test")
                return True
            
            # Test first GPS device
            vehicle_handler = vehicles_with_gps[0]
            gps_device = vehicle_handler['_gps']
            
            # Check GPS device properties
            assert hasattr(gps_device, 'on')
            assert hasattr(gps_device, 'off')
            assert hasattr(gps_device, 'device_id')
            
            print(f"   GPS Device test: device_id={gps_device.device_id}")
            
            return True
        except Exception as e:
            print(f"   GPS device operations error: {e}")
            return False
    
    def test_telemetry_pipeline(self):
        """Test telemetry data flow"""
        try:
            # This is a basic connectivity test
            # Full telemetry testing requires running system
            from world.vehicle_simulator.vehicle.driver.navigation.telemetry_buffer import TelemetryBuffer
            from world.vehicle_simulator.vehicle.gps_device.rxtx_buffer import RxTxBuffer
            
            # Test buffer creation
            telemetry_buffer = TelemetryBuffer()
            rxtx_buffer = RxTxBuffer()  # Remove device_id parameter - not supported
            
            assert hasattr(telemetry_buffer, 'write')
            assert hasattr(rxtx_buffer, 'write')
            
            print("   Telemetry buffers created successfully")
            
            return True
        except Exception as e:
            print(f"   Telemetry pipeline error: {e}")
            return False
    
    def test_full_system_integration(self):
        """Test complete system startup and basic operations"""
        if not self.depot:
            return False
        
        try:
            # Test depot status before starting
            status = self.depot.get_fleet_status()
            assert 'depot_running' in status
            assert 'total_vehicles' in status
            
            print(f"   Fleet status: {status['total_vehicles']} vehicles, "
                  f"API available: {status.get('api_available', False)}")
            
            # Test individual vehicle status
            if self.depot.vehicles:
                first_vehicle_id = list(self.depot.vehicles.keys())[0]
                vehicle_status = self.depot.get_vehicle_status(first_vehicle_id)
                assert 'vehicle_id' in vehicle_status
                print(f"   Vehicle status test: {first_vehicle_id} status retrieved")
            
            return True
        except Exception as e:
            print(f"   Full system integration error: {e}")
            return False
    
    def test_graceful_shutdown(self):
        """Test system shutdown procedures"""
        if not self.depot:
            return True
        
        try:
            # Test stop functionality
            self.depot.stop()
            print("   Depot stopped successfully")
            
            return True
        except Exception as e:
            print(f"   Graceful shutdown error: {e}")
            return False
    
    def print_final_report(self, passed, failed):
        """Print final test report"""
        total = passed + failed
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("=" * 50)
        print("🧪 SMOKE TEST RESULTS")
        print("=" * 50)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
        print()
        
        if failed == 0:
            print("🎉 ALL SMOKE TESTS PASSED!")
            print("✅ System is ready for refactoring")
        else:
            print("❌ SMOKE TESTS FAILED!")
            print("🚨 Do not proceed with refactoring until issues are resolved")
            print()
            print("Failed Tests:")
            for test_name, result in self.test_results.items():
                if result != "PASS":
                    print(f"   - {test_name}: {result}")
        
        print("=" * 50)

def run_smoke_tests():
    """Entry point for smoke tests"""
    suite = SmokeTestSuite()
    success = suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
