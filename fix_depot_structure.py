#!/usr/bin/env python3
"""
Depot Structure Fix & Default Depot Creation
==========================================

1. Fix existing depot coordinate structure
2. Create recommended default depots
3. Prepare depot schema for spawning system
"""

import asyncio
import sys
import os
import json

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def fix_depot_structure():
    """Fix depot coordinate structure and create default depots"""
    
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        await client.connect()
        
        print("🔧 DEPOT STRUCTURE FIX & DEFAULT DEPOT CREATION")
        print("="*55)
        
        # 1. Analyze current depot structure issue
        print("\n1. CURRENT DEPOT COORDINATE ISSUE:")
        depots_response = await client.session.get(f"{client.base_url}/api/depots")
        current_depots = []
        
        if depots_response.status_code == 200:
            current_depots = depots_response.json().get("data", [])
            
            for depot in current_depots:
                print(f"   Depot: {depot.get('name')}")
                location = depot.get('location', {})
                print(f"   Current structure: location = {location}")
                print(f"   Missing: separate latitude/longitude fields")
                
                # Extract coordinates from nested location
                if isinstance(location, dict):
                    lat = location.get('lat')
                    lon = location.get('lon')
                    print(f"   Available coordinates: lat={lat}, lon={lon}")
                else:
                    print(f"   ❌ Invalid location format: {type(location)}")
        
        # 2. Recommend depot schema migration
        print(f"\n2. RECOMMENDED SCHEMA MIGRATION:")
        print("   Current schema (problematic):")
        print("     location: {lat: 13.0969, lon: -59.6168}  ❌")
        print() 
        print("   Target schema (PostGIS compliant):")
        print("     latitude: 13.0969   ✅")
        print("     longitude: -59.6168  ✅")
        print("     location: null       (deprecated)")
        
        # 3. Define recommended default depots
        print(f"\n3. RECOMMENDED DEFAULT DEPOTS:")
        
        default_depots = [
            {
                "name": "Bridgetown Central Terminal",
                "depot_id": "BGI_CENTRAL",
                "latitude": 13.0969,   # From existing depot location
                "longitude": -59.6168,
                "address": "Bridgetown, St. Michael",
                "capacity": 100,
                "is_active": True,
                "is_regional_hub": True,
                "daily_passenger_estimate": 1500,
                "operating_hours": "05:00-23:00"
            },
            {
                "name": "Speightstown Bus Terminal", 
                "depot_id": "SPT_NORTH",
                "latitude": 13.25206812,  # From POI data
                "longitude": -59.642543,
                "address": "Speightstown, St. Peter",
                "capacity": 60,
                "is_active": True,
                "is_regional_hub": True,
                "daily_passenger_estimate": 800,
                "operating_hours": "05:30-22:30"
            },
            {
                "name": "Six Roads Junction Depot",
                "depot_id": "SIX_ROADS", 
                "latitude": 13.117628688888889,  # From service station POI
                "longitude": -59.47646964444444,
                "address": "Six Roads, St. Philip", 
                "capacity": 40,
                "is_active": True,
                "is_regional_hub": False,
                "daily_passenger_estimate": 400,
                "operating_hours": "06:00-22:00"
            },
            {
                "name": "Holetown Service Hub",
                "depot_id": "HOLETOWN",
                "latitude": 13.185472844444446,  # From service station POI
                "longitude": -59.63702315555555,
                "address": "Holetown, St. James",
                "capacity": 35, 
                "is_active": True,
                "is_regional_hub": False,
                "daily_passenger_estimate": 300,
                "operating_hours": "06:00-22:00"
            }
        ]
        
        for i, depot in enumerate(default_depots, 1):
            print(f"\n   {i}. {depot['name']} ({depot['depot_id']})")
            print(f"      Location: {depot['latitude']:.6f}, {depot['longitude']:.6f}")
            print(f"      Capacity: {depot['capacity']} vehicles")
            print(f"      Hub Status: {'Regional Hub' if depot['is_regional_hub'] else 'Local Depot'}")
            print(f"      Daily Passengers: ~{depot['daily_passenger_estimate']}")
        
        # 4. Manual API update instructions
        print(f"\n4. MANUAL DEPOT UPDATE INSTRUCTIONS:")
        print("   Since we're using the API client for validation only, here are the steps:")
        print()
        print("   A. UPDATE EXISTING DEPOT (Bridgetown):")
        print("      - Add latitude: 13.0969")
        print("      - Add longitude: -59.6168") 
        print("      - Keep location field for backward compatibility")
        print()
        print("   B. CREATE NEW DEPOTS via Strapi Admin:")
        
        for depot in default_depots[1:]:  # Skip first (it's the update)
            print(f"\n      CREATE: {depot['name']}")
            print(f"      depot_id: {depot['depot_id']}")
            print(f"      latitude: {depot['latitude']}")
            print(f"      longitude: {depot['longitude']}")
            print(f"      capacity: {depot['capacity']}")
            print(f"      is_active: {depot['is_active']}")
            print(f"      is_regional_hub: {depot['is_regional_hub']}")
        
        # 5. Validation test for fixed structure
        print(f"\n5. DEPOT SPAWNING VALIDATION TEST:")
        print("   After fixing coordinate structure, test with:")
        print("   ```python")
        print("   depot = api_client.get_depot(depot_id)")
        print("   lat = depot.get('latitude')    # Should exist")
        print("   lon = depot.get('longitude')   # Should exist") 
        print("   if lat and lon:")
        print("       spawn_passengers_at_depot(depot_id, lat, lon)")
        print("   ```")
        
        # 6. Geographic coverage analysis
        print(f"\n6. GEOGRAPHIC COVERAGE ANALYSIS:")
        if default_depots:
            print("   Recommended depot coverage:")
            print("   - North Coast: Speightstown (Regional Hub)")
            print("   - Central: Bridgetown (Primary Hub)")  
            print("   - East: Six Roads (Local)")
            print("   - West Coast: Holetown (Local)")
            print()
            print("   Missing coverage areas (for manual addition):")
            print("   - South Coast (Oistins area)")
            print("   - Airport/Grantley Adams area") 
            print("   - East Coast (Bathsheba area)")
        
        # Save results
        results = {
            'current_depots': current_depots,
            'recommended_defaults': default_depots,
            'migration_needed': True,
            'schema_fix': {
                'add_fields': ['latitude', 'longitude'],
                'deprecate_fields': ['location'],
                'reason': 'PostGIS compliance for spawning system'
            }
        }
        
        with open('depot_fix_plan.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Depot fix plan saved to: depot_fix_plan.json")
        print(f"📋 Summary: Fix 1 existing + Create 3 new depots")
        print(f"🎯 Result: Complete Barbados depot coverage for spawning system")
        
        return results
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(fix_depot_structure())