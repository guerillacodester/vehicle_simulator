#!/usr/bin/env python3
"""
Test Places relationships after successful import
"""

import httpx

def test_places_relationships():
    print('🔍 Testing Places Relationships')
    print('=' * 40)

    # Test Places with country relationship
    response = httpx.get('http://localhost:1337/api/places?populate=country&pagination[pageSize]=3')
    if response.status_code == 200:
        places = response.json().get('data', [])
        print(f'✅ Found {len(places)} sample places with country data')
        
        for i, place in enumerate(places[:3]):
            country = place.get('country', {})
            name = place.get('name', 'N/A')
            place_type = place.get('place_type', 'N/A')
            country_name = country.get('name', 'Not linked')
            country_id = country.get('id', 'N/A')
            
            print(f'  Place {i+1}: "{name}" (type: {place_type})')
            print(f'           Country: {country_name} (ID: {country_id})')

    # Test country filtering
    response = httpx.get('http://localhost:1337/api/places?filters[country][id][$eq]=29&pagination[pageSize]=5')
    if response.status_code == 200:
        filtered_places = len(response.json().get('data', []))
        print(f'\n✅ Country filtering works: {filtered_places} places for Barbados')
    else:
        print(f'\n❌ Country filtering failed: {response.status_code}')
    
    # Test total count
    response = httpx.get('http://localhost:1337/api/places')
    if response.status_code == 200:
        total_places = len(response.json().get('data', []))
        print(f'📊 Total places in system: {total_places}')

if __name__ == "__main__":
    test_places_relationships()