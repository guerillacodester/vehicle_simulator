#!/usr/bin/env python3
"""
Master Migration Script - Execute All Table Migrations in Correct Order
========================================================================

This script coordinates the migration of all tables from the remote database 
to Strapi API in the correct dependency order.

MIGRATION ORDER:
1. Countries (already completed ✅)
2. GPS Devices (no dependencies)
3. Drivers (no dependencies)  
4. Depots (depends on countries)
5. Routes (depends on depots)
6. Vehicles (depends on all above + vehicle-status)

Each migration script handles:
- Duplicate detection and skipping
- Relationship mapping between remote UUIDs and Strapi integer IDs
- Error handling and progress reporting
- Verification of migration success

PREREQUISITES:
- SSH tunnel to remote database running on port 5433
- Strapi API running on http://localhost:1337
- All Strapi content types created and API permissions enabled
- Vehicle-status content type populated with status values

USAGE:
python run_all_migrations.py
"""

import subprocess
import sys
import time
from datetime import datetime

# Migration scripts in dependency order
MIGRATION_SCRIPTS = [
    {
        'name': 'GPS Devices',
        'script': 'migrate_gps_devices.py',
        'description': 'GPS devices (no dependencies)',
        'depends_on': []
    },
    {
        'name': 'Drivers', 
        'script': 'migrate_drivers.py',
        'description': 'Driver records (no dependencies)',
        'depends_on': []
    },
    {
        'name': 'Depots',
        'script': 'migrate_depots.py', 
        'description': 'Depot locations (depends on countries)',
        'depends_on': ['countries']
    },
    {
        'name': 'Routes',
        'script': 'migrate_routes.py',
        'description': 'Transit routes (depends on depots)',
        'depends_on': ['depots']
    },
    {
        'name': 'Vehicles',
        'script': 'migrate_vehicles_new.py',
        'description': 'Fleet vehicles (depends on all above + vehicle-status)',
        'depends_on': ['countries', 'gps-devices', 'drivers', 'depots', 'routes', 'vehicle-statuses']
    }
]

def print_header():
    """Print migration header"""
    print("="*80)
    print("ARKNET TRANSIT SYSTEM - COMPLETE DATABASE MIGRATION")
    print("="*80)
    print(f"Started at: {datetime.now()}")
    print()
    print("Migration Order:")
    print("0. Countries ✅ (already completed)")
    for i, script in enumerate(MIGRATION_SCRIPTS, 1):
        deps = f" (depends on: {', '.join(script['depends_on'])})" if script['depends_on'] else ""
        print(f"{i}. {script['name']}{deps}")
    print()

def run_migration_script(script_info):
    """Run a single migration script"""
    print(f"🚀 Starting {script_info['name']} migration...")
    print(f"   Script: {script_info['script']}")
    print(f"   Description: {script_info['description']}")
    print()
    
    try:
        # Run the migration script
        result = subprocess.run(
            [sys.executable, script_info['script']], 
            capture_output=True, 
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {script_info['name']} migration completed successfully!")
            print("Output:")
            print(result.stdout)
            return True
        else:
            print(f"❌ {script_info['name']} migration failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {script_info['name']} migration timed out!")
        return False
    except Exception as e:
        print(f"💥 Error running {script_info['name']} migration: {e}")
        return False

def check_prerequisites():
    """Check if prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if SSH tunnel is running (port 5433)
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5433))
        sock.close()
        if result == 0:
            print("  ✅ SSH tunnel to remote database is running (port 5433)")
        else:
            print("  ❌ SSH tunnel to remote database not found (port 5433)")
            return False
    except Exception as e:
        print(f"  ❌ Error checking SSH tunnel: {e}")
        return False
    
    # Check if Strapi API is running
    import requests
    try:
        response = requests.get("http://localhost:1337/api", timeout=5)
        if response.status_code in [200, 404]:  # 404 is OK, means API is running
            print("  ✅ Strapi API is running (http://localhost:1337)")
        else:
            print(f"  ❌ Strapi API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Error connecting to Strapi API: {e}")
        return False
    
    print("  ✅ All prerequisites met!")
    return True

def main():
    """Main migration orchestration"""
    print_header()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix issues and try again.")
        return False
    
    print("\n" + "="*80)
    print("STARTING MIGRATIONS")
    print("="*80)
    
    # Track results
    completed = []
    failed = []
    
    # Run each migration in order
    for i, script_info in enumerate(MIGRATION_SCRIPTS, 1):
        print(f"\n[{i}/{len(MIGRATION_SCRIPTS)}] {script_info['name'].upper()} MIGRATION")
        print("-" * 50)
        
        success = run_migration_script(script_info)
        
        if success:
            completed.append(script_info['name'])
            print(f"✅ {script_info['name']} migration completed")
        else:
            failed.append(script_info['name'])
            print(f"❌ {script_info['name']} migration failed")
            
            # Ask user if they want to continue
            response = input(f"\nContinue with remaining migrations? (y/n): ").lower()
            if response != 'y':
                print("Migration stopped by user.")
                break
        
        # Small delay between migrations
        if i < len(MIGRATION_SCRIPTS):
            print("\nWaiting 3 seconds before next migration...")
            time.sleep(3)
    
    # Final summary
    print("\n" + "="*80)
    print("MIGRATION SUMMARY")
    print("="*80)
    print(f"Completed at: {datetime.now()}")
    print(f"✅ Completed migrations: {len(completed)}")
    for name in completed:
        print(f"   - {name}")
    
    if failed:
        print(f"❌ Failed migrations: {len(failed)}")
        for name in failed:
            print(f"   - {name}")
    
    total_success_rate = len(completed) / len(MIGRATION_SCRIPTS) * 100
    print(f"\nOverall success rate: {total_success_rate:.1f}%")
    
    if len(completed) == len(MIGRATION_SCRIPTS):
        print("\n🎉 ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        print("Your Arknet Transit System database migration is complete.")
    else:
        print(f"\n⚠️  {len(failed)} migrations failed. Please review errors and re-run failed scripts.")
    
    return len(failed) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)