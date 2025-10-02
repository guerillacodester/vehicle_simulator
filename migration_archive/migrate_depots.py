#!/usr/bin/env python3
"""
Migrate Depots from remote database to Strapi API
Migration order: 3/5 (depends on countries - already migrated)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json
from datetime import datetime
import time

# Database connection parameters  
REMOTE_DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,  # SSH tunnel port
    'database': 'arknetglobal',
    'user': 'arknetglobal',
    'password': 'password123'
}

# Strapi API configuration
STRAPI_API_URL = "http://localhost:1337/api"
STRAPI_HEADERS = {
    'Content-Type': 'application/json'
}

def get_remote_depots():
    """Fetch all depots from remote database"""
    try:
        conn = psycopg2.connect(**REMOTE_DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM depots ORDER BY depot_id")
        depots = cursor.fetchall()
        
        conn.close()
        return depots
        
    except Exception as e:
        print(f"Error fetching remote depots: {e}")
        return None

def get_existing_strapi_depots():
    """Get existing depots from Strapi to avoid duplicates"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/depots?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            existing = {}
            for depot in data['data']:
                # Use depot_uuid as unique identifier
                if 'depot_uuid' in depot['attributes']:
                    existing[depot['attributes']['depot_uuid']] = depot
            return existing
        else:
            print(f"Error fetching existing depots: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error connecting to Strapi: {e}")
        return {}

def get_strapi_countries():
    """Get countries from Strapi for relationship mapping"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/countries?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            countries = {}
            for country in data['data']:
                # Map by country_code for lookup
                if 'country_code' in country['attributes']:
                    countries[country['attributes']['country_code']] = country['id']
            return countries
        else:
            print(f"Error fetching Strapi countries: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching countries from Strapi: {e}")
        return {}

def find_country_id_by_uuid(country_uuid, strapi_countries):
    """Find Strapi country ID by remote country UUID"""
    # This would need country mapping - for now return None if not found
    # You might need to add country_uuid mapping to your countries migration
    return None

def create_strapi_depot(remote_depot, strapi_countries):
    """Create a depot in Strapi via API"""
    
    # Map remote fields to Strapi fields
    strapi_data = {
        "data": {
            "depot_uuid": str(remote_depot['depot_id']),  # Map UUID to string
            "depot_name": remote_depot.get('depot_name'),
            "depot_code": remote_depot.get('depot_code'),
            "address": remote_depot.get('address'),
            "city": remote_depot.get('city'),
            "postal_code": remote_depot.get('postal_code'),
            "latitude": float(remote_depot['latitude']) if remote_depot.get('latitude') else None,
            "longitude": float(remote_depot['longitude']) if remote_depot.get('longitude') else None,
            "capacity": remote_depot.get('capacity'),
            "manager_name": remote_depot.get('manager_name'),
            "manager_phone": remote_depot.get('manager_phone'),
            "operational_hours": remote_depot.get('operational_hours'),
            "status": remote_depot.get('status', 'unknown'),
            "notes": remote_depot.get('notes')
        }
    }
    
    # Handle country relationship
    if remote_depot.get('country_id'):
        # For now, we'll need to map country UUIDs to Strapi country IDs
        # This is a placeholder - you might need to enhance this based on your country data
        country_strapi_id = find_country_id_by_uuid(remote_depot['country_id'], strapi_countries)
        if country_strapi_id:
            strapi_data["data"]["country"] = country_strapi_id
    
    # Remove None values
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    try:
        response = requests.post(
            f"{STRAPI_API_URL}/depots",
            headers=STRAPI_HEADERS,
            json=strapi_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error creating depot: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling Strapi API: {e}")
        return None

def migrate_depots():
    """Main migration function for depots"""
    
    print("=== DEPOTS MIGRATION ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Get Strapi countries for relationship mapping
    print("Loading countries from Strapi for relationship mapping...")
    strapi_countries = get_strapi_countries()
    print(f"Found {len(strapi_countries)} countries in Strapi")
    
    # Fetch remote depots
    print("Fetching depots from remote database...")
    remote_depots = get_remote_depots()
    
    if not remote_depots:
        print("No depots found or error occurred")
        return
    
    print(f"Found {len(remote_depots)} depots in remote database")
    
    # Get existing Strapi depots
    print("Checking existing depots in Strapi...")
    existing_depots = get_existing_strapi_depots()
    print(f"Found {len(existing_depots)} existing depots in Strapi")
    
    # Migration counters
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    print("\nStarting migration...\n")
    
    for i, depot in enumerate(remote_depots, 1):
        depot_uuid = str(depot['depot_id'])
        depot_name = depot.get('depot_name', depot.get('depot_code', 'Unknown'))
        
        print(f"[{i}/{len(remote_depots)}] Processing {depot_name} ({depot_uuid})")
        
        # Check if depot already exists
        if depot_uuid in existing_depots:
            print(f"  → Skipped (already exists)")
            skipped_count += 1
            continue
        
        # Create the depot
        result = create_strapi_depot(depot, strapi_countries)
        
        if result:
            print(f"  → Created successfully (ID: {result['data']['id']})")
            created_count += 1
        else:
            print(f"  → Failed to create")
            error_count += 1
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
    
    # Final summary
    print(f"\n=== MIGRATION COMPLETE ===")
    print(f"Total depots processed: {len(remote_depots)}")
    print(f"Created: {created_count}")
    print(f"Skipped (already exist): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Completed at: {datetime.now()}")
    
    if error_count == 0:
        print("✅ All depots migrated successfully!")
    else:
        print(f"⚠️  {error_count} depots failed to migrate")

def verify_migration():
    """Verify the migration by comparing counts"""
    print("\n=== VERIFICATION ===")
    
    # Count remote depots
    remote_depots = get_remote_depots()
    remote_count = len(remote_depots) if remote_depots else 0
    
    # Count Strapi depots
    strapi_depots = get_existing_strapi_depots()
    strapi_count = len(strapi_depots)
    
    print(f"Remote depots: {remote_count}")
    print(f"Strapi depots: {strapi_count}")
    
    if remote_count == strapi_count:
        print("✅ Counts match - migration verified!")
    else:
        print(f"⚠️  Count mismatch - {remote_count - strapi_count} depots missing")

if __name__ == "__main__":
    migrate_depots()
    verify_migration()