#!/usr/bin/env python3
"""
Debug: Geographic Coordinate Structure Investigation
==================================================

Investigate the actual coordinate format in POI and Places API data
to fix Step 3 coordinate processing.
"""

import asyncio
import sys
import os
import json

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def investigate_coordinate_structure():
    """Investigate actual coordinate structure in API data"""
    
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        await client.connect()
        
        print("Investigating coordinate structure in API data...")
        
        # Get sample POI
        pois_response = await client.session.get(
            f"{client.base_url}/api/pois",
            params={"pagination[pageSize]": 3}
        )
        
        if pois_response.status_code == 200:
            pois_data = pois_response.json().get("data", [])
            print(f"\n📍 POI Sample Data (first {len(pois_data)} records):")
            
            for i, poi in enumerate(pois_data):
                print(f"\nPOI {i+1}:")
                print(f"  ID: {poi.get('id')}")
                print(f"  Name: {poi.get('name', 'Unknown')}")
                print(f"  Full structure:")
                # Pretty print the entire POI structure
                poi_json = json.dumps(poi, indent=4, default=str)
                print(f"    {poi_json}")
        
        # Get sample Place
        places_response = await client.session.get(
            f"{client.base_url}/api/places", 
            params={"pagination[pageSize]": 3}
        )
        
        if places_response.status_code == 200:
            places_data = places_response.json().get("data", [])
            print(f"\n🏘️ Places Sample Data (first {len(places_data)} records):")
            
            for i, place in enumerate(places_data):
                print(f"\nPlace {i+1}:")
                print(f"  ID: {place.get('id')}")
                print(f"  Name: {place.get('name', 'Unknown')}")
                print(f"  Full structure:")
                # Pretty print the entire Place structure
                place_json = json.dumps(place, indent=4, default=str)
                print(f"    {place_json}")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(investigate_coordinate_structure())