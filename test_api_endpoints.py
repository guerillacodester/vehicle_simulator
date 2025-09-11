#!/usr/bin/env python3
"""
API Endpoints Test Suite
------------------------
Comprehensive test of all FleetDataProvider API endpoints to ensure they work correctly.
Run this script when the Fleet Manager API is available.
"""

import sys
import time
import traceback
from typing import Dict, Any

# Add current directory to path
sys.path.append('.')

from world.vehicle_simulator.providers.data_provider import FleetDataProvider


def test_api_endpoint(provider: FleetDataProvider, endpoint_name: str, method_call) -> Dict[str, Any]:
    """Test a single API endpoint and return results"""
    print(f"\n🔍 Testing {endpoint_name}...")
    
    try:
        start_time = time.time()
        result = method_call()
        end_time = time.time()
        
        duration = end_time - start_time
        
        if isinstance(result, list):
            status = "✅ SUCCESS"
            details = f"Returned {len(result)} items in {duration:.2f}s"
            if result:
                details += f" (first item keys: {list(result[0].keys()) if isinstance(result[0], dict) else 'N/A'})"
        elif isinstance(result, dict):
            status = "✅ SUCCESS"
            details = f"Returned dict with {len(result)} keys in {duration:.2f}s (keys: {list(result.keys())})"
        else:
            status = "⚠️  UNEXPECTED"
            details = f"Returned {type(result)} in {duration:.2f}s"
            
        print(f"   {status}: {details}")
        
        return {
            'endpoint': endpoint_name,
            'status': 'success',
            'duration': duration,
            'result_type': type(result).__name__,
            'result_size': len(result) if hasattr(result, '__len__') else 'N/A',
            'details': details
        }
        
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        return {
            'endpoint': endpoint_name,
            'status': 'failed',
            'error': str(e),
            'details': f"Exception: {type(e).__name__}"
        }


def main():
    """Run comprehensive API endpoint tests"""
    print("=" * 60)
    print("FleetDataProvider API Endpoints Test Suite")
    print("=" * 60)
    
    try:
        # Initialize provider
        print("\n🚀 Initializing FleetDataProvider...")
        provider = FleetDataProvider(server_url='http://localhost:8000')
        
        # Wait for API connection
        print("⏳ Waiting for API connection...")
        for i in range(10):
            if provider.is_api_available():
                break
            time.sleep(1)
            print(f"   Waiting... ({i+1}/10)")
        
        if not provider.is_api_available():
            print("❌ API not available - cannot run tests")
            print("   Make sure Fleet Manager API is running on http://localhost:8000")
            return
            
        print("✅ API connection established")
        
        # Test results storage
        test_results = []
        
        # ==================== CORE DATA TESTS ====================
        
        print("\n" + "="*40)
        print("CORE DATA ENDPOINTS")
        print("="*40)
        
        # Test vehicles endpoint
        test_results.append(test_api_endpoint(
            provider, "get_vehicles()", 
            lambda: provider.get_vehicles()
        ))
        
        # Test routes endpoint
        test_results.append(test_api_endpoint(
            provider, "get_routes()", 
            lambda: provider.get_routes()
        ))
        
        # Test route coordinates (if routes exist)
        routes = provider.get_routes()
        if routes:
            first_route = list(routes.keys())[0]
            test_results.append(test_api_endpoint(
                provider, f"get_route_coordinates('{first_route}')", 
                lambda: provider.get_route_coordinates(first_route)
            ))
        
        # ==================== SCHEDULE DATA TESTS ====================
        
        print("\n" + "="*40)
        print("SCHEDULE DATA ENDPOINTS")
        print("="*40)
        
        test_results.append(test_api_endpoint(
            provider, "get_timetables()", 
            lambda: provider.get_timetables()
        ))
        
        test_results.append(test_api_endpoint(
            provider, "get_schedules()", 
            lambda: provider.get_schedules()
        ))
        
        # ==================== OPTIONAL DATA TESTS ====================
        
        print("\n" + "="*40)
        print("OPTIONAL DATA ENDPOINTS")
        print("="*40)
        
        test_results.append(test_api_endpoint(
            provider, "get_drivers()", 
            lambda: provider.get_drivers()
        ))
        
        test_results.append(test_api_endpoint(
            provider, "get_services()", 
            lambda: provider.get_services()
        ))
        
        test_results.append(test_api_endpoint(
            provider, "get_depots()", 
            lambda: provider.get_depots()
        ))
        
        # ==================== COMPREHENSIVE DATA TEST ====================
        
        print("\n" + "="*40)
        print("COMPREHENSIVE DATA TEST")
        print("="*40)
        
        test_results.append(test_api_endpoint(
            provider, "get_all_fleet_data()", 
            lambda: provider.get_all_fleet_data()
        ))
        
        # ==================== RESULTS SUMMARY ====================
        
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        total_tests = len(test_results)
        successful_tests = len([r for r in test_results if r['status'] == 'success'])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in test_results:
                if result['status'] == 'failed':
                    print(f"   • {result['endpoint']}: {result.get('error', 'Unknown error')}")
        
        if successful_tests > 0:
            print(f"\n✅ SUCCESSFUL TESTS:")
            for result in test_results:
                if result['status'] == 'success':
                    print(f"   • {result['endpoint']}: {result.get('details', 'Success')}")
        
        print(f"\n🎯 API Status: {'HEALTHY' if failed_tests == 0 else 'ISSUES DETECTED'}")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        traceback.print_exc()
        
    finally:
        # Clean up
        try:
            if 'provider' in locals():
                provider.__del__()
        except:
            pass


if __name__ == "__main__":
    main()