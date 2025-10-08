#!/usr/bin/env python3
"""
Coordinate Availability Investigation
====================================

Check GPS coordinate availability across all spawning components:
- Depots, Routes, Stops (we already confirmed POIs and Places)
"""

import asyncio
import sys
import os
import json

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def investigate_all_coordinates():
    """Check coordinate availability for all spawning components"""
    
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        await client.connect()
        
        print("🧭 COORDINATE AVAILABILITY INVESTIGATION")
        print("="*50)
        
        # 1. Check Depots
        print("\n📍 DEPOT COORDINATES:")
        try:
            depots_response = await client.session.get(f"{client.base_url}/api/depots")
            if depots_response.status_code == 200:
                depots_data = depots_response.json().get("data", [])
                print(f"Found {len(depots_data)} depots")
                
                for i, depot in enumerate(depots_data[:2]):  # Show first 2
                    print(f"\nDepot {i+1}: {depot.get('name', 'Unknown')}")
                    print(f"  Structure: {json.dumps(depot, indent=2, default=str)}")
            else:
                print(f"❌ Depots API failed: HTTP {depots_response.status_code}")
        except Exception as e:
            print(f"❌ Depot check failed: {e}")
        
        # 2. Check Routes  
        print("\n🛣️  ROUTE COORDINATES:")
        try:
            routes_response = await client.session.get(f"{client.base_url}/api/routes")
            if routes_response.status_code == 200:
                routes_data = routes_response.json().get("data", [])
                print(f"Found {len(routes_data)} routes")
                
                for i, route in enumerate(routes_data[:2]):  # Show first 2
                    print(f"\nRoute {i+1}: {route.get('short_name', 'Unknown')} - {route.get('long_name', 'Unknown')}")
                    print(f"  Structure: {json.dumps(route, indent=2, default=str)}")
            else:
                print(f"❌ Routes API failed: HTTP {routes_response.status_code}")
        except Exception as e:
            print(f"❌ Route check failed: {e}")
        
        # 3. Check Stops
        print("\n🚏 STOP COORDINATES:")
        try:
            stops_response = await client.session.get(f"{client.base_url}/api/stops")
            if stops_response.status_code == 200:
                stops_data = stops_response.json().get("data", [])
                print(f"Found {len(stops_data)} stops")
                
                for i, stop in enumerate(stops_data[:2]):  # Show first 2
                    print(f"\nStop {i+1}: {stop.get('name', 'Unknown')}")
                    print(f"  Structure: {json.dumps(stop, indent=2, default=str)}")
            else:
                print(f"❌ Stops API failed: HTTP {stops_response.status_code}")
        except Exception as e:
            print(f"❌ Stop check failed: {e}")
        
        # 4. Check Route Shapes (if separate)
        print("\n📐 ROUTE SHAPES COORDINATES:")
        try:
            shapes_response = await client.session.get(f"{client.base_url}/api/shapes")
            if shapes_response.status_code == 200:
                shapes_data = shapes_response.json().get("data", [])
                print(f"Found {len(shapes_data)} shape points")
                
                for i, shape in enumerate(shapes_data[:2]):  # Show first 2
                    print(f"\nShape Point {i+1}:")
                    print(f"  Structure: {json.dumps(shape, indent=2, default=str)}")
            else:
                print(f"❌ Shapes API failed: HTTP {shapes_response.status_code}")
        except Exception as e:
            print(f"❌ Shape check failed: {e}")
        
        # 5. Summary
        print("\n" + "="*50)
        print("COORDINATE AVAILABILITY SUMMARY:")
        print("✅ POIs: 1,419 with lat/lon (confirmed)")
        print("✅ Places: 8,283 with lat/lon (confirmed)")
        print("❓ Depots: Check above results")  
        print("❓ Routes: Check above results")
        print("❓ Stops: Check above results")
        print("❓ Shapes: Check above results")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(investigate_all_coordinates())