#!/usr/bin/env python3
"""
Test script for public API endpoints
Tests basic READ capabilities only
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000/api/v1"

def test_endpoint(endpoint, description):
    """Test a GET endpoint and return results"""
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"✅ {description}: {len(data)} items")
            else:
                print(f"✅ {description}: Success")
            return True, data
        else:
            print(f"❌ {description}: HTTP {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ {description}: Error - {str(e)}")
        return False, None

def main():
    print("🧪 TESTING PUBLIC API READ ENDPOINTS")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Test list endpoints
    endpoints = [
        ("/vehicles/public", "Vehicles List"),
        ("/routes/public", "Routes List"),
        ("/drivers/public", "Drivers List"),
    ]
    
    for endpoint, description in endpoints:
        total_tests += 1
        success, data = test_endpoint(endpoint, description)
        if success:
            success_count += 1
    
    # Test individual item endpoints
    individual_tests = [
        ("/vehicles/public/ZR101", "Vehicle by Reg Code"),
        ("/routes/public/1A", "Route by Code"),
        ("/drivers/public/LIC001", "Driver by License"),
    ]
    
    for endpoint, description in individual_tests:
        total_tests += 1
        success, data = test_endpoint(endpoint, description)
        if success:
            success_count += 1
    
    # Test error handling
    print(f"\n🔍 TESTING ERROR HANDLING")
    error_tests = [
        ("/vehicles/public/NONEXISTENT", "Non-existent Vehicle"),
        ("/routes/public/FAKE", "Non-existent Route"),
        ("/drivers/public/NOLIC", "Non-existent Driver"),
    ]
    
    for endpoint, description in error_tests:
        total_tests += 1
        try:
            url = f"{API_BASE}{endpoint}"
            response = requests.get(url, timeout=5)
            if response.status_code == 404:
                print(f"✅ {description}: Proper 404 error")
                success_count += 1
            else:
                print(f"❌ {description}: Expected 404, got {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")
    
    # Summary
    print(f"\n📊 RESULTS")
    print("=" * 50)
    print(f"✅ Passed: {success_count}/{total_tests}")
    print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print(f"🎉 ALL PUBLIC API READ ENDPOINTS WORKING!")
        return 0
    else:
        print(f"⚠️  Some endpoints need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())