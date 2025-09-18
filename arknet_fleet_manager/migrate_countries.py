"""
Country Migration Test Script
============================
Migrate all countries from remote database to local Strapi, skipping duplicates.
This tests the complete migration workflow using Strapi API.
"""
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import paramiko
import threading
import socket
import time
import json
from typing import Dict, List, Any, Set
import sys
import os

# Add the current directory to Python path to import from migrate_data
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel

class CountryMigrator:
    """Migrate all countries from remote to local Strapi"""
    
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
            print("   Make sure Strapi is running on http://localhost:1337")
            return False
        
        print("✅ Strapi is running and accessible!")
        return True
    
    def get_existing_countries(self) -> Set[str]:
        """Get list of existing country codes in Strapi"""
        print("📋 Checking existing countries in Strapi...")
        
        try:
            response = requests.get(f"{self.strapi_base_url}/countries?pagination[pageSize]=100", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                existing_codes = set()
                
                for country in result['data']:
                    code = country.get('code', '').upper()
                    if code:
                        existing_codes.add(code)
                
                print(f"   Found {len(existing_codes)} existing countries")
                if existing_codes:
                    print(f"   Existing codes: {sorted(list(existing_codes))}")
                
                return existing_codes
            else:
                print(f"   ❌ Failed to get existing countries: {response.status_code}")
                return set()
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API request failed: {e}")
            return set()
    
    def fetch_remote_countries(self) -> List[Dict]:
        """Fetch all countries from remote database"""
        print("📊 Fetching countries from remote database...")
        
        if not self.remote_conn:
            print("❌ No remote database connection")
            return []
        
        try:
            with self.remote_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM countries ORDER BY name")
                countries = cursor.fetchall()
                
            print(f"✅ Found {len(countries)} countries in remote database")
            return countries
        except Exception as e:
            print(f"❌ Failed to fetch countries: {e}")
            return []
    
    def create_country_via_api(self, country_data: Dict) -> bool:
        """Create a single country via Strapi API"""
        country_name = country_data['name']
        country_code = country_data['iso_code'].upper()
        
        print(f"📝 Creating: {country_name} ({country_code})")
        
        # Map remote database fields to Strapi fields
        strapi_data = {
            "data": {
                "country_id": str(country_data['country_id']),
                "name": country_name,
                "code": country_code,
                "currency": None,  # Not in remote data
                "timezone": None,  # Not in remote data
                "is_active": True
            }
        }
        
        try:
            response = requests.post(
                f"{self.strapi_base_url}/countries",
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
        """Verify all countries were migrated correctly"""
        print("\n" + "=" * 50)
        print("🔍 Verifying migration results...")
        print("=" * 50)
        
        # Get all countries from Strapi
        try:
            response = requests.get(f"{self.strapi_base_url}/countries?pagination[pageSize]=100", timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Failed to verify: {response.status_code}")
                return False
            
            result = response.json()
            strapi_countries = result['data']
            
            print(f"📊 Total countries in Strapi: {len(strapi_countries)}")
            
            # Group by code for easier verification
            strapi_by_code = {}
            for country in strapi_countries:
                code = country.get('code', '').upper()
                if code:
                    strapi_by_code[code] = country
            
            # Get remote countries for comparison
            remote_countries = self.fetch_remote_countries()
            remote_by_code = {}
            for country in remote_countries:
                code = country['iso_code'].upper()
                remote_by_code[code] = country
            
            print(f"📊 Remote countries: {len(remote_countries)}")
            print(f"📊 Strapi countries: {len(strapi_countries)}")
            
            # Check coverage
            missing_in_strapi = []
            for code in remote_by_code:
                if code not in strapi_by_code:
                    missing_in_strapi.append(code)
            
            if missing_in_strapi:
                print(f"⚠️  Missing countries: {missing_in_strapi}")
            else:
                print("✅ All remote countries are present in Strapi!")
            
            # Display sample results
            print(f"\n📋 Sample migrated countries:")
            for i, country in enumerate(strapi_countries[:10]):
                name = country.get('name', 'Unknown')
                code = country.get('code', 'Unknown')
                print(f"   {i+1:2d}. {name} ({code})")
            
            if len(strapi_countries) > 10:
                print(f"   ... and {len(strapi_countries) - 10} more")
            
            return len(missing_in_strapi) == 0
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def run_migration(self):
        """Run the complete country migration"""
        print("=" * 60)
        print("🌍 Starting Country Migration from Remote to Strapi")
        print("=" * 60)
        
        # Step 1: Connect to remote database
        if not self.connect_remote_database():
            return False
        
        # Step 2: Check Strapi connection
        if not self.check_strapi_connection():
            return False
        
        # Step 3: Get existing countries to skip
        existing_codes = self.get_existing_countries()
        
        # Step 4: Fetch remote countries
        remote_countries = self.fetch_remote_countries()
        if not remote_countries:
            print("❌ No countries to migrate")
            return False
        
        # Step 5: Filter out existing countries
        countries_to_create = []
        skipped_count = 0
        
        for country in remote_countries:
            remote_code = country['iso_code'].upper()
            if remote_code in existing_codes:
                print(f"⏭️  Skipping {country['name']} ({remote_code}) - already exists")
                skipped_count += 1
            else:
                countries_to_create.append(country)
        
        print(f"\n📊 Migration Summary:")
        print(f"   Total remote countries: {len(remote_countries)}")
        print(f"   Already in Strapi: {skipped_count}")
        print(f"   To be created: {len(countries_to_create)}")
        
        if not countries_to_create:
            print("✅ All countries already exist in Strapi!")
            return self.verify_migration()
        
        # Step 6: Create new countries
        print(f"\n" + "=" * 40)
        print(f"📝 Creating {len(countries_to_create)} new countries...")
        print("=" * 40)
        
        created_count = 0
        failed_count = 0
        
        for country in countries_to_create:
            if self.create_country_via_api(country):
                created_count += 1
            else:
                failed_count += 1
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
        
        # Step 7: Results summary
        print(f"\n" + "=" * 50)
        print("📊 Migration Results:")
        print(f"   Successfully created: {created_count}")
        print(f"   Failed: {failed_count}")
        print(f"   Skipped (existing): {skipped_count}")
        print("=" * 50)
        
        # Step 8: Verify results
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
    migrator = CountryMigrator()
    
    try:
        success = migrator.run_migration()
        if success:
            print("\n🎉 Country migration completed successfully!")
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