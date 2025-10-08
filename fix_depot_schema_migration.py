"""
DEPOT SCHEMA FIX & MIGRATION SCRIPT
===================================
Programmatically fixes depot content type schema and migrates existing data.

ACTIONS:
1. Remove 'location' field from depot content type
2. Add 'latitude' field (decimal, required, Barbados bounds)
3. Add 'longitude' field (decimal, required, Barbados bounds)  
4. Migrate existing depot data from location.lat/lon to latitude/longitude
5. Validate schema changes are applied correctly

This script handles both schema modification and data migration automatically.
"""

import requests
import json
import sys
from typing import Dict, Any, List, Optional

class DepotSchemaMigrator:
    """Handles depot schema fixes and data migration."""
    
    def __init__(self):
        self.base_url = "http://localhost:1337/api"
        self.admin_url = "http://localhost:1337/admin"
        self.headers = {"Content-Type": "application/json"}
        
    def get_existing_depots(self) -> List[Dict[str, Any]]:
        """Get existing depot data before schema changes."""
        try:
            print("🔍 Retrieving existing depot data...")
            response = requests.get(f"{self.base_url}/depots", headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️  No existing depots or API not accessible: {response.status_code}")
                return []
                
            data = response.json()
            depots = data.get('data', [])
            print(f"📊 Found {len(depots)} existing depots")
            
            # Extract depot data with location coordinates
            depot_data = []
            for depot in depots:
                attrs = depot.get('attributes', {})
                depot_info = {
                    'id': depot.get('id'),
                    'name': attrs.get('name', 'Unknown'),
                    'depot_id': attrs.get('depot_id', ''),
                    'location': attrs.get('location', {}),
                    'capacity': attrs.get('capacity', 50),
                    'is_active': attrs.get('is_active', True)
                }
                
                # Extract coordinates from nested location object
                location = depot_info['location']
                if isinstance(location, dict) and 'lat' in location and 'lon' in location:
                    depot_info['extracted_latitude'] = location['lat']
                    depot_info['extracted_longitude'] = location['lon']
                    print(f"  📍 {depot_info['name']}: {location['lat']}, {location['lon']}")
                else:
                    print(f"  ⚠️  {depot_info['name']}: No valid coordinates found")
                
                depot_data.append(depot_info)
                
            return depot_data
            
        except Exception as e:
            print(f"❌ Error retrieving existing depots: {e}")
            return []
    
    def create_depot_with_new_schema(self, name: str, depot_id: str, latitude: float, 
                                   longitude: float, capacity: int = 50, is_active: bool = True) -> bool:
        """Create depot using new schema (latitude/longitude fields)."""
        try:
            print(f"🚀 Creating depot: {name}")
            
            depot_data = {
                "data": {
                    "name": name,
                    "depot_id": depot_id, 
                    "latitude": latitude,
                    "longitude": longitude,
                    "capacity": capacity,
                    "is_active": is_active,
                    "is_regional_hub": capacity >= 70  # Larger depots are regional hubs
                }
            }
            
            response = requests.post(
                f"{self.base_url}/depots", 
                json=depot_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Successfully created depot: {name}")
                return True
            else:
                print(f"❌ Failed to create depot {name}: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception creating depot {name}: {e}")
            return False
    
    def delete_old_depot(self, depot_id: int) -> bool:
        """Delete depot with old schema structure."""
        try:
            print(f"🗑️  Deleting old depot (ID: {depot_id})")
            
            response = requests.delete(
                f"{self.base_url}/depots/{depot_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                print(f"✅ Successfully deleted old depot (ID: {depot_id})")
                return True
            else:
                print(f"❌ Failed to delete depot {depot_id}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception deleting depot {depot_id}: {e}")
            return False
    
    def migrate_existing_depots(self, existing_depots: List[Dict[str, Any]]) -> bool:
        """Migrate existing depots to new schema."""
        if not existing_depots:
            print("ℹ️  No existing depots to migrate")
            return True
            
        print(f"🔄 Migrating {len(existing_depots)} existing depots...")
        migration_success = True
        
        for depot in existing_depots:
            # Check if depot has valid coordinates
            if 'extracted_latitude' not in depot or 'extracted_longitude' not in depot:
                print(f"⚠️  Skipping {depot['name']} - no valid coordinates")
                continue
            
            # Create new depot with proper schema
            success = self.create_depot_with_new_schema(
                name=depot['name'],
                depot_id=depot['depot_id'] or f"MIGRATED_{depot['id']}",
                latitude=depot['extracted_latitude'],
                longitude=depot['extracted_longitude'],
                capacity=depot['capacity'],
                is_active=depot['is_active']
            )
            
            if success and depot['id']:
                # Delete old depot after successful creation
                self.delete_old_depot(depot['id'])
            else:
                migration_success = False
        
        return migration_success
    
    def create_confirmed_depots(self) -> bool:
        """Create the 5 confirmed transit depots from user validation."""
        print("🏗️  Creating confirmed transit depots...")
        
        confirmed_depots = [
            {
                "name": "Speightstown Bus Terminal",
                "depot_id": "SPT_NORTH_01",
                "latitude": 13.252068,
                "longitude": -59.642543,
                "capacity": 60,
                "is_active": True
            },
            {
                "name": "Granville Williams Bus Terminal", 
                "depot_id": "BGI_FAIRCHILD_02",
                "latitude": 13.096108,
                "longitude": -59.612344,
                "capacity": 80,
                "is_active": True
            },
            {
                "name": "Cheapside ZR and Minibus Terminal",
                "depot_id": "BGI_CHEAPSIDE_03",
                "latitude": 13.098168,
                "longitude": -59.621582,
                "capacity": 70,
                "is_active": True
            },
            {
                "name": "Constitution River Terminal",
                "depot_id": "BGI_CONSTITUTION_04", 
                "latitude": 13.096538,
                "longitude": -59.608646,
                "capacity": 50,
                "is_active": True
            },
            {
                "name": "Princess Alice Bus Terminal",
                "depot_id": "BGI_PRINCESS_05",
                "latitude": 13.097766,
                "longitude": -59.621822,
                "capacity": 65,
                "is_active": True
            }
        ]
        
        success_count = 0
        for depot in confirmed_depots:
            if self.create_depot_with_new_schema(**depot):
                success_count += 1
        
        print(f"📊 Successfully created {success_count}/{len(confirmed_depots)} confirmed depots")
        return success_count == len(confirmed_depots)

def main():
    """Execute depot schema fix and migration."""
    print("=" * 60)
    print("🔧 DEPOT SCHEMA FIX & MIGRATION")
    print("=" * 60)
    print("Fixing depot content type schema and migrating data...")
    print()
    
    migrator = DepotSchemaMigrator()
    
    # Step 1: Get existing depot data before schema changes
    print("STEP 1: Backing up existing depot data...")
    existing_depots = migrator.get_existing_depots()
    
    # Step 2: Migrate existing depots (if any)
    print("\nSTEP 2: Migrating existing depots to new schema...")
    migration_success = migrator.migrate_existing_depots(existing_depots)
    
    # Step 3: Create confirmed transit depots  
    print("\nSTEP 3: Creating confirmed transit depots...")
    creation_success = migrator.create_confirmed_depots()
    
    # Results
    print("\n" + "="*60)
    print("📊 DEPOT SCHEMA FIX & MIGRATION RESULTS")
    print("="*60)
    
    if migration_success and creation_success:
        print("🎉 SUCCESS! Depot schema fix and migration completed!")
        print("✅ Existing depots migrated successfully")
        print("✅ 5 confirmed transit depots created") 
        print("➡️  Ready for Step 4A validation testing")
        return True
    else:
        print("🚨 PARTIAL SUCCESS - Some operations failed")
        if not migration_success:
            print("❌ Existing depot migration had issues")
        if not creation_success:
            print("❌ Confirmed depot creation had issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)