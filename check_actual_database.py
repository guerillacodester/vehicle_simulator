#!/usr/bin/env python3
"""Check actual database contents"""

import requests
import json

def check_database():
    try:
        base_url = "http://localhost:1337/api"
        
        # Check countries
        countries_resp = requests.get(f"{base_url}/countries")
        countries = countries_resp.json()
        print(f"Countries: {len(countries.get('data', []))}")
        
        # Check total counts with high pagination limit
        endpoints = [
            ("pois", "POIs"),
            ("places", "Places"), 
            ("landuse-zones", "Landuse"),
            ("regions", "Regions")
        ]
        
        total_records = 0
        print("\n🗄️  ACTUAL DATABASE TOTALS:")
        
        for endpoint, name in endpoints:
            try:
                resp = requests.get(f"{base_url}/{endpoint}?pagination[limit]=20000")
                data = resp.json()
                count = len(data.get('data', []))
                total_records += count
                print(f"  📊 {name}: {count}")
                
                # Check pagination info
                meta = data.get('meta', {}).get('pagination', {})
                if meta:
                    print(f"      Total available: {meta.get('total', 'unknown')}")
                    print(f"      Page size: {meta.get('pageSize', 'unknown')}")
                
            except Exception as e:
                print(f"  ❌ {name}: Error - {e}")
        
        print(f"\n🎯 TOTAL RECORDS: {total_records}")
        
        # Sample some data
        print("\n📋 SAMPLE DATA:")
        try:
            pois_resp = requests.get(f"{base_url}/pois?pagination[limit]=3")
            pois_data = pois_resp.json().get('data', [])
            for i, poi in enumerate(pois_data[:2]):
                print(f"  📍 POI {i+1}: {poi.get('name', 'Unknown')} ({poi.get('amenity_type', 'unknown type')})")
                
        except Exception as e:
            print(f"  ❌ Sample POI error: {e}")
            
        try:
            places_resp = requests.get(f"{base_url}/places?pagination[limit]=3")
            places_data = places_resp.json().get('data', [])
            for i, place in enumerate(places_data[:2]):
                print(f"  🏘️  Place {i+1}: {place.get('name', 'Unknown')} ({place.get('place_type', 'unknown type')})")
                
        except Exception as e:
            print(f"  ❌ Sample Place error: {e}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Is Strapi running on localhost:1337?")

if __name__ == "__main__":
    check_database()