#!/usr/bin/env python3
"""
Interactive test of simulator API
"""

import asyncio
import httpx


async def test_simulator_api():
    """Test simulator API directly"""
    base_url = "http://localhost:5001"
    
    async with httpx.AsyncClient(timeout=10) as client:
        # Test health
        print("\n" + "="*80)
        print("1. Testing Simulator Health")
        print("="*80)
        try:
            response = await client.get(f"{base_url}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test vehicles
        print("\n" + "="*80)
        print("2. Testing /api/vehicles endpoint")
        print("="*80)
        try:
            response = await client.get(f"{base_url}/api/vehicles")
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {data}")
            
            if isinstance(data, dict) and 'drivers' in data:
                print(f"\n✅ Found {len(data.get('drivers', []))} vehicles")
                for vehicle in data.get('drivers', [])[:3]:
                    print(f"   - {vehicle.get('vehicle_id', 'N/A')}: {vehicle.get('status', 'N/A')}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test sim/status
        print("\n" + "="*80)
        print("3. Testing /api/sim/status endpoint")
        print("="*80)
        try:
            response = await client.get(f"{base_url}/api/sim/status")
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {data}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_simulator_api())
