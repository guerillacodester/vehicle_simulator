"""
DIRECT DEPOT VERIFICATION
========================
Directly checks depot data to see if coordinates are actually stored.
"""

import requests
import json
import sys

def check_depot_data_directly():
    """Check depot data directly with full population."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    try:
        print("🔍 Checking depot data with populate all fields...")
        
        # Try with populate parameter to get all fields
        response = requests.get(f"{base_url}/depots?populate=*", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Cannot access depot API: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        depots = data.get('data', [])
        
        print(f"📊 Found {len(depots)} depots")
        
        for i, depot in enumerate(depots, 1):
            print(f"\n[{i}] DEPOT ID: {depot.get('id')}")
            print(f"Raw depot data:")
            print(json.dumps(depot, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking depot data: {e}")
        return False

def check_individual_depot(depot_id):
    """Check individual depot by ID."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    try:
        print(f"\n🔍 Checking individual depot {depot_id}...")
        
        response = requests.get(f"{base_url}/depots/{depot_id}", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Cannot access depot {depot_id}: {response.status_code}")
            return False
        
        depot = response.json()
        print(f"Individual depot {depot_id} data:")
        print(json.dumps(depot, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking depot {depot_id}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 DIRECT DEPOT DATA VERIFICATION")
    print("=" * 60)
    
    # Check all depots
    check_depot_data_directly()
    
    # Check individual depots
    for depot_id in [8, 9, 10, 11, 12]:
        check_individual_depot(depot_id)