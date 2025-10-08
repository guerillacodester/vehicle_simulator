#!/usr/bin/env python3
"""
Depot Structure Analysis & Fix Strategy
======================================

1. Analyze current depot structure 
2. Find potential depot locations from existing data
3. Recommend coordinate structure fixes
"""

import asyncio
import sys
import os
import json

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def analyze_depot_structure():
    """Analyze current depot issues and find potential depot locations"""
    
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        await client.connect()
        
        print("🔍 DEPOT STRUCTURE ANALYSIS")
        print("="*40)
        
        # 1. Current depot structure
        print("\n1. CURRENT DEPOT STRUCTURE:")
        depots_response = await client.session.get(f"{client.base_url}/api/depots")
        if depots_response.status_code == 200:
            depots_data = depots_response.json().get("data", [])
            print(f"   Found {len(depots_data)} existing depots")
            
            for depot in depots_data:
                print(f"\n   Depot: {depot.get('name', 'Unknown')}")
                print(f"   Full structure: {json.dumps(depot, indent=4, default=str)}")
        
        # 2. Search for potential depot locations in POIs
        print(f"\n2. POTENTIAL DEPOT LOCATIONS FROM POI DATA:")
        pois_response = await client.session.get(
            f"{client.base_url}/api/pois", 
            params={"pagination[pageSize]": 100}
        )
        
        potential_depots = []
        if pois_response.status_code == 200:
            pois_data = pois_response.json().get("data", [])
            
            # Search for transportation-related POIs
            depot_keywords = [
                'bus', 'terminal', 'station', 'depot', 'transport', 'transit'
            ]
            
            for poi in pois_data:
                poi_name = poi.get('name', '').lower()
                poi_type = poi.get('poi_type', '').lower()
                amenity = poi.get('amenity', '').lower()
                
                # Check if POI could be a depot/terminal
                is_potential_depot = any(keyword in poi_name for keyword in depot_keywords)
                is_transport_poi = poi_type in ['bus_station', 'terminal'] or amenity in ['bus_station', 'terminal']
                
                if is_potential_depot or is_transport_poi:
                    potential_depots.append({
                        'name': poi.get('name'),
                        'poi_type': poi.get('poi_type'),
                        'amenity': poi.get('amenity'),
                        'latitude': poi.get('latitude'),
                        'longitude': poi.get('longitude'),
                        'source_poi_id': poi.get('id')
                    })
        
        print(f"   Found {len(potential_depots)} potential depot locations:")
        for depot in potential_depots:
            print(f"   - {depot['name']} (type: {depot['poi_type']}, lat: {depot['latitude']}, lon: {depot['longitude']})")
        
        # 3. Search for depot-like locations in Places
        print(f"\n3. POTENTIAL DEPOT LOCATIONS FROM PLACES DATA:")
        places_response = await client.session.get(
            f"{client.base_url}/api/places",
            params={"pagination[pageSize]": 100}
        )
        
        potential_place_depots = []
        if places_response.status_code == 200:
            places_data = places_response.json().get("data", [])
            
            for place in places_data:
                place_name = place.get('name', '').lower()
                
                # Check for major hubs/terminals in place names
                if any(keyword in place_name for keyword in ['terminal', 'station', 'depot', 'hub']):
                    potential_place_depots.append({
                        'name': place.get('name'),
                        'latitude': place.get('latitude'),
                        'longitude': place.get('longitude'),
                        'source_place_id': place.get('id')
                    })
        
        print(f"   Found {len(potential_place_depots)} potential depot locations in places:")
        for depot in potential_place_depots:
            print(f"   - {depot['name']} (lat: {depot['latitude']}, lon: {depot['longitude']})")
        
        # 4. Recommended depot structure fix
        print(f"\n4. RECOMMENDED DEPOT STRUCTURE FIX:")
        print("   Current issue: 'location' field is not PostGIS compliant")
        print("   Solution: Add separate 'latitude' and 'longitude' fields")
        print()
        print("   Recommended depot schema:")
        recommended_depot = {
            "id": "auto-generated",
            "name": "Depot Name",
            "depot_id": "unique_depot_code", 
            "latitude": 13.0934,  # Separate latitude field
            "longitude": -59.6178, # Separate longitude field
            "address": "Street address",
            "capacity": 50,
            "is_active": True,
            "is_regional_hub": False,
            "daily_passenger_estimate": 500,
            "operating_hours": "05:00-23:00"
        }
        print(f"   {json.dumps(recommended_depot, indent=4)}")
        
        # 5. Automatic depot creation candidates
        print(f"\n5. RECOMMENDED DEFAULT DEPOTS TO CREATE:")
        default_depots = []
        
        # Merge best candidates from POIs and Places
        all_candidates = potential_depots + [
            {
                'name': p['name'], 
                'latitude': p['latitude'], 
                'longitude': p['longitude'],
                'source': 'places'
            } for p in potential_place_depots
        ]
        
        # Filter for best depot candidates (major terminals)
        major_terminals = [
            d for d in all_candidates 
            if any(term in d['name'].lower() for term in ['bridgetown', 'speightstown', 'terminal'])
        ]
        
        print(f"   Top candidates for automatic creation:")
        for i, depot in enumerate(major_terminals[:5], 1):  # Top 5
            depot_id = f"depot_{i:02d}"
            estimated_capacity = 100 if 'bridgetown' in depot['name'].lower() else 50
            
            default_depot = {
                "name": depot['name'],
                "depot_id": depot_id,
                "latitude": depot['latitude'], 
                "longitude": depot['longitude'],
                "capacity": estimated_capacity,
                "is_active": True,
                "is_regional_hub": 'bridgetown' in depot['name'].lower()
            }
            
            default_depots.append(default_depot)
            print(f"   {i}. {json.dumps(default_depot, indent=6)}")
        
        print(f"\n📋 SUMMARY:")
        print(f"   - Current depots: {len(depots_data)} (missing coordinates)")
        print(f"   - Potential POI depots: {len(potential_depots)}")
        print(f"   - Potential place depots: {len(potential_place_depots)}")
        print(f"   - Recommended defaults: {len(default_depots)}")
        print(f"   - Action needed: Fix depot schema + add coordinates")
        
        return {
            'current_depots': depots_data,
            'potential_depots': potential_depots,
            'potential_place_depots': potential_place_depots,
            'recommended_defaults': default_depots
        }
        
    finally:
        await client.close()

if __name__ == "__main__":
    results = asyncio.run(analyze_depot_structure())
    
    # Save results for reference
    with open('depot_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: depot_analysis_results.json")