"""
UPDATE DEPOT COORDINATES WITH FULL PRECISION
============================================
Updates existing depots with full precision coordinates from the actual database.
"""

import requests
import json
import sys

def update_depot_coordinates_full_precision():
    """Update depot coordinates with full precision values."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    # Full precision coordinates from depot candidate analysis
    # Confirmed depots: indices 0, 2, 3, 4, 5 (excluding [1] Chicken Galore Depot)
    full_precision_depots = {
        "Speightstown Bus Terminal": {
            "latitude": 13.252068,
            "longitude": -59.642543
        },
        "Granville Williams Bus Terminal": {  # Note: removing "The" and "(Fairchild Street)"
            "latitude": 13.096108,
            "longitude": -59.612344
        },
        "Cheapside ZR and Minibus Terminal": {
            "latitude": 13.098168,
            "longitude": -59.621582
        },
        "Constitution River Terminal": {
            "latitude": 13.096538,
            "longitude": -59.608646
        },
        "Princess Alice Bus Terminal": {
            "latitude": 13.097766,
            "longitude": -59.621822
        }
    }
    
    try:
        print("🔍 Getting current depots to update coordinates...")
        
        # Get all current depots
        response = requests.get(f"{base_url}/depots", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Cannot access depot API: {response.status_code}")
            return False
        
        data = response.json()
        depots = data.get('data', [])
        
        print(f"📊 Found {len(depots)} existing depots to update")
        
        updated_count = 0
        
        for depot in depots:
            depot_id = depot.get('id')
            attrs = depot.get('attributes', {})
            current_name = attrs.get('name', '')
            
            print(f"\n🔍 Processing depot: {current_name} (ID: {depot_id})")
            
            # Find matching full precision coordinates
            matching_coords = None
            
            # Direct name match
            if current_name in full_precision_depots:
                matching_coords = full_precision_depots[current_name]
                print(f"✅ Direct name match found")
            else:
                # Partial name matching for variations
                for precision_name, coords in full_precision_depots.items():
                    if precision_name.lower() in current_name.lower() or current_name.lower() in precision_name.lower():
                        matching_coords = coords
                        print(f"✅ Partial name match found: {precision_name}")
                        break
            
            if not matching_coords:
                print(f"⚠️  No matching full precision coordinates found for: {current_name}")
                continue
            
            # Update depot with full precision coordinates
            current_lat = attrs.get('latitude')
            current_lon = attrs.get('longitude')
            new_lat = matching_coords['latitude']
            new_lon = matching_coords['longitude']
            
            print(f"📍 Current: {current_lat}, {current_lon}")
            print(f"📍 Updated: {new_lat}, {new_lon}")
            
            # Only update if coordinates actually changed
            if current_lat != new_lat or current_lon != new_lon:
                update_data = {
                    "data": {
                        "latitude": new_lat,
                        "longitude": new_lon,
                        # Keep all existing fields
                        "name": attrs.get('name'),
                        "depot_id": attrs.get('depot_id'),
                        "capacity": attrs.get('capacity'),
                        "is_active": attrs.get('is_active'),
                        "address": attrs.get('address')
                    }
                }
                
                response = requests.put(
                    f"{base_url}/depots/{depot_id}",
                    json=update_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"✅ Successfully updated coordinates for: {current_name}")
                    updated_count += 1
                else:
                    print(f"❌ Failed to update depot {current_name}: {response.status_code}")
                    print(f"Response: {response.text}")
            else:
                print(f"ℹ️  Coordinates already correct for: {current_name}")
                updated_count += 1
        
        print(f"\n📊 Updated {updated_count}/{len(depots)} depots with full precision coordinates")
        return updated_count > 0
        
    except Exception as e:
        print(f"❌ Error updating depot coordinates: {e}")
        return False

def verify_depot_coordinates():
    """Verify all depots now have full precision coordinates."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    try:
        print("\n🔍 Verifying depot coordinates...")
        
        response = requests.get(f"{base_url}/depots", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Cannot verify depot API: {response.status_code}")
            return False
        
        data = response.json()
        depots = data.get('data', [])
        
        print(f"\n📊 FINAL DEPOT COORDINATES VERIFICATION:")
        print("=" * 50)
        
        all_valid = True
        
        for depot in depots:
            attrs = depot.get('attributes', {})
            name = attrs.get('name', 'Unknown')
            latitude = attrs.get('latitude')
            longitude = attrs.get('longitude')
            
            # Check precision (should have more than 2 decimal places)
            lat_precision = len(str(latitude).split('.')[-1]) if latitude and '.' in str(latitude) else 0
            lon_precision = len(str(longitude).split('.')[-1]) if longitude and '.' in str(longitude) else 0
            
            precision_ok = lat_precision >= 6 and lon_precision >= 6
            
            status = "✅" if precision_ok else "❌"
            print(f"{status} {name}")
            print(f"   Coordinates: {latitude}, {longitude}")
            print(f"   Precision: {lat_precision} & {lon_precision} decimal places")
            
            if not precision_ok:
                all_valid = False
        
        print(f"\n🎯 VERIFICATION RESULT: {'ALL DEPOTS HAVE FULL PRECISION' if all_valid else 'SOME DEPOTS NEED COORDINATE FIXES'}")
        return all_valid
        
    except Exception as e:
        print(f"❌ Error verifying depot coordinates: {e}")
        return False

def main():
    """Update depot coordinates with full precision and verify."""
    print("=" * 60)
    print("🎯 DEPOT FULL PRECISION COORDINATE UPDATE")
    print("=" * 60)
    
    # Update coordinates
    update_success = update_depot_coordinates_full_precision()
    
    # Verify results
    verify_success = verify_depot_coordinates()
    
    if update_success and verify_success:
        print("\n🎉 SUCCESS! All depots now have full precision coordinates!")
        print("➡️  Ready for Step 4A validation with accurate coordinates")
        return True
    else:
        print("\n🚨 Some issues encountered during coordinate update")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)