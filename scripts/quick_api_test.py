"""
Quick API Test Script
====================
Rapid verification script for Fleet Management API endpoints.
Performs basic connectivity and endpoint availability tests.
"""

import requests
import json
import sys
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[str, Any] = None, use_prefix: bool = True) -> bool:
    """Test a single endpoint"""
    if use_prefix and endpoint.startswith("/") and not endpoint.startswith("/health") and not endpoint == "/":
        url = f"{API_BASE_URL}{API_PREFIX}{endpoint}"
    else:
        url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return False
            
        print(f"{'✅' if response.status_code < 400 else '❌'} {method} {endpoint} - Status: {response.status_code}")
        return response.status_code < 400
        
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return False

def main():
    """Quick test runner"""
    print("🧪 Quick API Test - Fleet Management System")
    print("=" * 50)
    
    # Test basic connectivity
    print("\n📡 Testing basic connectivity...")
    if not test_endpoint("/", use_prefix=False):
        print("❌ API is not responding")
        sys.exit(1)
        
    if not test_endpoint("/health", use_prefix=False):
        print("❌ Health check failed")
        sys.exit(1)
    
    # Test API documentation
    print("\n📚 Testing documentation endpoints...")
    test_endpoint("/docs", use_prefix=False)
    test_endpoint("/redoc", use_prefix=False)
    
    # Test core CRUD endpoints
    print("\n🔧 Testing CRUD endpoints...")
    endpoints = [
        "/countries",
        "/depots", 
        "/vehicles",
        "/drivers",
        "/stops",
        "/trips",
        "/services",
        "/blocks"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        if test_endpoint(endpoint):
            success_count += 1
    
    print(f"\n📊 Results: {success_count}/{len(endpoints)} endpoints responding")
    
    if success_count == len(endpoints):
        print("✅ All endpoints are accessible - API is ready!")
        sys.exit(0)
    else:
        print("❌ Some endpoints failed - Check API status")
        sys.exit(1)

if __name__ == "__main__":
    main()
