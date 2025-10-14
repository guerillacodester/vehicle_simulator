#!/usr/bin/env python3
"""
Cleanup script to delete all highways and highway-shapes for Barbados
"""

import requests

# Configuration
STRAPI_URL = "http://localhost:1337"
API_URL = f"{STRAPI_URL}/api"
API_TOKEN = "b127418caf99e995d561f1c787005e328c8b9168e7fcc313460e43e032259a2b26d209b260b1dd8c0ca5dced2f20db90823984a50e2ec7429070552acad2b81f94bcad87ddf09e3314ded62538163e55e7f11a8909de45f67dd95890311211f5c1af76b86452a9e4f585ea9e4d3832e434c6cb46b97823c103801323a0214442"

session = requests.Session()

def find_country():
    print("\n[FIND] Finding Barbados (BB)...")
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
            return country_id
    print(f"❌ Failed to find country")
    return None

def delete_all_highways(country_id=None):
    print("\n[DELETE] Deleting ALL highways in database...")
    
    # Keep deleting until there are no more highways
    total_deleted = 0
    while True:
        # Get a batch of highways (max 100 at a time due to API limits)
        response = session.get(
            f"{API_URL}/highways",
            params={
                "pagination[pageSize]": 100
            },
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch highways: {response.status_code}")
            return False
        
        data = response.json()
        highways = data["data"]
        total = data["meta"]["pagination"]["total"]
        
        if not highways:
            print(f"✅ No more highways to delete")
            break
        
        print(f"📊 Found {total} total highways, deleting batch of {len(highways)}...")
        
        # Delete this batch
        for highway in highways:
            doc_id = highway["documentId"]
            response = session.delete(
                f"{API_URL}/highways/{doc_id}",
                headers={"Authorization": f"Bearer {API_TOKEN}"}
            )
            
            if response.status_code in [200, 204]:
                total_deleted += 1
            else:
                print(f"❌ Failed to delete highway {doc_id}: {response.status_code}")
        
        print(f"  Progress: {total_deleted} highways deleted so far...")
    
    print(f"✅ Deleted {total_deleted} total highways")
    return True

def delete_orphaned_shapes():
    print("\n[DELETE] Checking for orphaned highway-shapes...")
    
    # Get count of all shapes
    response = session.get(
        f"{API_URL}/highway-shapes",
        params={"pagination[pageSize]": 1},
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch shapes: {response.status_code}")
        return False
    
    total = response.json()["meta"]["pagination"]["total"]
    print(f"📊 Found {total} highway-shapes")
    
    if total == 0:
        print("✅ No shapes to delete")
        return True
    
    # Fetch all shapes in batches
    page_size = 100
    deleted = 0
    page = 1
    
    while True:
        response = session.get(
            f"{API_URL}/highway-shapes",
            params={
                "pagination[page]": page,
                "pagination[pageSize]": page_size
            },
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if response.status_code != 200:
            break
        
        shapes = response.json()["data"]
        if not shapes:
            break
        
        for shape in shapes:
            doc_id = shape["documentId"]
            response = session.delete(
                f"{API_URL}/highway-shapes/{doc_id}",
                headers={"Authorization": f"Bearer {API_TOKEN}"}
            )
            
            if response.status_code in [200, 204]:
                deleted += 1
                if deleted % 100 == 0:
                    print(f"  Progress: {deleted}/{total} shapes deleted")
        
        page += 1
    
    print(f"✅ Deleted {deleted} highway-shapes")
    return True

def main():
    print("="*60)
    print("HIGHWAY CLEANUP SCRIPT")
    print("="*60)
    
    # Delete all highways regardless of country
    if not delete_all_highways():
        return False
    
    # Clean up any orphaned shapes
    delete_orphaned_shapes()
    
    print("\n🎉 CLEANUP COMPLETE!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
