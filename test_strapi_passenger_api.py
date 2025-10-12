"""
Deep diagnostic test for Strapi active-passengers API
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta


async def test_strapi_api():
    """Test all aspects of the Strapi API for active-passengers"""
    
    strapi_url = "http://localhost:1337"
    
    print("=" * 80)
    print("STRAPI API DIAGNOSTIC TEST")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Check if the endpoint exists (GET)
        print("\n1️⃣ Testing GET /api/active-passengers...")
        try:
            async with session.get(f"{strapi_url}/api/active-passengers") as response:
                print(f"   Status: {response.status}")
                print(f"   Reason: {response.reason}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ GET works! Found {len(data.get('data', []))} passengers")
                else:
                    text = await response.text()
                    print(f"   ❌ Error: {text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 2: Try POST with minimal data
        print("\n2️⃣ Testing POST /api/active-passengers (minimal data)...")
        test_data = {
            "data": {
                "passenger_id": "TEST_001",
                "route_id": "1A",
                "latitude": 13.0965,
                "longitude": -59.6086,
                "destination_lat": 13.2521,
                "destination_lon": -59.6425,
                "status": "WAITING"
            }
        }
        
        try:
            async with session.post(
                f"{strapi_url}/api/active-passengers",
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"   Status: {response.status}")
                print(f"   Reason: {response.reason}")
                print(f"   Headers: {dict(response.headers)}")
                
                text = await response.text()
                print(f"   Response Body: {text[:500]}")
                
                if response.status in (200, 201):
                    print("   ✅ POST works!")
                elif response.status == 405:
                    print("   ❌ 405 Method Not Allowed - Permission issue!")
                elif response.status == 400:
                    print("   ❌ 400 Bad Request - Data validation issue")
                elif response.status == 403:
                    print("   ❌ 403 Forbidden - Permission denied")
                else:
                    print(f"   ❌ Unexpected status: {response.status}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 3: Check Content-Type in collection
        print("\n3️⃣ Checking collection type definition...")
        try:
            async with session.get(f"{strapi_url}/api/active-passengers") as response:
                print(f"   Status: {response.status}")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data:
                        print(f"   ✅ Collection exists with {len(data['data'])} entries")
                        if len(data['data']) > 0:
                            print(f"   Sample entry: {data['data'][0]}")
                    else:
                        print(f"   Response structure: {list(data.keys())}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 4: Try with full data (like the actual code)
        print("\n4️⃣ Testing POST with full data structure...")
        spawned_at = datetime.utcnow()
        expires_at = spawned_at + timedelta(minutes=30)
        
        full_data = {
            "data": {
                "passenger_id": "TEST_FULL_002",
                "route_id": "1A",
                "depot_id": None,
                "direction": "OUTBOUND",
                "latitude": 13.0965,
                "longitude": -59.6086,
                "destination_name": "Destination",
                "destination_lat": 13.2521,
                "destination_lon": -59.6425,
                "spawned_at": spawned_at.isoformat() + "Z",
                "expires_at": expires_at.isoformat() + "Z",
                "status": "WAITING",
                "priority": 3
            }
        }
        
        try:
            async with session.post(
                f"{strapi_url}/api/active-passengers",
                json=full_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"   Status: {response.status}")
                text = await response.text()
                
                if response.status in (200, 201):
                    print("   ✅ Full data POST works!")
                    print(f"   Response: {text[:300]}")
                else:
                    print(f"   ❌ Failed with status {response.status}")
                    print(f"   Response: {text[:500]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 5: Check OPTIONS (CORS preflight)
        print("\n5️⃣ Testing OPTIONS (CORS preflight)...")
        try:
            async with session.options(f"{strapi_url}/api/active-passengers") as response:
                print(f"   Status: {response.status}")
                print(f"   Allow: {response.headers.get('Allow', 'Not specified')}")
                print(f"   Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'Not specified')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_strapi_api())
