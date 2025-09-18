"""
Vehicle Migration Test Script
============================
Migrate vehicles from remote database to local Strapi, mapping relationships properly.
This tests vehicle CRUD operations and relationship handling via Strapi API.
"""
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import paramiko
import threading
import socket
import time
import json
from typing import Dict, List, Any, Set, Optional
import sys
import os

# Add the current directory to Python path to import from migrate_data
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel

class VehicleMigrator:
    """Migrate vehicles from remote to local Strapi with relationship mapping"""
    
    def __init__(self):
        self.strapi_base_url = "http://localhost:1337/api"
        self.strapi_admin_url = "http://localhost:1337/admin"
        
        # Remote database configuration (via SSH tunnel)
        self.ssh_config = {
            'ssh_host': 'arknetglobal.com',
            'ssh_port': 22,
            'ssh_user': 'david',
            'ssh_pass': 'Cabbyminnie5!',
            'remote_host': 'localhost',
            'remote_port': 5432,
            'local_port': 6543
        }
        
        self.remote_config = {
            'host': '127.0.0.1',
            'port': 6543,
            'database': 'arknettransit',
            'user': 'david',
            'password': 'Ga25w123!'
        }
        
        self.tunnel = None
        self.remote_conn = None
        
        # Mapping dictionaries for relationships
        self.country_mapping = {}  # remote_country_id -> strapi_country_id
        self.vehicle_status_mapping = {}  # remote_status -> strapi_status_id
    
    def connect_remote_database(self):
        """Connect to remote database via SSH tunnel"""
        print("🔗 Setting up SSH tunnel to remote database...")
        try:
            self.tunnel = SSHTunnel(**self.ssh_config)
            self.tunnel.start()
            time.sleep(2)  # Give tunnel time to establish
            
            print("📡 Connecting to remote database...")
            self.remote_conn = psycopg2.connect(**self.remote_config, cursor_factory=RealDictCursor)
            print("✅ Remote database connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Remote database connection failed: {e}")
            return False
    
    def check_strapi_connection(self):
        """Check if Strapi is running and accessible"""
        print("🔐 Checking Strapi connection...")
        
        try:
            response = requests.get(f"{self.strapi_admin_url}/init", timeout=5)
            if response.status_code != 200:
                print("❌ Strapi admin not accessible. Make sure Strapi is running.")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to Strapi: {e}")
            return False
        
        print("✅ Strapi is running and accessible!")
        return True
    
    def build_relationship_mappings(self):
        """Build mapping dictionaries for relationships"""
        print("🔗 Building relationship mappings...")
        
        # Map countries: remote country_id -> strapi country documentId
        try:
            response = requests.get(f"{self.strapi_base_url}/countries?pagination[pageSize]=100", timeout=10)
            if response.status_code == 200:
                countries = response.json()['data']
                for country in countries:
                    remote_id = country.get('country_id')
                    if remote_id:
                        self.country_mapping[remote_id] = country['documentId']
                print(f"   ✅ Mapped {len(self.country_mapping)} countries")
            else:
                print(f"   ⚠️  Could not fetch countries for mapping: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Country mapping failed: {e}")
        
        # Map vehicle statuses: status name -> strapi status documentId
        try:
            response = requests.get(f"{self.strapi_base_url}/vehicle-statuses?pagination[pageSize]=100", timeout=10)
            if response.status_code == 200:
                statuses = response.json()['data']
                for status in statuses:
                    status_name = status.get('name', '').lower()
                    if status_name:
                        self.vehicle_status_mapping[status_name] = status['documentId']
                print(f"   ✅ Mapped {len(self.vehicle_status_mapping)} vehicle statuses")
            else:
                print(f"   ⚠️  Could not fetch vehicle statuses: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Vehicle status mapping failed: {e}")
    
    def get_existing_vehicles(self) -> Set[str]:
        """Get list of existing vehicle reg_codes in Strapi"""
        print("📋 Checking existing vehicles in Strapi...")
        
        try:
            response = requests.get(f"{self.strapi_base_url}/vehicles?pagination[pageSize]=100", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                existing_codes = set()
                
                for vehicle in result['data']:
                    reg_code = vehicle.get('reg_code', '').upper()
                    if reg_code:
                        existing_codes.add(reg_code)
                
                print(f"   Found {len(existing_codes)} existing vehicles")
                if existing_codes:
                    print(f"   Existing codes: {sorted(list(existing_codes))[:5]}{'...' if len(existing_codes) > 5 else ''}")
                
                return existing_codes
            else:
                print(f"   ❌ Failed to get existing vehicles: {response.status_code}")
                return set()
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API request failed: {e}")
            return set()
    
    def fetch_remote_vehicles(self) -> List[Dict]:
        """Fetch vehicles from remote database"""
        print("🚗 Fetching vehicles from remote database...")
        
        if not self.remote_conn:
            print("❌ No remote database connection")
            return []
        
        try:
            with self.remote_conn.cursor() as cursor:
                # First, let's see what tables exist
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name LIKE '%vehicle%'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                print(f"   Vehicle-related tables: {[t['table_name'] for t in tables]}")
                
                # Check vehicle table structure
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'vehicles' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                print(f"   Vehicle columns: {[c['column_name'] for c in columns]}")
                
                # Now get vehicles with correct column names
                cursor.execute("SELECT * FROM vehicles ORDER BY vehicle_id LIMIT 10")
                vehicles = cursor.fetchall()
                
            print(f"✅ Found {len(vehicles)} vehicles in remote database")
            if vehicles:
                for vehicle in vehicles[:3]:
                    reg_num = vehicle.get('registration_number', 'Unknown')
                    status = vehicle.get('status_name', 'Unknown')
                    print(f"   - {reg_num} (Status: {status})")
                if len(vehicles) > 3:
                    print(f"   ... and {len(vehicles) - 3} more")
            
            return vehicles
        except Exception as e:
            print(f"❌ Failed to fetch vehicles: {e}")
            return []
    
    def map_vehicle_status(self, remote_status: str) -> Optional[str]:
        """Map remote vehicle status to Strapi vehicle status"""
        if not remote_status:
            return None
        
        # Try direct mapping first
        status_lower = remote_status.lower()
        if status_lower in self.vehicle_status_mapping:
            return self.vehicle_status_mapping[status_lower]
        
        # Try some common mappings
        status_mappings = {
            'active': 'available',
            'operational': 'available', 
            'inactive': 'out_of_service',
            'repair': 'maintenance',
            'servicing': 'maintenance'
        }
        
        for remote_key, strapi_key in status_mappings.items():
            if remote_key in status_lower:
                if strapi_key in self.vehicle_status_mapping:
                    return self.vehicle_status_mapping[strapi_key]
        
        # Default to available if we have it
        return self.vehicle_status_mapping.get('available')
    
    def create_vehicle_via_api(self, vehicle_data: Dict) -> bool:
        """Create a single vehicle via Strapi API"""
        reg_code = vehicle_data.get('registration_number', 'UNKNOWN')
        print(f"🚗 Creating: {reg_code}")
        
        # Map relationships
        country_ref = None
        if vehicle_data.get('country_id'):
            country_ref = self.country_mapping.get(str(vehicle_data['country_id']))
        
        status_ref = self.map_vehicle_status(vehicle_data.get('status_name'))
        
        # Map remote fields to Strapi fields
        strapi_data = {
            "data": {
                "reg_code": reg_code,
                "capacity": vehicle_data.get('capacity', 11),
                "profile_id": vehicle_data.get('profile_id'),
                "notes": vehicle_data.get('notes'),
                "max_speed_kmh": float(vehicle_data.get('max_speed_kmh', 25.0)),
                "acceleration_mps2": float(vehicle_data.get('acceleration_mps2', 1.2)),
                "braking_mps2": float(vehicle_data.get('braking_mps2', 1.8)),
                "eco_mode": vehicle_data.get('eco_mode', False),
                "performance_profile": vehicle_data.get('performance_profile', 'standard'),
                # Relationships
                "country": country_ref,
                "vehicle_status": status_ref,
                # Other relationships would be None for now
                "home_depot": None,
                "preferred_route": None,
                "assigned_driver": None,
                "gps_device": None
            }
        }
        
        # Remove None values to avoid validation issues
        strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
        
        try:
            response = requests.post(
                f"{self.strapi_base_url}/vehicles",
                json=strapi_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                print(f"   ✅ Created with ID: {result['data']['id']}")
                return True
            else:
                print(f"   ❌ Failed: {response.status_code}")
                if response.status_code == 400:
                    error_data = response.json()
                    if 'unique' in str(error_data):
                        print(f"   📝 Already exists (unique constraint)")
                        return False
                print(f"      Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API request failed: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify vehicles were migrated correctly"""
        print("\n" + "=" * 50)
        print("🔍 Verifying vehicle migration results...")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.strapi_base_url}/vehicles?pagination[pageSize]=100", timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Failed to verify: {response.status_code}")
                return False
            
            result = response.json()
            strapi_vehicles = result['data']
            
            print(f"📊 Total vehicles in Strapi: {len(strapi_vehicles)}")
            
            # Display sample results
            print(f"\n📋 Sample migrated vehicles:")
            for i, vehicle in enumerate(strapi_vehicles[:10]):
                reg_code = vehicle.get('reg_code', 'Unknown')
                capacity = vehicle.get('capacity', 'Unknown')
                print(f"   {i+1:2d}. {reg_code} (Capacity: {capacity})")
            
            if len(strapi_vehicles) > 10:
                print(f"   ... and {len(strapi_vehicles) - 10} more")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def run_migration(self):
        """Run the complete vehicle migration"""
        print("=" * 60)
        print("🚗 Starting Vehicle Migration from Remote to Strapi")
        print("=" * 60)
        
        # Step 1: Connect to remote database
        if not self.connect_remote_database():
            return False
        
        # Step 2: Check Strapi connection
        if not self.check_strapi_connection():
            return False
        
        # Step 3: Build relationship mappings
        self.build_relationship_mappings()
        
        # Step 4: Get existing vehicles to skip
        existing_codes = self.get_existing_vehicles()
        
        # Step 5: Fetch remote vehicles
        remote_vehicles = self.fetch_remote_vehicles()
        if not remote_vehicles:
            print("❌ No vehicles to migrate")
            return False
        
        # Step 6: Filter out existing vehicles
        vehicles_to_create = []
        skipped_count = 0
        
        for vehicle in remote_vehicles:
            remote_reg = vehicle.get('registration_number', '').upper()
            if remote_reg in existing_codes:
                print(f"⏭️  Skipping {remote_reg} - already exists")
                skipped_count += 1
            else:
                vehicles_to_create.append(vehicle)
        
        print(f"\n📊 Migration Summary:")
        print(f"   Total remote vehicles: {len(remote_vehicles)}")
        print(f"   Already in Strapi: {skipped_count}")
        print(f"   To be created: {len(vehicles_to_create)}")
        
        if not vehicles_to_create:
            print("✅ All vehicles already exist in Strapi!")
            return self.verify_migration()
        
        # Step 7: Create new vehicles
        print(f"\n" + "=" * 40)
        print(f"🚗 Creating {len(vehicles_to_create)} new vehicles...")
        print("=" * 40)
        
        created_count = 0
        failed_count = 0
        
        for vehicle in vehicles_to_create:
            if self.create_vehicle_via_api(vehicle):
                created_count += 1
            else:
                failed_count += 1
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
        
        # Step 8: Results summary
        print(f"\n" + "=" * 50)
        print("📊 Migration Results:")
        print(f"   Successfully created: {created_count}")
        print(f"   Failed: {failed_count}")
        print(f"   Skipped (existing): {skipped_count}")
        print("=" * 50)
        
        # Step 9: Verify results
        return self.verify_migration()
    
    def cleanup(self):
        """Clean up connections"""
        if self.remote_conn:
            self.remote_conn.close()
            print("📡 Remote database connection closed")
        
        if self.tunnel:
            self.tunnel.stop()
            print("🔗 SSH tunnel closed")

def main():
    """Main execution function"""
    print("⚠️  IMPORTANT: Make sure you've enabled public API permissions for:")
    print("   - Vehicles (find, findOne, create, update, delete)")
    print("   - Vehicle-statuses (find, findOne)")
    print("   - Countries (find, findOne)")
    print("\n   Go to: Settings → Users & Permissions → Public")
    print("\nPress Enter to continue...")
    input()
    
    migrator = VehicleMigrator()
    
    try:
        success = migrator.run_migration()
        if success:
            print("\n🎉 Vehicle migration completed successfully!")
        else:
            print("\n❌ Migration completed with issues")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
    finally:
        migrator.cleanup()

if __name__ == "__main__":
    main()