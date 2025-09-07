#!/usr/bin/env python3
"""
Simple 404 test to debug the connection issue
"""
import requests
import uuid
import time

def test_404():
    base_url = "http://localhost:8000"
    fake_id = str(uuid.uuid4())
    url = f"{base_url}/api/v1/countries/{fake_id}"
    
    print(f"Testing URL: {url}")
    
    try:
        # Test with requests directly
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content: {response.text}")
        print(f"URL used: {response.url}")
        
        if response.status_code == 404:
            print("✅ 404 test PASSED")
        else:
            print(f"❌ 404 test FAILED - Expected 404, got {response.status_code}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    # Test multiple times to see if it's intermittent
    for i in range(3):
        print(f"\n--- Test {i+1} ---")
        test_404()
        time.sleep(1)
