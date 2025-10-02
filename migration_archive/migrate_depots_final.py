#!/usr/bin/env python3
"""
Depots Migration Script - From Remote PostgreSQL to Strapi
===========================================================
Migrates depot records using comprehensive field mappings from analysis.

Field Mappings (from comprehensive analysis):
- depot_id (UUID) → depot_id (String) [REQUIRED]
- name (String) → name (String) [REQUIRED]
- capacity (Integer) → capacity (Integer) [OPTIONAL]
- notes (String) → notes (String) [OPTIONAL]

Remote Table: depots (1 record)
Strapi Endpoint: /api/depots
Dependencies: countries (already migrated)
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

def create_strapi_depot(remote_depot):
    """Create depot in Strapi - FIELD MAPPINGS FROM COMPREHENSIVE ANALYSIS"""
    
    strapi_data = {
        "data": {
            "depot_id": str(remote_depot.get("depot_id")) if remote_depot.get("depot_id") else None,
            "name": str(remote_depot.get("name")) if remote_depot.get("name") else None,
            "capacity": remote_depot.get("capacity"),
            "notes": remote_depot.get("notes"),
        }
    }
    
    # Remove None values for optional fields
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    response = requests.post('http://localhost:1337/api/depots',
                           headers={'Content-Type': 'application/json'},
                           json=strapi_data)
    
    if response.status_code in [200, 201]:
        created = response.json()
        return created['data']['id']
    else:
        print(f"Error creating depot: {response.status_code} - {response.text}")
        return None

def check_depot_exists(depot_id):
    """Check if depot already exists in Strapi by depot_id"""
    try:
        response = requests.get('http://localhost:1337/api/depots')
        if response.status_code == 200:
            depots = response.json()['data']
            for depot in depots:
                if depot.get('depot_id') == str(depot_id):
                    return depot['id']
        return None
    except Exception as e:
        print(f"Error checking existing depots: {e}")
        return None

def migrate_depots():
    """Main migration function for depots"""
    print("🏢 DEPOTS MIGRATION - Remote PostgreSQL → Strapi")
    print("=" * 60)
    
    # Initialize SSH tunnel
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        # Connect to remote database
        conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all depots from remote database
        print("📊 Fetching depots from remote database...")
        cursor.execute("""
            SELECT 
                depot_id,
                country_id,
                name,
                location,
                capacity,
                notes,
                created_at,
                updated_at
            FROM depots 
            ORDER BY name
        """)
        
        remote_depots = cursor.fetchall()
        print(f"Found {len(remote_depots)} depots in remote database")
        
        if not remote_depots:
            print("❌ No depots found in remote database")
            return
        
        # Display what we're about to migrate
        print("\n📋 Depots to migrate:")
        for depot in remote_depots:
            print(f"  - {depot['name']} (ID: {depot['depot_id']}, Capacity: {depot['capacity']})")
        
        # Migration statistics
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n🔄 Starting migration...")
        
        for depot in remote_depots:
            depot_name = depot['name']
            depot_id = depot['depot_id']
            
            print(f"\n--- Processing: {depot_name} ---")
            
            # Check if depot already exists
            existing_id = check_depot_exists(depot_id)
            if existing_id:
                print(f"⏭️  Depot already exists (Strapi ID: {existing_id})")
                skipped_count += 1
                continue
            
            # Create depot in Strapi
            print("📝 Creating depot in Strapi...")
            strapi_id = create_strapi_depot(depot)
            
            if strapi_id:
                print(f"✅ Successfully created depot (Strapi ID: {strapi_id})")
                created_count += 1
            else:
                print(f"❌ Failed to create depot")
                error_count += 1
        
        # Final summary
        print(f"\n{'='*60}")
        print("📊 DEPOTS MIGRATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total depots processed: {len(remote_depots)}")
        print(f"Created: {created_count}")
        print(f"Skipped (already exist): {skipped_count}")
        print(f"Errors: {error_count}")
        
        if error_count == 0:
            if created_count > 0:
                print("🎉 All depots migrated successfully!")
            else:
                print("✅ All depots were already migrated")
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
        response = requests.get('http://localhost:1337/api/depots')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strapi connected - {len(data['data'])} existing depots")
            return True
        else:
            print(f"❌ Strapi connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Strapi connection error: {e}")
        return False

if __name__ == "__main__":
    print("🏢 ARKNET DEPOTS MIGRATION")
    print("Migration: Remote PostgreSQL → Strapi API")
    print(f"Timestamp: {__import__('datetime').datetime.now()}")
    print()
    
    # Test connections first
    if not test_strapi_connection():
        print("❌ Cannot proceed - Strapi connection failed")
        sys.exit(1)
    
    # Run migration
    migrate_depots()