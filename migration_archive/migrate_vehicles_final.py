#!/usr/bin/env python3
"""
Vehicles Migration Script - From Remote PostgreSQL to Strapi
===========================================================
Migrates vehicle records using comprehensive field mappings from analysis.

Field Mappings (from comprehensive analysis):
- vehicle_id (UUID) → vehicle_id (String) [REQUIRED]
- reg_code (String) → reg_code (String) [REQUIRED]
- capacity (Integer) → capacity (Integer) [OPTIONAL]
- notes (String) → notes (String) [OPTIONAL]
- profile_id (String) → profile_id (String) [OPTIONAL]
- max_speed_kmh (Double) → max_speed_kmh (Number) [OPTIONAL]
- acceleration_mps2 (Double) → acceleration_mps2 (Number) [OPTIONAL]
- braking_mps2 (Double) → braking_mps2 (Number) [OPTIONAL]
- eco_mode (Boolean) → eco_mode (Boolean) [OPTIONAL]
- performance_profile (String) → performance_profile (String) [OPTIONAL]

Remote Table: vehicles (4 records)
Strapi Endpoint: /api/vehicles
Dependencies: depots, routes, drivers, gps_devices (may reference these)
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

def create_strapi_vehicle(remote_vehicle):
    """Create vehicle in Strapi - FIELD MAPPINGS FROM COMPREHENSIVE ANALYSIS"""
    
    strapi_data = {
        "data": {
            "vehicle_id": str(remote_vehicle.get("vehicle_id")) if remote_vehicle.get("vehicle_id") else None,
            "reg_code": str(remote_vehicle.get("reg_code")) if remote_vehicle.get("reg_code") else None,
            "capacity": remote_vehicle.get("capacity"),
            "notes": remote_vehicle.get("notes"),
            "profile_id": remote_vehicle.get("profile_id"),
            "max_speed_kmh": remote_vehicle.get("max_speed_kmh"),
            "acceleration_mps2": remote_vehicle.get("acceleration_mps2"),
            "braking_mps2": remote_vehicle.get("braking_mps2"),
            "eco_mode": remote_vehicle.get("eco_mode", False),
            "performance_profile": remote_vehicle.get("performance_profile"),
        }
    }
    
    # Remove None values for optional fields
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    response = requests.post('http://localhost:1337/api/vehicles',
                           headers={'Content-Type': 'application/json'},
                           json=strapi_data)
    
    if response.status_code in [200, 201]:
        created = response.json()
        return created['data']['id']
    else:
        print(f"Error creating vehicle: {response.status_code} - {response.text}")
        return None

def check_vehicle_exists(vehicle_id):
    """Check if vehicle already exists in Strapi by vehicle_id"""
    try:
        response = requests.get('http://localhost:1337/api/vehicles')
        if response.status_code == 200:
            vehicles = response.json()['data']
            for vehicle in vehicles:
                if vehicle.get('vehicle_id') == str(vehicle_id):
                    return vehicle['id']
        return None
    except Exception as e:
        print(f"Error checking existing vehicles: {e}")
        return None

def migrate_vehicles():
    """Main migration function for vehicles"""
    print("🚐 VEHICLES MIGRATION - Remote PostgreSQL → Strapi")
    print("=" * 60)
    
    # Initialize SSH tunnel
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        # Connect to remote database
        conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all vehicles from remote database
        print("📊 Fetching vehicles from remote database...")
        cursor.execute("""
            SELECT 
                vehicle_id,
                country_id,
                reg_code,
                home_depot_id,
                preferred_route_id,
                status,
                profile_id,
                notes,
                created_at,
                updated_at,
                capacity,
                assigned_driver_id,
                assigned_gps_device_id,
                max_speed_kmh,
                acceleration_mps2,
                braking_mps2,
                eco_mode,
                performance_profile
            FROM vehicles 
            ORDER BY reg_code
        """)
        
        remote_vehicles = cursor.fetchall()
        print(f"Found {len(remote_vehicles)} vehicles in remote database")
        
        if not remote_vehicles:
            print("❌ No vehicles found in remote database")
            return
        
        # Display what we're about to migrate
        print("\n📋 Vehicles to migrate:")
        for vehicle in remote_vehicles:
            status = vehicle['status']
            capacity = vehicle['capacity'] or 'N/A'
            speed = vehicle['max_speed_kmh'] or 'N/A'
            print(f"  - {vehicle['reg_code']} (ID: {vehicle['vehicle_id']}, Status: {status}, Capacity: {capacity}, Max Speed: {speed} km/h)")
        
        # Migration statistics
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n🔄 Starting migration...")
        
        for vehicle in remote_vehicles:
            vehicle_reg = vehicle['reg_code']
            vehicle_id = vehicle['vehicle_id']
            
            print(f"\n--- Processing: {vehicle_reg} ---")
            
            # Check if vehicle already exists
            existing_id = check_vehicle_exists(vehicle_id)
            if existing_id:
                print(f"⏭️  Vehicle already exists (Strapi ID: {existing_id})")
                skipped_count += 1
                continue
            
            # Create vehicle in Strapi
            print("📝 Creating vehicle in Strapi...")
            strapi_id = create_strapi_vehicle(vehicle)
            
            if strapi_id:
                print(f"✅ Successfully created vehicle (Strapi ID: {strapi_id})")
                created_count += 1
            else:
                print(f"❌ Failed to create vehicle")
                error_count += 1
        
        # Final summary
        print(f"\n{'='*60}")
        print("📊 VEHICLES MIGRATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total vehicles processed: {len(remote_vehicles)}")
        print(f"Created: {created_count}")
        print(f"Skipped (already exist): {skipped_count}")
        print(f"Errors: {error_count}")
        
        if error_count == 0:
            if created_count > 0:
                print("🎉 All vehicles migrated successfully!")
            else:
                print("✅ All vehicles were already migrated")
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
        response = requests.get('http://localhost:1337/api/vehicles')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strapi connected - {len(data['data'])} existing vehicles")
            return True
        else:
            print(f"❌ Strapi connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Strapi connection error: {e}")
        return False

if __name__ == "__main__":
    print("🚐 ARKNET VEHICLES MIGRATION")
    print("Migration: Remote PostgreSQL → Strapi API")
    print(f"Timestamp: {__import__('datetime').datetime.now()}")
    print()
    
    # Test connections first
    if not test_strapi_connection():
        print("❌ Cannot proceed - Strapi connection failed")
        sys.exit(1)
    
    # Run migration
    migrate_vehicles()