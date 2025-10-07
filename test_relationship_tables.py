#!/usr/bin/env python3
"""
Test Database Schema and Relationships
=====================================

Check if the relationship tables exist in the database
"""

import asyncio
import httpx

async def test_relationship_tables():
    """Test if relationship link tables exist"""
    
    print("🔍 Testing Database Schema and Relationships")
    print("=" * 50)
    
    base_url = "http://localhost:1337"
    
    async with httpx.AsyncClient() as session:
        
        # Test basic landuse endpoint first
        print("1️⃣  Basic landuse endpoint test:")
        response = await session.get(f"{base_url}/api/landuse-zones")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total_zones = len(data.get('data', []))
            print(f"   Total zones: {total_zones}")
        
        # Test different filter approaches to diagnose the 400 error
        print("\n2️⃣  Testing various filter approaches:")
        
        test_cases = [
            # Basic filters
            ("Basic pagination", "pagination[pageSize]=10"),
            ("Basic sort", "sort=zone_type:asc"), 
            ("Simple field filter", "filters[zone_type][$eq]=residential"),
            
            # Country relationship tests
            ("Country populate", "populate=country"),
            ("Country filter attempt 1", "filters[country][$eq]=29"),
            ("Country filter attempt 2", "filters[country][id][$eq]=29"),
            ("Country filter attempt 3", "filters[country][$in]=29"),
            
            # Combination tests
            ("Populate + filter", "populate=country&filters[zone_type][$eq]=residential"),
        ]
        
        for description, query_params in test_cases:
            try:
                url = f"{base_url}/api/landuse-zones?{query_params}"
                print(f"   Testing {description}:")
                print(f"     URL: {query_params}")
                
                response = await session.get(url)
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data.get('data', []))
                    print(f"     Results: {count} zones")
                    
                    # If we have results, show sample structure
                    if count > 0:
                        sample = data['data'][0]
                        print(f"     Sample fields: {list(sample.keys())}")
                        if 'country' in sample:
                            print(f"     Country field: {sample['country']}")
                    
                elif response.status_code == 400:
                    print(f"     ❌ Bad Request - this filter is not supported")
                else:
                    print(f"     ❌ Error {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"     💥 Exception: {e}")
        
        print("\n3️⃣  Testing country endpoint for comparison:")
        try:
            response = await session.get(f"{base_url}/api/countries/29?populate=landuse_zones")
            print(f"   Country with landuse zones: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                country = data.get('data')
                if country and 'landuse_zones' in country:
                    zones_count = len(country['landuse_zones']) if country['landuse_zones'] else 0
                    print(f"   Landuse zones linked to country: {zones_count}")
                else:
                    print(f"   No landuse_zones field in country data")
                    print(f"   Available fields: {list(country.keys()) if country else 'None'}")
        except Exception as e:
            print(f"   💥 Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_relationship_tables())