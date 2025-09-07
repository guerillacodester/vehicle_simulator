#!/usr/bin/env python3
"""
Quick API Connection Test
========================
Test connectivity to the running API server
"""

import requests
import json

def test_api_connection():
    """Test basic API connectivity"""
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        
        # Test countries endpoint  
        print("\n🔍 Testing countries endpoint...")
        response = requests.get(f"{base_url}/api/v1/countries", timeout=5)
        print(f"✅ Countries: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data)} countries")
        else:
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_api_connection()
