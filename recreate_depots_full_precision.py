"""
DELETE AND RECREATE DEPOTS WITH FULL PRECISION
==============================================
Deletes existing depots and recreates them after schema precision fix.
"""

import requests
import json
import sys

def delete_all_depots():
    """Delete all existing depots."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    try:
        print("🗑️  Deleting all existing depots...")
        
        # Get all depots
        response = requests.get(f"{base_url}/depots?populate=*", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Cannot access depots: {response.status_code}")
            return False
        
        data = response.json()
        depots = data.get('data', [])
        
        print(f"📊 Found {len(depots)} depots to delete")
        
        deleted_count = 0
        for depot in depots:
            depot_id = depot.get('id')
            name = depot.get('name', 'Unknown')
            
            try:
                response = requests.delete(f"{base_url}/depots/{depot_id}", headers=headers, timeout=10)
                
                if response.status_code in [200, 204]:
                    print(f"✅ Deleted: {name} (ID: {depot_id})")
                    deleted_count += 1
                else:
                    print(f"❌ Failed to delete {name}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Exception deleting {name}: {e}")
        
        print(f"📊 Deleted {deleted_count}/{len(depots)} depots")
        return deleted_count == len(depots)
        
    except Exception as e:
        print(f"❌ Error deleting depots: {e}")
        return False

def create_full_precision_depots():
    """Create depots with full precision coordinates after schema fix."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    # Full precision coordinates from depot candidate analysis 
    confirmed_depots = [
        {
            "name": "Speightstown Bus Terminal",
            "depot_id": "SPT_NORTH_01",
            "latitude": 13.252068,  # Full precision
            "longitude": -59.642543,
            "capacity": 60,
            "is_active": True,
            "address": "Speightstown, St. Peter"
        },
        {
            "name": "Granville Williams Bus Terminal", 
            "depot_id": "BGI_FAIRCHILD_02",
            "latitude": 13.096108,  # Full precision
            "longitude": -59.612344,
            "capacity": 80,
            "is_active": True,
            "address": "Fairchild Street, Bridgetown"
        },
        {
            "name": "Cheapside ZR and Minibus Terminal",
            "depot_id": "BGI_CHEAPSIDE_03", 
            "latitude": 13.098168,  # Full precision
            "longitude": -59.621582,
            "capacity": 70,
            "is_active": True,
            "address": "Cheapside, Bridgetown"
        },
        {
            "name": "Constitution River Terminal",
            "depot_id": "BGI_CONSTITUTION_04",
            "latitude": 13.096538,  # Full precision
            "longitude": -59.608646,
            "capacity": 50,
            "is_active": True,
            "address": "Constitution River, Bridgetown"
        },
        {
            "name": "Princess Alice Bus Terminal",
            "depot_id": "BGI_PRINCESS_05",
            "latitude": 13.097766,  # Full precision
            "longitude": -59.621822,
            "capacity": 65,
            "is_active": True,
            "address": "Princess Alice Highway, Bridgetown"
        }
    ]
    
    print(f"\n🚀 Creating {len(confirmed_depots)} depots with FULL PRECISION after schema fix...")
    
    success_count = 0
    
    for i, depot in enumerate(confirmed_depots, 1):
        try:
            print(f"\n[{i}/{len(confirmed_depots)}] Creating: {depot['name']}")
            print(f"   📍 Full precision: {depot['latitude']}, {depot['longitude']}")
            
            depot_data = {"data": depot}
            
            response = requests.post(
                f"{base_url}/depots",
                json=depot_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"   ✅ SUCCESS")
                success_count += 1
            else:
                print(f"   ❌ FAILED: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
    
    print(f"\n📊 Created {success_count}/{len(confirmed_depots)} depots")
    return success_count == len(confirmed_depots)

def verify_full_precision():
    """Verify depots now have full precision coordinates."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    try:
        print(f"\n🔍 VERIFYING FULL PRECISION COORDINATES:")
        print("=" * 50)
        
        response = requests.get(f"{base_url}/depots?populate=*", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Cannot verify: {response.status_code}")
            return False
        
        data = response.json()
        depots = data.get('data', [])
        
        all_precise = True
        
        for depot in depots:
            name = depot.get('name', 'Unknown')
            latitude = depot.get('latitude')
            longitude = depot.get('longitude')
            
            # Check precision
            lat_str = str(latitude) if latitude else ""
            lon_str = str(longitude) if longitude else ""
            
            lat_precision = len(lat_str.split('.')[-1]) if '.' in lat_str else 0
            lon_precision = len(lon_str.split('.')[-1]) if '.' in lon_str else 0
            
            precision_ok = lat_precision >= 6 and lon_precision >= 6
            
            print(f"{'✅' if precision_ok else '❌'} {name}")
            print(f"   Coordinates: {latitude}, {longitude}")
            print(f"   Precision: {lat_precision}, {lon_precision} decimal places")
            
            if not precision_ok:
                all_precise = False
        
        return all_precise
        
    except Exception as e:
        print(f"❌ Error verifying: {e}")
        return False

def main():
    """Delete and recreate depots with full precision."""
    print("=" * 70)
    print("🔄 DELETE AND RECREATE DEPOTS WITH FULL PRECISION")
    print("=" * 70)
    
    # Step 1: Delete existing depots
    delete_success = delete_all_depots()
    
    if not delete_success:
        print("❌ Failed to delete existing depots")
        return False
    
    # Step 2: Create new depots with full precision 
    create_success = create_full_precision_depots()
    
    # Step 3: Verify precision
    verify_success = verify_full_precision()
    
    print(f"\n{'='*70}")
    print("🎯 FINAL RESULTS:")
    print("=" * 70)
    
    if create_success and verify_success:
        print("🎉 SUCCESS! All depots recreated with FULL PRECISION coordinates!")
        print("✅ Schema precision fix applied successfully")
        print("✅ All 5 confirmed transit depots created")
        print("✅ Full 6+ decimal place precision maintained")
        print("➡️  READY FOR STEP 4A VALIDATION")
        return True
    else:
        print("🚨 ISSUES FOUND:")
        if not create_success:
            print("❌ Depot creation failed")
        if not verify_success:
            print("❌ Precision verification failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)