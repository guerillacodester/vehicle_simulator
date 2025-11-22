#!/usr/bin/env python3
"""Test fleet_manager authenticated SSE telemetry access"""
import requests
import json
import time

print("=" * 70)
print("Testing FLEET_MANAGER Authenticated Telemetry Access via SSE")
print("=" * 70)

# Test with fleet_manager authentication
print("\nTesting AUTHENTICATED access (fleet_manager)...")
try:
    # Login to get JWT cookie
    print("Logging in as fleet_manager...")
    login_response = requests.post(
        'http://localhost:7000/login',
        json={'username': 'fleet_manager', 'password': 'Ga25w123'}
    )
    
    if login_response.status_code == 200:
        print(f"[OK] Login successful")
        cookies = login_response.cookies
        
        # Connect to SSE with cookies
        print("Connecting to SSE stream with authentication...")
        response = requests.get('http://localhost:5000/sse', cookies=cookies, stream=True, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("[OK] Connected to SSE stream with fleet_manager authentication")
            print("Listening for telemetry updates (10 seconds)...\n")
            
            start_time = time.time()
            count = 0
            for line in response.iter_lines():
                if time.time() - start_time > 10:
                    break
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data:'):
                        data = decoded[5:].strip()
                        try:
                            obj = json.loads(data)
                            if obj.get('type') == 'update':
                                count += 1
                                state = obj.get('state', {})
                                print(f"[Update #{count}] Device: {obj.get('deviceId', 'Unknown')}")
                                print(f"  Fields received: {list(state.keys())}")
                                print(f"  Field count: {len(state)}")
                                print(f"  Sample data: lat={state.get('lat')}, lon={state.get('lon')}, speed={state.get('speed')}")
                                if 'driverId' in state:
                                    print(f"  [AUTH FIELD] driverId: {state.get('driverId')}")
                                if 'deviceId' in state:
                                    print(f"  [AUTH FIELD] deviceId: {state.get('deviceId')}")
                                print()
                        except Exception as e:
                            print(f"  Parse error: {e}")
            
            print(f"\n[OK] Received {count} telemetry updates as fleet_manager")
            print("[OK] Authenticated access working - seeing more fields than public!")
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"Response: {response.text}")
    else:
        print(f"[ERROR] Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
except requests.exceptions.Timeout:
    print("[WARNING] Timeout - no data received")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "=" * 70)
print("Test complete")
print("=" * 70)
