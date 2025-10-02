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

def get_remote_drivers():
    """Fetch all drivers from remote database"""
    try:
        conn = psycopg2.connect(**REMOTE_DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM drivers ORDER BY driver_id")
        drivers = cursor.fetchall()
        
        conn.close()
        return drivers
        
    except Exception as e:
        print(f"Error fetching remote drivers: {e}")
        return None

def get_existing_strapi_drivers():
    """Get existing drivers from Strapi to avoid duplicates"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/drivers?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            existing = {}
            for driver in data['data']:
                # Use driver_uuid as unique identifier
                if 'driver_uuid' in driver['attributes']:
                    existing[driver['attributes']['driver_uuid']] = driver
            return existing
        else:
            print(f"Error fetching existing drivers: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error connecting to Strapi: {e}")
        return {}

def create_strapi_driver(remote_driver):
    """Create a driver in Strapi via API"""
    
    # Map remote fields to Strapi fields
    strapi_data = {
        "data": {
            "driver_uuid": str(remote_driver['driver_id']),  # Map UUID to string
            "employee_id": remote_driver.get('employee_id'),
            "first_name": remote_driver.get('first_name'),
            "last_name": remote_driver.get('last_name'),
            "phone_number": remote_driver.get('phone_number'),
            "email": remote_driver.get('email'),
            "license_number": remote_driver.get('license_number'),
            "license_class": remote_driver.get('license_class'),
            "license_expiry": remote_driver.get('license_expiry'),
            "hire_date": remote_driver.get('hire_date'),
            "emergency_contact_name": remote_driver.get('emergency_contact_name'),
            "emergency_contact_phone": remote_driver.get('emergency_contact_phone'),
            "address": remote_driver.get('address'),
            "status": remote_driver.get('status', 'unknown'),
            "notes": remote_driver.get('notes')
        }
    }
    
    # Remove None values
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    try:
        response = requests.post(
            f"{STRAPI_API_URL}/drivers",
            headers=STRAPI_HEADERS,
            json=strapi_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error creating driver: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling Strapi API: {e}")
        return None

def migrate_drivers():
    """Main migration function for drivers"""
    
    print("=== DRIVERS MIGRATION ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Fetch remote drivers
    print("Fetching drivers from remote database...")
    remote_drivers = get_remote_drivers()
    
    if not remote_drivers:
        print("No drivers found or error occurred")
        return
    
    print(f"Found {len(remote_drivers)} drivers in remote database")
    
    # Get existing Strapi drivers
    print("Checking existing drivers in Strapi...")
    existing_drivers = get_existing_strapi_drivers()
    print(f"Found {len(existing_drivers)} existing drivers in Strapi")
    
    # Migration counters
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    print("\nStarting migration...\n")
    
    for i, driver in enumerate(remote_drivers, 1):
        driver_uuid = str(driver['driver_id'])
        driver_name = f"{driver.get('first_name', '')} {driver.get('last_name', '')}".strip()
        if not driver_name:
            driver_name = driver.get('employee_id', 'Unknown')
        
        print(f"[{i}/{len(remote_drivers)}] Processing {driver_name} ({driver_uuid})")
        
        # Check if driver already exists
        if driver_uuid in existing_drivers:
            print(f"  → Skipped (already exists)")
            skipped_count += 1
            continue
        
        # Create the driver
        result = create_strapi_driver(driver)
        
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
    print(f"Total drivers processed: {len(remote_drivers)}")
    print(f"Created: {created_count}")
    print(f"Skipped (already exist): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Completed at: {datetime.now()}")
    
    if error_count == 0:
        print("✅ All drivers migrated successfully!")
    else:
        print(f"⚠️  {error_count} drivers failed to migrate")

def verify_migration():
    """Verify the migration by comparing counts"""
    print("\n=== VERIFICATION ===")
    
    # Count remote drivers
    remote_drivers = get_remote_drivers()
    remote_count = len(remote_drivers) if remote_drivers else 0
    
    # Count Strapi drivers
    strapi_drivers = get_existing_strapi_drivers()
    strapi_count = len(strapi_drivers)
    
    print(f"Remote drivers: {remote_count}")
    print(f"Strapi drivers: {strapi_count}")
    
    if remote_count == strapi_count:
        print("✅ Counts match - migration verified!")
    else:
        print(f"⚠️  Count mismatch - {remote_count - strapi_count} drivers missing")

if __name__ == "__main__":
    migrate_drivers()
    verify_migration()