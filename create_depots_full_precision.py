"""
CREATE CONFIRMED DEPOTS WITH FULL PRECISION COORDINATES
======================================================
Creates the 5 confirmed transit depots using exact coordinates from database analysis.
"""

import requests
import json
import sys

def create_confirmed_depots_full_precision():
    """Create confirmed transit depots with full precision coordinates."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    # Full precision coordinates from depot candidate analysis
    # Confirmed valid depots: indices 0, 2, 3, 4, 5 (excluding [1] Chicken Galore Depot)
    confirmed_depots = [
        {
            "name": "Speightstown Bus Terminal",
            "depot_id": "SPT_NORTH_01",
            "latitude": 13.252068,  # Full precision from POI ID: 9936
            "longitude": -59.642543,
            "capacity": 60,
            "is_active": True,
            "address": "Speightstown, St. Peter"
        },
        {
            "name": "Granville Williams Bus Terminal",
            "depot_id": "BGI_FAIRCHILD_02", 
            "latitude": 13.096108,  # Full precision from POI ID: 10397
            "longitude": -59.612344,
            "capacity": 80,
            "is_active": True,
            "address": "Fairchild Street, Bridgetown"
        },
        {
            "name": "Cheapside ZR and Minibus Terminal",
            "depot_id": "BGI_CHEAPSIDE_03",
            "latitude": 13.098168,  # Full precision from POI ID: 10852
            "longitude": -59.621582,
            "capacity": 70,
            "is_active": True,
            "address": "Cheapside, Bridgetown"
        },
        {
            "name": "Constitution River Terminal",
            "depot_id": "BGI_CONSTITUTION_04",
            "latitude": 13.096538,  # Full precision from POI ID: 10982
            "longitude": -59.608646,
            "capacity": 50,
            "is_active": True,
            "address": "Constitution River, Bridgetown"
        },
        {
            "name": "Princess Alice Bus Terminal", 
            "depot_id": "BGI_PRINCESS_05",
            "latitude": 13.097766,  # Full precision from POI ID: 11098
            "longitude": -59.621822,
            "capacity": 65,
            "is_active": True,
            "address": "Princess Alice Highway, Bridgetown"
        }
    ]
    
    print(f"🚀 Creating {len(confirmed_depots)} confirmed transit depots with full precision coordinates...")
    print("=" * 80)
    
    success_count = 0
    
    for i, depot in enumerate(confirmed_depots, 1):
        try:
            print(f"\n🏗️  [{i}/{len(confirmed_depots)}] Creating: {depot['name']}")
            print(f"   📍 Coordinates: {depot['latitude']}, {depot['longitude']}")
            print(f"   🏢 Capacity: {depot['capacity']} vehicles")
            print(f"   📍 Address: {depot['address']}")
            
            depot_data = {"data": depot}
            
            response = requests.post(
                f"{base_url}/depots",
                json=depot_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                created_depot = result.get('data', {})
                created_id = created_depot.get('id')
                created_attrs = created_depot.get('attributes', {})
                
                print(f"   ✅ SUCCESS - Created depot (ID: {created_id})")
                print(f"   📊 Verified coordinates: {created_attrs.get('latitude')}, {created_attrs.get('longitude')}")
                success_count += 1
            else:
                print(f"   ❌ FAILED - HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION - {e}")
    
    print(f"\n{'='*80}")
    print(f"📊 DEPOT CREATION RESULTS: {success_count}/{len(confirmed_depots)} successful")
    
    return success_count == len(confirmed_depots)

def verify_all_depots_created():
    """Verify all depots were created successfully with correct coordinates."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    try:
        print("\n🔍 VERIFYING ALL CREATED DEPOTS:")
        print("=" * 50)
        
        response = requests.get(f"{base_url}/depots", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Cannot access depot API: {response.status_code}")
            return False
        
        data = response.json()
        depots = data.get('data', [])
        
        print(f"📊 Total depots found: {len(depots)}")
        
        if len(depots) != 5:
            print(f"⚠️  Expected 5 depots, found {len(depots)}")
        
        all_valid = True
        
        for i, depot in enumerate(depots, 1):
            attrs = depot.get('attributes', {})
            name = attrs.get('name', 'Unknown')
            depot_id_field = attrs.get('depot_id', '')
            latitude = attrs.get('latitude')
            longitude = attrs.get('longitude')
            capacity = attrs.get('capacity')
            is_active = attrs.get('is_active')
            
            print(f"\n[{i}] {name}")
            print(f"    ID: {depot.get('id')} | Depot ID: {depot_id_field}")
            print(f"    📍 Coordinates: {latitude}, {longitude}")
            print(f"    🏢 Capacity: {capacity} | Active: {is_active}")
            
            # Validate coordinate precision (should be 6+ decimal places)
            lat_str = str(latitude) if latitude else ""
            lon_str = str(longitude) if longitude else ""
            
            lat_precision = len(lat_str.split('.')[-1]) if '.' in lat_str else 0
            lon_precision = len(lon_str.split('.')[-1]) if '.' in lon_str else 0
            
            if lat_precision >= 6 and lon_precision >= 6:
                print(f"    ✅ Full precision coordinates ({lat_precision}, {lon_precision} decimal places)")
            else:
                print(f"    ❌ Low precision coordinates ({lat_precision}, {lon_precision} decimal places)")
                all_valid = False
            
            # Validate Barbados bounds
            if latitude and longitude:
                valid_lat = 13.0 <= latitude <= 13.35
                valid_lon = -59.65 <= longitude <= -59.4
                
                bounds_ok = valid_lat and valid_lon
                print(f"    {'✅' if bounds_ok else '❌'} Within Barbados bounds: {bounds_ok}")
                
                if not bounds_ok:
                    all_valid = False
        
        print(f"\n🎯 OVERALL VALIDATION: {'✅ ALL DEPOTS VALID' if all_valid else '❌ SOME ISSUES FOUND'}")
        return all_valid and len(depots) == 5
        
    except Exception as e:
        print(f"❌ Error verifying depots: {e}")
        return False

def main():
    """Create and verify all confirmed depots."""
    print("=" * 80)
    print("🏗️  CONFIRMED DEPOT CREATION WITH FULL PRECISION")
    print("=" * 80)
    
    # Create depots
    creation_success = create_confirmed_depots_full_precision()
    
    # Verify results
    verification_success = verify_all_depots_created()
    
    print(f"\n{'='*80}")
    print("🎯 FINAL RESULTS:")
    print("=" * 80)
    
    if creation_success and verification_success:
        print("🎉 SUCCESS! All 5 confirmed depots created with full precision coordinates!")
        print("✅ Schema fix completed")
        print("✅ All depots have 6+ decimal place precision") 
        print("✅ All coordinates within Barbados bounds")
        print("➡️  READY FOR STEP 4A VALIDATION")
        return True
    else:
        print("🚨 ISSUES ENCOUNTERED:")
        if not creation_success:
            print("❌ Depot creation had failures")
        if not verification_success:
            print("❌ Depot verification found issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)