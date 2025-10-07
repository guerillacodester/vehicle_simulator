#!/usr/bin/env python3
"""
Test Landuse Zone Schema and Filtering
=====================================

Identify the exact issue with landuse zone filtering
"""

import asyncio
import httpx

async def test_landuse_schema():
    """Test landuse zone schema and filtering step by step"""
    
    print("🔍 Testing Landuse Zone Schema")
    print("=" * 40)
    
    base_url = "http://localhost:1337"
    
    async with httpx.AsyncClient() as session:
        
        # Step 1: Test basic landuse endpoint
        print("1️⃣  Testing basic /api/landuse-zones")
        response = await session.get(f"{base_url}/api/landuse-zones")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total_zones = len(data.get('data', []))
            print(f"   Total zones: {total_zones}")
            
            if total_zones > 0:
                # Show first zone structure
                first_zone = data['data'][0]
                print(f"   Sample zone ID: {first_zone.get('id')}")
                print(f"   Available fields: {list(first_zone.keys())}")
                
                # Check if country field exists
                if 'country' in first_zone:
                    print(f"   Country field: {first_zone['country']}")
                else:
                    print("   ❌ No 'country' field found!")
        
        # Step 2: Test different filter variations
        print("\n2️⃣  Testing filter variations")
        
        # Try simple country filter
        test_filters = [
            "filters[country][$eq]=29",
            "filters[country][id][$eq]=29", 
            "filters[country][$in]=29",
            "populate=country"
        ]
        
        for filter_param in test_filters:
            try:
                url = f"{base_url}/api/landuse-zones?{filter_param}"
                print(f"   Testing: {filter_param}")
                response = await session.get(url)
                print(f"     Status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text[:200]
                    print(f"     Error: {error_text}")
                else:
                    data = response.json()
                    count = len(data.get('data', []))
                    print(f"     Results: {count} zones")
                    
            except Exception as e:
                print(f"     Exception: {e}")
        
        # Step 3: Test content type schema
        print("\n3️⃣  Testing content type schema")
        try:
            # This might not work but worth trying
            response = await session.get(f"{base_url}/content-manager/content-types/api::landuse-zone.landuse-zone")
            print(f"   Schema endpoint: {response.status_code}")
        except:
            print("   Schema endpoint not accessible")

if __name__ == "__main__":
    asyncio.run(test_landuse_schema())