#!/usr/bin/env python3
"""
Test script for FastAPI server integration with RedisServiceManager
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from arknet_transit_launcher.server import create_app
from fastapi.testclient import TestClient

def test_server_integration():
    app = create_app()
    client = TestClient(app)

    print('🧪 Testing FastAPI Server Integration')
    print('=====================================')

    # Test /services endpoint
    print('Testing /services endpoint...')
    response = client.get('/services')
    print(f'  Status: {response.status_code}')
    if response.status_code == 200:
        services = response.json()
        print(f'  Services returned: {len(services)}')
        for service in services:
            print(f'    {service.get("name", "unknown")}: {service.get("state", "unknown")} - {service.get("message", "")}')
    else:
        print(f'  Error: {response.text}')

    # Test /services/redis/start endpoint
    print('Testing /services/redis/start endpoint...')
    response = client.post('/services/redis/start')
    print(f'  Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'  Response: {data}')
    else:
        print(f'  Error: {response.text}')

    # Test /services/redis/stop endpoint
    print('Testing /services/redis/stop endpoint...')
    response = client.post('/services/redis/stop')
    print(f'  Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'  Response: {data}')
    else:
        print(f'  Error: {response.text}')

    # Test /services/redis/enable endpoint
    print('Testing /services/redis/enable endpoint...')
    response = client.post('/services/redis/enable')
    print(f'  Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'  Response: {data}')
    else:
        print(f'  Error: {response.text}')

    print('✅ Server integration test complete!')

if __name__ == '__main__':
    test_server_integration()