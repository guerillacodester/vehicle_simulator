#!/usr/bin/env python3
"""
Drivers Migration Script - From Remote PostgreSQL to Strapi
===========================================================
Migrates driver records using comprehensive field mappings from analysis.

Field Mappings (from comprehensive analysis):
- driver_id (UUID) → driver_id (String) [REQUIRED]
- name (String) → name (String) [REQUIRED] 
- license_no (String) → license_no (String) [REQUIRED]
- employment_status (String) → employment_status (String) [OPTIONAL]

Remote Table: drivers (4 records)
Strapi Endpoint: /api/drivers
Dependencies: None (can run first)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json
import uuid

def create_strapi_driver(remote_driver):
    """Create driver in Strapi - FIELD MAPPINGS FROM COMPREHENSIVE ANALYSIS"""
    
    strapi_data = {
        "data": {
            "driver_id": str(remote_driver.get("driver_id")) if remote_driver.get("driver_id") else None,
            "name": str(remote_driver.get("name")) if remote_driver.get("name") else None,
            "license_no": str(remote_driver.get("license_no")) if remote_driver.get("license_no") else None,
            "employment_status": str(remote_driver.get("employment_status")) if remote_driver.get("employment_status") else None,
        }
    }
    
    # Remove None values for optional fields
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    response = requests.post('http://localhost:1337/api/drivers',
                           headers={'Content-Type': 'application/json'},
                           json=strapi_data)
    
    if response.status_code in [200, 201]:
        created = response.json()
        return created['data']['id']
    else:
        print(f"Error creating driver: {response.status_code} - {response.text}")
        return None

def check_driver_exists(driver_id):
    """Check if driver already exists in Strapi by driver_id"""
    try:
        response = requests.get('http://localhost:1337/api/drivers')
        if response.status_code == 200:
            drivers = response.json()['data']
            for driver in drivers:
                if driver.get('driver_id') == str(driver_id):
                    return driver['id']
        return None
    except Exception as e:
        print(f"Error checking existing drivers: {e}")
        return None

def migrate_drivers():
    """Main migration function for drivers"""
    print("🚛 DRIVERS MIGRATION - Remote PostgreSQL → Strapi")
    print("=" * 60)
    
    # Initialize SSH tunnel
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        # Connect to remote database
        conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all drivers from remote database
        print("📊 Fetching drivers from remote database...")
        cursor.execute("""
            SELECT 
                driver_id,
                country_id,
                name,
                license_no,
                home_depot_id,
                employment_status,
                created_at,
                updated_at
            FROM drivers 
            ORDER BY name
        """)
        
        remote_drivers = cursor.fetchall()
        print(f"Found {len(remote_drivers)} drivers in remote database")
        
        if not remote_drivers:
            print("❌ No drivers found in remote database")
            return
        
        # Display what we're about to migrate
        print("\n📋 Drivers to migrate:")
        for driver in remote_drivers:
            print(f"  - {driver['name']} (ID: {driver['driver_id']}, License: {driver['license_no']}, Status: {driver['employment_status']})")
        
        # Migration statistics
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n🔄 Starting migration...")
        
        for driver in remote_drivers:
            driver_name = driver['name']
            driver_id = driver['driver_id']
            
            print(f"\n--- Processing: {driver_name} ---")
            
            # Check if driver already exists
            existing_id = check_driver_exists(driver_id)
            if existing_id:
                print(f"⏭️  Driver already exists (Strapi ID: {existing_id})")
                skipped_count += 1
                continue
            
            # Create driver in Strapi
            print("📝 Creating driver in Strapi...")
            strapi_id = create_strapi_driver(driver)
            
            if strapi_id:
                print(f"✅ Successfully created driver (Strapi ID: {strapi_id})")
                created_count += 1
            else:
                print(f"❌ Failed to create driver")
                error_count += 1
        
        # Final summary
        print(f"\n{'='*60}")
        print("📊 DRIVERS MIGRATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total drivers processed: {len(remote_drivers)}")
        print(f"Created: {created_count}")
        print(f"Skipped (already exist): {skipped_count}")
        print(f"Errors: {error_count}")
        
        if error_count == 0:
            if created_count > 0:
                print("🎉 All drivers migrated successfully!")
            else:
                print("✅ All drivers were already migrated")
        else:
            print(f"⚠️  Migration completed with {error_count} errors")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        tunnel.stop()

def test_strapi_connection():
    """Test connection to Strapi API"""
    print("🔍 Testing Strapi connection...")
    try:
        response = requests.get('http://localhost:1337/api/drivers')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strapi connected - {len(data['data'])} existing drivers")
            return True
        else:
            print(f"❌ Strapi connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Strapi connection error: {e}")
        return False

if __name__ == "__main__":
    print("🚛 ARKNET DRIVERS MIGRATION")
    print("Migration: Remote PostgreSQL → Strapi API")
    print(f"Timestamp: {__import__('datetime').datetime.now()}")
    print()
    
    # Test connections first
    if not test_strapi_connection():
        print("❌ Cannot proceed - Strapi connection failed")
        sys.exit(1)
    
    # Run migration
    migrate_drivers()