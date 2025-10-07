#!/usr/bin/env python3
"""
Test Current Database State
==========================

Verify what geographic data we actually have in Strapi database
"""

import asyncio
import sys
import os

# Add commuter_service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def test_database_state():
    """Test what's currently in the database"""
    
    print("🔍 Testing Current Database State")
    print("=" * 50)
    
    async with StrapiApiClient("http://localhost:1337") as client:
        # Test basic connectivity
        health = await client.health_check()
        print(f"📡 API Health: {health['status']}")
        
        if health['status'] != 'healthy':
            print("❌ API not healthy - check if Strapi is running")
            return False
        
        # Get Barbados country info
        country = await client.get_country_by_code("BB")
        if not country:
            print("❌ Barbados country not found")
            return False
        
        country_id = country['id']
        print(f"🌍 Country: {country['name']} (ID: {country_id})")
        
        # Test each geographic data type
        print("\n📊 Current Database Contents:")
        
        # POIs
        pois = await client.get_pois_by_country(country_id)
        print(f"  📍 POIs: {len(pois)}")
        
        # Places
        places = await client.get_places_by_country(country_id)
        print(f"  🏘️  Places: {len(places)}")
        
        # Landuse Zones
        landuse = await client.get_landuse_zones_by_country(country_id)
        print(f"  🌾 Landuse Zones: {len(landuse)}")
        
        # Regions
        regions = await client.get_regions_by_country(country_id)
        print(f"  🗺️  Regions: {len(regions)}")
        
        print("\n" + "=" * 50)
        
        # Show sample data if available
        if pois:
            print(f"📍 Sample POI: {pois[0].get('name', 'No name')} ({pois[0].get('poi_type', 'Unknown type')})")
        
        if places:
            print(f"🏘️  Sample Place: {places[0].get('name', 'No name')} ({places[0].get('place_type', 'Unknown type')})")
            
        if landuse:
            print(f"🌾 Sample Landuse: {landuse[0].get('landuse_type', 'Unknown type')}")
            
        if regions:
            print(f"🗺️  Sample Region: {regions[0].get('name', 'No name')} ({regions[0].get('region_type', 'Unknown type')})")
        
        return True

if __name__ == "__main__":
    success = asyncio.run(test_database_state())
    sys.exit(0 if success else 1)