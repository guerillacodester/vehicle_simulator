#!/usr/bin/env python3
"""
Debug: Depot Spawning Issue Investigation
=========================================

Investigate why depot spawning returned 0 passengers.
"""

import asyncio
import sys
import os
import json

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def debug_depot_spawning():
    """Debug depot spawning issue"""
    
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        await client.connect()
        
        print("🔍 DEPOT SPAWNING DEBUG")
        print("="*30)
        
        # Get depot data
        depots_response = await client.session.get(f"{client.base_url}/api/depots")
        if depots_response.status_code == 200:
            depots_data = depots_response.json().get("data", [])
            print(f"Found {len(depots_data)} depots")
            
            for depot in depots_data:
                print(f"\nDepot: {depot.get('name', 'Unknown')} (ID: {depot.get('id')})")
                print(f"  Latitude: {depot.get('latitude')} (type: {type(depot.get('latitude'))})")
                print(f"  Longitude: {depot.get('longitude')} (type: {type(depot.get('longitude'))})")
                print(f"  Capacity: {depot.get('capacity')}")
                print(f"  Is Active: {depot.get('is_active')}")
                
                # Test coordinate validation
                lat = depot.get('latitude')
                lon = depot.get('longitude')
                
                print(f"  Coordinate validation:")
                print(f"    lat exists: {lat is not None}")
                print(f"    lon exists: {lon is not None}")
                
                if lat is not None and lon is not None:
                    print(f"    Both coordinates exist ✅")
                else:
                    print(f"    Missing coordinates ❌")
                    print(f"    This explains why spawning returned 0 passengers")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(debug_depot_spawning())