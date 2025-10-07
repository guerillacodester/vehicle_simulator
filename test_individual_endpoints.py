#!/usr/bin/env python3
"""
Test Individual API Endpoints
===========================

Test each geographic data endpoint separately to identify issues
"""

import asyncio
import sys
import os
import httpx

# Add commuter_service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def test_individual_endpoints():
    """Test each endpoint individually"""
    
    print("🔍 Testing Individual API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:1337"
    country_id = 29  # Barbados
    
    # Test direct HTTP calls first
    async with httpx.AsyncClient() as session:
        
        print("🧪 Testing Direct HTTP Calls:")
        
        # Test POIs endpoint with high pagination
        try:
            response = await session.get(f"{base_url}/api/pois?pagination[limit]=50000")
            print(f"  📍 /api/pois: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"    Total POIs in system: {len(data.get('data', []))}")
                meta = data.get('meta', {}).get('pagination', {})
                if meta:
                    print(f"    Pagination total: {meta.get('total', 'unknown')}")
        except Exception as e:
            print(f"    ❌ POIs endpoint error: {e}")
        
        # Test Places endpoint with high pagination
        try:
            response = await session.get(f"{base_url}/api/places?pagination[limit]=50000")
            print(f"  🏘️  /api/places: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"    Total Places in system: {len(data.get('data', []))}")
                meta = data.get('meta', {}).get('pagination', {})
                if meta:
                    print(f"    Pagination total: {meta.get('total', 'unknown')}")
        except Exception as e:
            print(f"    ❌ Places endpoint error: {e}")
        
        # Test Landuse Zones endpoint with high pagination
        try:
            response = await session.get(f"{base_url}/api/landuse-zones?pagination[limit]=50000")
            print(f"  🌾 /api/landuse-zones: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"    Total Landuse zones in system: {len(data.get('data', []))}")
                meta = data.get('meta', {}).get('pagination', {})
                if meta:
                    print(f"    Pagination total: {meta.get('total', 'unknown')}")
            else:
                print(f"    ❌ Response: {response.text[:200]}")
        except Exception as e:
            print(f"    ❌ Landuse zones endpoint error: {e}")
        
        # Test Regions endpoint with high pagination
        try:
            response = await session.get(f"{base_url}/api/regions?pagination[limit]=50000")
            print(f"  🗺️  /api/regions: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"    Total Regions in system: {len(data.get('data', []))}")
                meta = data.get('meta', {}).get('pagination', {})
                if meta:
                    print(f"    Pagination total: {meta.get('total', 'unknown')}")
        except Exception as e:
            print(f"    ❌ Regions endpoint error: {e}")
    
    print("\n" + "=" * 50)
    
    # Now test with our API client
    print("🧪 Testing with StrapiApiClient:")
    
    async with StrapiApiClient(base_url) as client:
        
        # Test POIs with country filter
        try:
            pois = await client.get_pois_by_country(country_id)
            print(f"  📍 POIs for country {country_id}: {len(pois)}")
        except Exception as e:
            print(f"    ❌ POIs client error: {e}")
        
        # Test Places with country filter
        try:
            places = await client.get_places_by_country(country_id)
            print(f"  🏘️  Places for country {country_id}: {len(places)}")
        except Exception as e:
            print(f"    ❌ Places client error: {e}")
        
        # Test Landuse with country filter
        try:
            landuse = await client.get_landuse_zones_by_country(country_id)
            print(f"  🌾 Landuse zones for country {country_id}: {len(landuse)}")
        except Exception as e:
            print(f"    ❌ Landuse client error: {e}")
        
        # Test Regions with country filter
        try:
            regions = await client.get_regions_by_country(country_id)
            print(f"  🗺️  Regions for country {country_id}: {len(regions)}")
        except Exception as e:
            print(f"    ❌ Regions client error: {e}")

if __name__ == "__main__":
    asyncio.run(test_individual_endpoints())