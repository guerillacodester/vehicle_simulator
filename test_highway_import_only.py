#!/usr/bin/env python3
"""
Test ONLY the highway import (no deletion) to see debug output
"""

import requests
import json
import time

BASE_URL = "http://localhost:1337/api"

def main():
    print("=" * 60)
    print("HIGHWAY IMPORT ONLY TEST")
    print("=" * 60)
    
    # Find Barbados
    print("\n[COUNTRY] Finding Barbados (BB)...")
    countries_response = requests.get(f"{BASE_URL}/countries?filters[code][$eq]=BB")
    countries = countries_response.json()['data']
    
    if not countries:
        print("❌ Barbados not found!")
        return 1
    
    country = countries[0]
    country_id = country['documentId']
    print(f"✅ Found: Barbados (ID: {country_id})")
    
    # Upload file
    print("\n[UPLOAD] Uploading barbados_highway_sample10.json...")
    with open('e:/projects/github/vehicle_simulator/commuter_service/geojson_data/barbados_highway_sample10.json', 'rb') as f:
        files = {'files': ('barbados_highway_sample10.json', f, 'application/json')}
        upload_response = requests.post(f"{BASE_URL}/upload", files=files)
    
    uploaded_file = upload_response.json()[0]
    file_id = uploaded_file['id']
    print(f"✅ Uploaded (ID: {file_id})")
    
    # Set highways_geojson_file to trigger import
    print("\n[UPDATE] Setting highways_geojson_file to trigger import...")
    update_data = {
        "data": {
            "highways_geojson_file": file_id
        }
    }
    update_response = requests.put(
        f"{BASE_URL}/countries/{country_id}",
        json=update_data
    )
    print(f"✅ Import triggered")
    
    # Wait for processing
    print("\n[WAIT] Waiting 15 seconds for processing...")
    time.sleep(15)
    
    # Count results
    print("\n[COUNT] Checking results:")
    highways_response = requests.get(f"{BASE_URL}/highways?filters[country][documentId][$eq]={country_id}&pagination[pageSize]=1")
    highways_total = highways_response.json()['meta']['pagination']['total']
    
    shapes_response = requests.get(f"{BASE_URL}/highway-shapes?pagination[pageSize]=1")
    shapes_total = shapes_response.json()['meta']['pagination']['total']
    
    print(f"  highways: {highways_total}")
    print(f"  highway-shapes: {shapes_total}")
    
    if highways_total == 10 and shapes_total == 84:
        print("\n✅ IMPORT SUCCESSFUL")
        print("\nNOTE: Check Strapi console for debug output showing highway object structure")
        return 0
    else:
        print(f"\n❌ UNEXPECTED COUNTS (expected 10 highways, 84 shapes)")
        return 1

if __name__ == '__main__':
    exit(main())
