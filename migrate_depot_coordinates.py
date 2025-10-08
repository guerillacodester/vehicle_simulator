"""
DEPOT COORDINATE MIGRATION SCRIPT
=================================
Migrates depot coordinates from location.lat/lon to latitude/longitude fields.
This script assumes the Strapi schema has been manually updated to include latitude/longitude fields.
"""

import requests
import json
import sys

def migrate_depot_coordinates():
    """Migrate existing depot from location object to latitude/longitude fields."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    try:
        print("🔄 Migrating depot coordinates...")
        
        # Get existing depot
        response = requests.get(f"{base_url}/depots", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Cannot access depot API: {response.status_code}")
            return False
        
        data = response.json()
        depots = data.get('data', [])
        
        if not depots:
            print("ℹ️  No existing depots to migrate")
            return True
        
        # Migrate the existing Bridgetown depot
        existing_depot = depots[0]
        depot_id = existing_depot.get('id')
        attrs = existing_depot.get('attributes', {})
        location = attrs.get('location', {})
        
        print(f"📍 Migrating depot: {attrs.get('name', 'Unknown')}")
        print(f"Current location: {location}")
        
        if not isinstance(location, dict) or 'lat' not in location or 'lon' not in location:
            print("❌ No valid coordinates in location field")
            return False
        
        # Extract coordinates
        latitude = location['lat']
        longitude = location['lon']
        
        print(f"Extracted coordinates: latitude={latitude}, longitude={longitude}")
        
        # Update depot with new schema fields
        update_data = {
            "data": {
                "latitude": latitude,
                "longitude": longitude,
                # Keep existing fields
                "name": attrs.get('name'),
                "depot_id": attrs.get('depot_id'),
                "capacity": attrs.get('capacity', 100),
                "is_active": attrs.get('is_active', True),
                "address": attrs.get('address')
            }
        }
        
        # Remove location field (set to null)
        # Note: This requires the schema to allow location to be nullable
        
        response = requests.put(
            f"{base_url}/depots/{depot_id}",
            json=update_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Successfully migrated depot coordinates")
            result = response.json()
            new_attrs = result.get('data', {}).get('attributes', {})
            print(f"New structure: latitude={new_attrs.get('latitude')}, longitude={new_attrs.get('longitude')}")
            return True
        else:
            print(f"❌ Failed to update depot: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error migrating depot coordinates: {e}")
        return False

def create_confirmed_depots():
    """Create the 5 confirmed transit depots."""
    base_url = "http://localhost:1337/api" 
    headers = {"Content-Type": "application/json"}
    
    confirmed_depots = [
        {
            "name": "Speightstown Bus Terminal",
            "depot_id": "SPT_NORTH_01", 
            "latitude": 13.252068,
            "longitude": -59.642543,
            "capacity": 60,
            "is_active": True,
            "address": "Speightstown, St. Peter"
        },
        {
            "name": "Granville Williams Bus Terminal",
            "depot_id": "BGI_FAIRCHILD_02",
            "latitude": 13.096108,
            "longitude": -59.612344,
            "capacity": 80,
            "is_active": True,
            "address": "Fairchild Street, Bridgetown"
        },
        {
            "name": "Cheapside ZR and Minibus Terminal", 
            "depot_id": "BGI_CHEAPSIDE_03",
            "latitude": 13.098168,
            "longitude": -59.621582,
            "capacity": 70,
            "is_active": True,
            "address": "Cheapside, Bridgetown"
        },
        {
            "name": "Constitution River Terminal",
            "depot_id": "BGI_CONSTITUTION_04",
            "latitude": 13.096538, 
            "longitude": -59.608646,
            "capacity": 50,
            "is_active": True,
            "address": "Constitution River, Bridgetown"
        },
        {
            "name": "Princess Alice Bus Terminal",
            "depot_id": "BGI_PRINCESS_05",
            "latitude": 13.097766,
            "longitude": -59.621822,
            "capacity": 65,
            "is_active": True,
            "address": "Princess Alice Highway, Bridgetown"
        }
    ]
    
    print(f"🚀 Creating {len(confirmed_depots)} confirmed transit depots...")
    
    success_count = 0
    for depot in confirmed_depots:
        try:
            depot_data = {"data": depot}
            
            response = requests.post(
                f"{base_url}/depots",
                json=depot_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Created: {depot['name']}")
                success_count += 1
            else:
                print(f"❌ Failed to create {depot['name']}: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception creating {depot['name']}: {e}")
    
    print(f"📊 Successfully created {success_count}/{len(confirmed_depots)} depots")
    return success_count == len(confirmed_depots)

def main():
    """Execute depot migration and creation."""
    print("=" * 60)
    print("🔧 DEPOT COORDINATE MIGRATION & CREATION")
    print("=" * 60)
    
    # Step 1: Migrate existing depot
    print("STEP 1: Migrating existing depot coordinates...")
    migration_success = migrate_depot_coordinates()
    
    # Step 2: Create confirmed depots
    print("\nSTEP 2: Creating confirmed transit depots...")
    creation_success = create_confirmed_depots()
    
    # Results
    print("\n" + "="*60)
    print("📊 MIGRATION & CREATION RESULTS")
    print("="*60)
    
    if migration_success and creation_success:
        print("🎉 SUCCESS! All depot operations completed!")
        print("✅ Existing depot migrated to new schema")
        print("✅ 5 confirmed transit depots created")
        print("➡️  Ready for Step 4A validation")
        return True
    else:
        print("🚨 PARTIAL SUCCESS - Some operations failed") 
        if not migration_success:
            print("❌ Existing depot migration failed")
        if not creation_success:
            print("❌ Confirmed depot creation failed")
        print("⚠️  Manual schema fix may be required in Strapi Admin")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)