#!/usr/bin/env python3
"""
Migrate GPS Devices from remote database to Strapi API
Migration order: 1/5 (no dependencies)
Uses the same SSH tunnel approach that worked for countries migration
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json
from datetime import datetime
import time
import sys
import os

# Add the current directory to Python path to import from migrate_data
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel

# Database connection parameters (via SSH tunnel)
REMOTE_DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 6543,  # SSH tunnel port  
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}

# Strapi API configuration
STRAPI_API_URL = "http://localhost:1337/api"
STRAPI_HEADERS = {
    'Content-Type': 'application/json'
}

def get_remote_gps_devices():
    """Fetch all GPS devices from remote database"""
    try:
        conn = psycopg2.connect(**REMOTE_DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM gps_devices ORDER BY device_id")
        devices = cursor.fetchall()
        
        conn.close()
        return devices
        
    except Exception as e:
        print(f"Error fetching remote GPS devices: {e}")
        return None

def get_existing_strapi_gps_devices():
    """Get existing GPS devices from Strapi to avoid duplicates"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/gps-devices?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            existing = {}
            for device in data['data']:
                # Use device_id as unique identifier
                if 'device_id' in device['attributes']:
                    existing[device['attributes']['device_id']] = device
            return existing
        else:
            print(f"Error fetching existing GPS devices: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error connecting to Strapi: {e}")
        return {}

def create_strapi_gps_device(remote_device):
    """Create a GPS device in Strapi via API"""
    
    # Map remote fields to Strapi fields based on actual remote structure
    strapi_data = {
        "data": {
            "device_id": str(remote_device['device_id']),  # UUID as string
            "device_name": remote_device.get('device_name'),
            "serial_number": remote_device.get('serial_number'),
            "manufacturer": remote_device.get('manufacturer'),
            "model": remote_device.get('model'),
            "firmware_version": remote_device.get('firmware_version'),
            "is_active": remote_device.get('is_active', True),
            "notes": remote_device.get('notes')
        }
    }
    
    # Remove None values
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    try:
        response = requests.post(
            f"{STRAPI_API_URL}/gps-devices",
            headers=STRAPI_HEADERS,
            json=strapi_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error creating GPS device: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling Strapi API: {e}")
        return None

def migrate_gps_devices():
    """Main migration function for GPS devices"""
    
    print("=== GPS DEVICES MIGRATION ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Setup SSH tunnel (same as successful countries migration)
    print("Setting up SSH tunnel...")
    tunnel = SSHTunnel(
        ssh_host='arknetglobal.com',
        ssh_port=22,
        ssh_user='david',
        ssh_pass='Cabbyminnie5!',
        remote_host='localhost',
        remote_port=5432,
        local_port=6543
    )
    
    try:
        tunnel.start()
        print("✅ SSH tunnel established")
        
        # Fetch remote GPS devices
        print("Fetching GPS devices from remote database...")
        remote_devices = get_remote_gps_devices()
        
        if not remote_devices:
            print("No GPS devices found or error occurred")
            return
        
        print(f"Found {len(remote_devices)} GPS devices in remote database")
        
        # Get existing Strapi GPS devices
        print("Checking existing GPS devices in Strapi...")
        existing_devices = get_existing_strapi_gps_devices()
        print(f"Found {len(existing_devices)} existing GPS devices in Strapi")
        
        # Migration counters
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        print("\nStarting migration...\n")
        
        for i, device in enumerate(remote_devices, 1):
            device_uuid = str(device['device_id'])
            device_name = device.get('device_name', 'Unknown')
            
            print(f"[{i}/{len(remote_devices)}] Processing {device_name} ({device_uuid})")
            
            # Check if device already exists
            if device_uuid in existing_devices:
                print(f"  → Skipped (already exists)")
                skipped_count += 1
                continue
            
            # Create the GPS device
            result = create_strapi_gps_device(device)
            
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
        print(f"Total devices processed: {len(remote_devices)}")
        print(f"Created: {created_count}")
        print(f"Skipped (already exist): {skipped_count}")
        print(f"Errors: {error_count}")
        print(f"Completed at: {datetime.now()}")
        
        if error_count == 0:
            print("✅ All GPS devices migrated successfully!")
        else:
            print(f"⚠️  {error_count} devices failed to migrate")
    
    finally:
        # Clean up SSH tunnel
        print("Closing SSH tunnel...")
        tunnel.stop()
        print("✅ SSH tunnel closed")

def verify_migration():
    """Verify the migration by comparing counts"""
    print("\n=== VERIFICATION ===")
    
    # Setup SSH tunnel for verification
    tunnel = SSHTunnel(
        ssh_host='arknetglobal.com',
        ssh_port=22,
        ssh_user='david',
        ssh_pass='Cabbyminnie5!',
        remote_host='localhost',
        remote_port=5432,
        local_port=6543
    )
    
    try:
        tunnel.start()
        
        # Count remote devices
        remote_devices = get_remote_gps_devices()
        remote_count = len(remote_devices) if remote_devices else 0
        
        # Count Strapi devices
        strapi_devices = get_existing_strapi_gps_devices()
        strapi_count = len(strapi_devices)
        
        print(f"Remote GPS devices: {remote_count}")
        print(f"Strapi GPS devices: {strapi_count}")
        
        if remote_count == strapi_count:
            print("✅ Counts match - migration verified!")
        else:
            print(f"⚠️  Count mismatch - {remote_count - strapi_count} devices missing")
    
    finally:
        tunnel.stop()

if __name__ == "__main__":
    migrate_gps_devices()
    verify_migration()