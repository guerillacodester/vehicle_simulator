#!/usr/bin/env python3
"""Test public (unauthenticated) SSE telemetry access"""
import requests
import json
import time

print("=" * 70)
print("Testing Public (Unauthenticated) Telemetry Access via SSE")
print("=" * 70)

# Test without authentication (public access)
print("\n1. Testing PUBLIC access (no authentication)...")
try:
    response = requests.get('http://localhost:5000/sse', stream=True, timeout=5)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✓ Connected to SSE stream")
        print("   Listening for 5 seconds...")
        
        start_time = time.time()
        for line in response.iter_lines():
            if time.time() - start_time > 5:
                break
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data:'):
                    data = decoded[5:].strip()
                    try:
                        obj = json.loads(data)
                        print(f"   Received: {json.dumps(obj, indent=2)}")
                    except:
                        print(f"   Received: {data}")
        print("   ✓ Public access working")
    else:
        print(f"   ✗ Error: {response.status_code}")
        print(f"   Response: {response.text}")
except requests.exceptions.Timeout:
    print("   ⚠ Timeout (no data received in 5 seconds - this may be normal if no vehicles are broadcasting)")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test with fleet_manager authentication
print("\n2. Testing AUTHENTICATED access (fleet_manager)...")
try:
    # Login to get JWT cookie
    login_response = requests.post(
        'http://localhost:7000/login',
        json={'username': 'fleet_manager', 'password': 'Ga25w123'}
    )
    
    if login_response.status_code == 200:
        print("   ✓ Login successful")
        cookies = login_response.cookies
        
        # Connect to SSE with cookies
        response = requests.get('http://localhost:5000/sse', cookies=cookies, stream=True, timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ Connected to SSE stream with authentication")
            print("   Listening for 5 seconds...")
            
            start_time = time.time()
            for line in response.iter_lines():
                if time.time() - start_time > 5:
                    break
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data:'):
                        data = decoded[5:].strip()
                        try:
                            obj = json.loads(data)
                            print(f"   Received: {json.dumps(obj, indent=2)}")
                        except:
                            print(f"   Received: {data}")
            print("   ✓ Authenticated access working")
        else:
            print(f"   ✗ Error: {response.status_code}")
            print(f"   Response: {response.text}")
    else:
        print(f"   ✗ Login failed: {login_response.status_code}")
except requests.exceptions.Timeout:
    print("   ⚠ Timeout (no data received in 5 seconds - this may be normal if no vehicles are broadcasting)")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 70)
print("Test complete")
print("=" * 70)
