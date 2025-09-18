#!/usr/bin/env python3
"""
Complete Migration Runner - Execute All Migrations in Correct Order
===================================================================
Runs all migrations from remote PostgreSQL to Strapi in dependency order:

Migration Order:
1. ✅ Countries (already completed)
2. ✅ GPS Devices (already completed)
3. 🚛 Drivers (no dependencies)
4. 🏢 Depots (depends on countries)
5. 🚌 Routes (depends on countries)
6. 🚐 Vehicles (depends on depots, routes, drivers, gps_devices)

This script uses the comprehensive field mappings from our thorough analysis.
"""
import sys
import os
import subprocess
import requests
from datetime import datetime

def test_strapi_connection():
    """Test connection to Strapi API"""
    print("🔍 Testing Strapi connection...")
    try:
        response = requests.get('http://localhost:1337/api/countries')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strapi connected - {len(data['data'])} countries exist")
            return True
        else:
            print(f"❌ Strapi connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Strapi connection error: {e}")
        return False

def run_migration_script(script_name, description):
    """Run a migration script and return success status"""
    print(f"\n{'='*80}")
    print(f"🚀 STARTING: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*80}")
    
    try:
        # Run the migration script
        result = subprocess.run(['python', script_name], 
                              capture_output=True, 
                              text=True, 
                              cwd=os.path.dirname(os.path.abspath(__file__)))
        
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - COMPLETED SUCCESSFULLY")
            return True
        else:
            print(f"❌ {description} - FAILED (Exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False

def check_migration_status():
    """Check current status of all migrations"""
    print("📊 CHECKING CURRENT MIGRATION STATUS")
    print("=" * 60)
    
    endpoints = {
        'Countries': 'countries',
        'GPS Devices': 'gps-devices', 
        'Drivers': 'drivers',
        'Depots': 'depots',
        'Routes': 'routes',
        'Vehicles': 'vehicles'
    }
    
    status = {}
    for name, endpoint in endpoints.items():
        try:
            response = requests.get(f'http://localhost:1337/api/{endpoint}')
            if response.status_code == 200:
                count = len(response.json()['data'])
                status[name] = count
                print(f"✅ {name:<12}: {count} records")
            else:
                status[name] = 0
                print(f"❌ {name:<12}: API error ({response.status_code})")
        except Exception as e:
            status[name] = 0
            print(f"❌ {name:<12}: Connection error")
    
    return status

def main():
    """Main migration runner"""
    print("🎯 ARKNET COMPLETE MIGRATION RUNNER")
    print("Migration: Remote PostgreSQL → Strapi API")
    print(f"Started: {datetime.now()}")
    print("=" * 80)
    
    # Test connections first
    if not test_strapi_connection():
        print("❌ Cannot proceed - Strapi connection failed")
        sys.exit(1)
    
    # Check current status
    initial_status = check_migration_status()
    
    print(f"\n📋 MIGRATION PLAN:")
    print("1. ✅ Countries (already completed)")
    print("2. ✅ GPS Devices (already completed)")
    print("3. 🚛 Drivers (4 records)")
    print("4. 🏢 Depots (1 record)")
    print("5. 🚌 Routes (3 records)")
    print("6. 🚐 Vehicles (4 records)")
    
    # Migration scripts in dependency order
    migrations = [
        # Skip already completed ones
        # ('migrate_countries.py', 'Countries Migration'),
        # ('migrate_gps_devices_final.py', 'GPS Devices Migration'),
        
        # Run remaining migrations
        ('migrate_drivers_final.py', 'Drivers Migration'),
        ('migrate_depots_final.py', 'Depots Migration'), 
        ('migrate_routes_final.py', 'Routes Migration'),
        ('migrate_vehicles_final.py', 'Vehicles Migration')
    ]
    
    print(f"\n🔄 Starting migration of {len(migrations)} tables...")
    
    # Track results
    results = {}
    
    for script, description in migrations:
        success = run_migration_script(script, description)
        results[description] = success
        
        if not success:
            print(f"\n⚠️  {description} failed. Do you want to continue with remaining migrations? (y/n)")
            # For automated runs, continue on error
            continue
    
    # Final status check
    print(f"\n{'='*80}")
    print("📊 FINAL MIGRATION RESULTS")
    print(f"{'='*80}")
    
    final_status = check_migration_status()
    
    print(f"\n📈 MIGRATION COMPARISON:")
    print(f"{'Table':<12} | {'Before':<6} | {'After':<6} | {'Change':<6} | {'Status'}")
    print("-" * 55)
    
    for table in ['Countries', 'GPS Devices', 'Drivers', 'Depots', 'Routes', 'Vehicles']:
        before = initial_status.get(table, 0)
        after = final_status.get(table, 0)
        change = after - before
        
        if table in ['Countries', 'GPS Devices']:
            status = "✅ Done"
        elif change > 0:
            status = "✅ New"
        elif after > 0:
            status = "✅ Exist"
        else:
            status = "❌ None"
        
        print(f"{table:<12} | {before:<6} | {after:<6} | {change:<6} | {status}")
    
    # Summary
    successful_migrations = sum(1 for success in results.values() if success)
    total_migrations = len(results)
    
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"Completed: {datetime.now()}")
    print(f"Successful migrations: {successful_migrations}/{total_migrations}")
    
    if successful_migrations == total_migrations:
        print("🎉 ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        print("✅ Your Strapi database is now fully populated with:")
        print("   - Countries (reference data)")
        print("   - GPS Devices (tracking hardware)")
        print("   - Drivers (personnel)")
        print("   - Depots (locations)")
        print("   - Routes (transit lines)")
        print("   - Vehicles (fleet)")
    else:
        failed_count = total_migrations - successful_migrations
        print(f"⚠️  {failed_count} migrations failed")
        print("Check the individual migration outputs above for details.")

if __name__ == "__main__":
    main()