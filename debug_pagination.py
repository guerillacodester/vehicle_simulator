#!/usr/bin/env python3
"""
Debug: Strapi Pagination Investigation
=====================================

Test different pagination parameters to understand correct syntax.
"""

import asyncio
import sys
import os

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def investigate_pagination():
    """Test different pagination syntaxes"""
    
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        await client.connect()
        
        print("Testing different pagination parameters...")
        
        # Test 1: pageSize parameter
        print("\n1. Testing pagination[pageSize]=1000")
        try:
            response = await client.session.get(
                f"{client.base_url}/api/pois",
                params={"pagination[pageSize]": 1000}
            )
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("data", []))
                pagination = data.get("meta", {}).get("pagination", {})
                print(f"   Result: {count} POIs, pagination meta: {pagination}")
            else:
                print(f"   Failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: limit parameter  
        print("\n2. Testing pagination[limit]=1000")
        try:
            response = await client.session.get(
                f"{client.base_url}/api/pois", 
                params={"pagination[limit]": 1000}
            )
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("data", []))
                pagination = data.get("meta", {}).get("pagination", {})
                print(f"   Result: {count} POIs, pagination meta: {pagination}")
            else:
                print(f"   Failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: Check available endpoints
        print("\n3. Testing available endpoints...")
        endpoints = ["pois", "places", "landuses", "landuse", "land-uses"]
        
        for endpoint in endpoints:
            try:
                response = await client.session.get(f"{client.base_url}/api/{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    count = len(data.get("data", []))
                    print(f"   ✅ /api/{endpoint}: {count} records")
                else:
                    print(f"   ❌ /api/{endpoint}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ /api/{endpoint}: {e}")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(investigate_pagination())