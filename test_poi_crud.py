#!/usr/bin/env python3
"""
Test POI (Amenities) CRUD operations
"""

import requests
import json
import time

# Configuration
STRAPI_URL = "http://localhost:1337"
API_URL = f"{STRAPI_URL}/api"
API_TOKEN = "b127418caf99e995d561f1c787005e328c8b9168e7fcc313460e43e032259a2b26d209b260b1dd8c0ca5dced2f20db90823984a50e2ec7429070552acad2b81f94bcad87ddf09e3314ded62538163e55e7f11a8909de45f67dd95890311211f5c1af76b86452a9e4f585ea9e4d3832e434c6cb46b97823c103801323a0214442"

POI_FILE = "E:/projects/github/vehicle_simulator/commuter_service/geojson_data/barbados_amenities.json"

session = requests.Session()
country_id = None

def find_country():
    global country_id
    print("\n[COUNTRY] Finding Barbados (BB)...")
    response = session.get(
        f"{API_URL}/countries",
        params={"filters[code][$eq]": "BB"},
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data["data"]:
            country_id = data["data"][0]["documentId"]
            print(f"✅ Found: {data['data'][0]['name']} (ID: {country_id})")
            return True
    print(f"❌ Failed to find country")
    return False

def upload_file(file_path):
    filename = file_path.split('/')[-1]
    print(f"\n[UPLOAD] Uploading {filename}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    response = session.post(
        f"{API_URL}/upload",
        files={'files': (filename, content, 'application/json')}
    )
    
    if response.status_code == 201:
        file_id = response.json()[0]["id"]
        print(f"✅ Uploaded (ID: {file_id})")
        return file_id
    print(f"❌ Upload failed: {response.status_code}")
    return None

def update_country(field_name, file_id):
    print(f"\n[UPDATE] Setting {field_name} to file {file_id}...")
    response = session.put(
        f"{API_URL}/countries/{country_id}",
        json={"data": {field_name: file_id}},
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    if response.status_code == 200:
        print(f"✅ Updated")
        return True
    print(f"❌ Failed: {response.status_code}")
    return False

def count_entities(entity_type):
    response = session.get(
        f"{API_URL}/{entity_type}",
        params={
            "filters[country][documentId][$eq]": country_id,
            "pagination[pageSize]": 1
        },
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    if response.status_code == 200:
        count = response.json()["meta"]["pagination"]["total"]
        print(f"  {entity_type}: {count}")
        return count
    return -1

def count_shapes(shape_type):
    response = session.get(
        f"{API_URL}/{shape_type}",
        params={"pagination[pageSize]": 1},
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    if response.status_code == 200:
        count = response.json()["meta"]["pagination"]["total"]
        print(f"  {shape_type}: {count}")
        return count
    return -1

def remove_file(field_name):
    print(f"\n[REMOVE] Removing {field_name}...")
    response = session.put(
        f"{API_URL}/countries/{country_id}",
        json={"data": {field_name: None}},
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    if response.status_code == 200:
        print(f"✅ Removed")
        return True
    print(f"❌ Failed: {response.status_code}")
    return False

def main():
    print("="*60)
    print("POI (AMENITIES) CRUD TEST")
    print("="*60)
    
    if not find_country():
        return False
    
    # Upload and create POIs
    file_id = upload_file(POI_FILE)
    if not file_id:
        return False
    
    if not update_country("pois_geojson_file", file_id):
        return False
    
    print("\n[WAIT] Waiting 10 seconds for processing...")
    time.sleep(10)
    
    # Verify creation
    print("\n[COUNT] Counting entities after upload:")
    poi_count = count_entities("pois")
    poi_shape_count = count_shapes("poi-shapes")
    
    if poi_count == 0:
        print("\n❌ TEST FAILED - No POIs created")
        return False
    
    print(f"\n✅ Created {poi_count} POIs with {poi_shape_count} shapes")
    
    # Delete POIs
    if not remove_file("pois_geojson_file"):
        return False
    
    print("\n[WAIT] Waiting 10 seconds for deletion...")
    time.sleep(10)
    
    # Verify deletion
    print("\n[COUNT] Counting entities after deletion:")
    poi_count = count_entities("pois")
    poi_shape_count = count_shapes("poi-shapes")
    
    if poi_count != 0 or poi_shape_count != 0:
        print(f"\n❌ TEST FAILED - Deletion incomplete (POIs: {poi_count}, Shapes: {poi_shape_count})")
        return False
    
    print("\n✅ All POIs and shapes deleted successfully")
    print("\n🎉 POI CRUD TEST PASSED!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
