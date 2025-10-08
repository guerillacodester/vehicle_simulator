#!/usr/bin/env python3
"""
Find Valid Transit Depot Candidates
===================================

Search through POIs and Places for actual transit terminals, bus stations,
and transportation hubs (NOT service stations).
"""

import asyncio
import sys
import os
import json

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def find_valid_depot_candidates():
    """Find real transit depot candidates from existing data"""
    
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        await client.connect()
        
        print("🚌 VALID TRANSIT DEPOT CANDIDATES")
        print("="*40)
        
        # Search criteria for valid depots
        valid_depot_keywords = [
            'terminal', 'bus terminal', 'transport terminal',
            'bus station', 'transit hub', 'transport hub',
            'depot', 'bus depot', 'transport depot'
        ]
        
        exclude_keywords = [
            'service station', 'gas station', 'fuel', 'petrol',
            'police station', 'fire station', 'radio station'
        ]
        
        # 1. Search POIs for valid transit facilities
        print("\n1. SEARCHING POIs FOR TRANSIT FACILITIES:")
        print("-" * 42)
        
        # Fetch all POIs using multi-page method
        all_pois = []
        page = 1
        while page <= 100:  # Safety limit
            response = await client.session.get(
                f"{client.base_url}/api/pois",
                params={"pagination[page]": page, "pagination[pageSize]": 100}
            )
            if response.status_code == 200:
                data = response.json()
                page_data = data.get("data", [])
                all_pois.extend(page_data)
                
                pagination = data.get("meta", {}).get("pagination", {})
                if page >= pagination.get("pageCount", 1) or len(page_data) == 0:
                    break
                page += 1
            else:
                break
        
        print(f"   Searching through {len(all_pois)} POIs...")
        
        valid_poi_candidates = []
        
        for i, poi in enumerate(all_pois):
            poi_name = poi.get('name', '').lower()
            poi_type = poi.get('poi_type', '').lower() 
            amenity = poi.get('amenity', '').lower()
            
            # Check if it matches valid depot criteria
            is_valid_transit = False
            
            # Check for transit-related poi_type or amenity
            if poi_type in ['bus_station', 'terminal', 'transport_hub'] or amenity in ['bus_station', 'terminal']:
                is_valid_transit = True
            
            # Check for transit keywords in name
            if any(keyword in poi_name for keyword in valid_depot_keywords):
                is_valid_transit = True
            
            # Exclude service stations and other non-transit facilities
            if any(exclude in poi_name for exclude in exclude_keywords):
                is_valid_transit = False
            
            if is_valid_transit:
                candidate = {
                    'index': len(valid_poi_candidates),
                    'name': poi.get('name'),
                    'poi_type': poi.get('poi_type'),
                    'amenity': poi.get('amenity'),
                    'latitude': poi.get('latitude'),
                    'longitude': poi.get('longitude'),
                    'poi_id': poi.get('id'),
                    'source': 'POI'
                }
                valid_poi_candidates.append(candidate)
        
        # Display POI candidates with index numbers
        print(f"\n   Found {len(valid_poi_candidates)} valid POI transit candidates:")
        for candidate in valid_poi_candidates:
            print(f"   [{candidate['index']}] {candidate['name']}")
            print(f"       Type: {candidate['poi_type']} | Amenity: {candidate['amenity']}")
            print(f"       Location: {candidate['latitude']:.6f}, {candidate['longitude']:.6f}")
            print(f"       POI ID: {candidate['poi_id']}")
            print()
        
        # 2. Search Places for transit facilities  
        print("2. SEARCHING PLACES FOR TRANSIT FACILITIES:")
        print("-" * 43)
        
        # Fetch all Places using multi-page method
        all_places = []
        page = 1
        while page <= 100:  # Safety limit
            response = await client.session.get(
                f"{client.base_url}/api/places",
                params={"pagination[page]": page, "pagination[pageSize]": 100}
            )
            if response.status_code == 200:
                data = response.json()
                page_data = data.get("data", [])
                all_places.extend(page_data)
                
                pagination = data.get("meta", {}).get("pagination", {})
                if page >= pagination.get("pageCount", 1) or len(page_data) == 0:
                    break
                page += 1
            else:
                break
        
        print(f"   Searching through {len(all_places)} Places...")
        
        valid_place_candidates = []
        
        for place in all_places:
            place_name = place.get('name', '').lower()
            
            # Check for transit keywords in place names
            is_valid_transit = any(keyword in place_name for keyword in valid_depot_keywords)
            
            # Exclude service stations
            if any(exclude in place_name for exclude in exclude_keywords):
                is_valid_transit = False
            
            if is_valid_transit:
                candidate = {
                    'index': len(valid_poi_candidates) + len(valid_place_candidates),
                    'name': place.get('name'),
                    'latitude': place.get('latitude'),
                    'longitude': place.get('longitude'),
                    'place_id': place.get('id'),
                    'source': 'PLACE'
                }
                valid_place_candidates.append(candidate)
        
        # Display Place candidates with index numbers
        print(f"\n   Found {len(valid_place_candidates)} valid Place transit candidates:")
        for candidate in valid_place_candidates:
            print(f"   [{candidate['index']}] {candidate['name']}")
            print(f"       Location: {candidate['latitude']:.6f}, {candidate['longitude']:.6f}")
            print(f"       Place ID: {candidate['place_id']}")
            print()
        
        # 3. Major Barbados locations (manual suggestions)
        print("3. MAJOR BARBADOS TRANSIT LOCATIONS (Manual Research):")
        print("-" * 54)
        
        known_major_locations = [
            "Bridgetown Bus Terminal", "Speightstown Terminal", "Oistins Terminal",
            "Six Roads", "Worthing", "Hastings", "St. Lawrence Gap",
            "Airport", "University of the West Indies", "Queen Elizabeth Hospital"
        ]
        
        location_matches = []
        for known_location in known_major_locations:
            # Search for matches in existing data
            poi_matches = [p for p in all_pois if known_location.lower() in p.get('name', '').lower()]
            place_matches = [p for p in all_places if known_location.lower() in p.get('name', '').lower()]
            
            if poi_matches or place_matches:
                location_matches.append({
                    'location': known_location,
                    'poi_matches': len(poi_matches),
                    'place_matches': len(place_matches),
                    'total_matches': len(poi_matches) + len(place_matches)
                })
        
        print("   Major locations found in database:")
        for match in location_matches:
            print(f"   - {match['location']}: {match['total_matches']} matches ({match['poi_matches']} POIs, {match['place_matches']} Places)")
        
        # 4. Summary with index reference
        print("\n" + "="*60)
        print("DEPOT CANDIDATE SUMMARY")
        print("="*60)
        
        all_candidates = valid_poi_candidates + valid_place_candidates
        
        print(f"Total valid transit candidates found: {len(all_candidates)}")
        print("\nCandidate List for Manual Confirmation:")
        print("(Use index numbers to confirm which are actual depots)")
        print()
        
        for candidate in all_candidates:
            source_type = f"({candidate['source']})"
            print(f"[{candidate['index']}] {candidate['name']} {source_type}")
        
        print(f"\nInstructions:")
        print(f"Please review the list above and provide the index numbers")
        print(f"of candidates that are confirmed as actual transit depots.")
        print(f"Example: 'Confirm indices: 0, 2, 5' for candidates 0, 2, and 5")
        
        # Save results for reference
        results = {
            'poi_candidates': valid_poi_candidates,
            'place_candidates': valid_place_candidates,
            'all_candidates': all_candidates,
            'total_count': len(all_candidates)
        }
        
        with open('depot_candidates.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Full candidate data saved to: depot_candidates.json")
        
        return results
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(find_valid_depot_candidates())