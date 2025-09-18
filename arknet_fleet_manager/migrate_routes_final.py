#!/usr/bin/env python3
"""
Routes Migration Script - From Remote PostgreSQL to Strapi
===========================================================
Migrates route records using comprehensive field mappings from analysis.

Field Mappings (from comprehensive analysis):
- route_id (UUID) → route_id (String) [REQUIRED]
- short_name (String) → short_name (String) [REQUIRED]
- long_name (String) → long_name (String) [OPTIONAL]
- parishes (String) → parishes (String) [OPTIONAL]
- description (String) → description (String) [OPTIONAL]
- color (String) → color (String) [OPTIONAL]
- is_active (Boolean) → is_active (Boolean) [OPTIONAL]
- valid_from (Date) → valid_from (String) [OPTIONAL]
- valid_to (Date) → valid_to (String) [OPTIONAL]

Remote Table: routes (3 records)
Strapi Endpoint: /api/routes
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

def create_strapi_route(remote_route):
    """Create route in Strapi - FIELD MAPPINGS FROM COMPREHENSIVE ANALYSIS"""
    
    strapi_data = {
        "data": {
            "route_id": str(remote_route.get("route_id")) if remote_route.get("route_id") else None,
            "short_name": str(remote_route.get("short_name")) if remote_route.get("short_name") else None,
            "is_active": remote_route.get("is_active", False),
            "long_name": str(remote_route.get("long_name")) if remote_route.get("long_name") else None,
            "parishes": remote_route.get("parishes"),
            "description": remote_route.get("description"),
            "color": remote_route.get("color"),
            "valid_from": str(remote_route.get("valid_from")) if remote_route.get("valid_from") else None,
            "valid_to": str(remote_route.get("valid_to")) if remote_route.get("valid_to") else None,
        }
    }
    
    # Remove None values for optional fields
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    response = requests.post('http://localhost:1337/api/routes',
                           headers={'Content-Type': 'application/json'},
                           json=strapi_data)
    
    if response.status_code in [200, 201]:
        created = response.json()
        return created['data']['id']
    else:
        print(f"Error creating route: {response.status_code} - {response.text}")
        return None

def check_route_exists(route_id):
    """Check if route already exists in Strapi by route_id"""
    try:
        response = requests.get('http://localhost:1337/api/routes')
        if response.status_code == 200:
            routes = response.json()['data']
            for route in routes:
                if route.get('route_id') == str(route_id):
                    return route['id']
        return None
    except Exception as e:
        print(f"Error checking existing routes: {e}")
        return None

def migrate_routes():
    """Main migration function for routes"""
    print("🚌 ROUTES MIGRATION - Remote PostgreSQL → Strapi")
    print("=" * 60)
    
    # Initialize SSH tunnel
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        # Connect to remote database
        conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all routes from remote database
        print("📊 Fetching routes from remote database...")
        cursor.execute("""
            SELECT 
                route_id,
                country_id,
                short_name,
                long_name,
                parishes,
                is_active,
                valid_from,
                valid_to,
                created_at,
                updated_at,
                description,
                color
            FROM routes 
            ORDER BY short_name
        """)
        
        remote_routes = cursor.fetchall()
        print(f"Found {len(remote_routes)} routes in remote database")
        
        if not remote_routes:
            print("❌ No routes found in remote database")
            return
        
        # Display what we're about to migrate
        print("\n📋 Routes to migrate:")
        for route in remote_routes:
            active_status = "Active" if route['is_active'] else "Inactive"
            print(f"  - Route {route['short_name']}: {route['long_name']} (ID: {route['route_id']}, {active_status})")
        
        # Migration statistics
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n🔄 Starting migration...")
        
        for route in remote_routes:
            route_name = f"Route {route['short_name']}"
            route_id = route['route_id']
            
            print(f"\n--- Processing: {route_name} ---")
            
            # Check if route already exists
            existing_id = check_route_exists(route_id)
            if existing_id:
                print(f"⏭️  Route already exists (Strapi ID: {existing_id})")
                skipped_count += 1
                continue
            
            # Create route in Strapi
            print("📝 Creating route in Strapi...")
            strapi_id = create_strapi_route(route)
            
            if strapi_id:
                print(f"✅ Successfully created route (Strapi ID: {strapi_id})")
                created_count += 1
            else:
                print(f"❌ Failed to create route")
                error_count += 1
        
        # Final summary
        print(f"\n{'='*60}")
        print("📊 ROUTES MIGRATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total routes processed: {len(remote_routes)}")
        print(f"Created: {created_count}")
        print(f"Skipped (already exist): {skipped_count}")
        print(f"Errors: {error_count}")
        
        if error_count == 0:
            if created_count > 0:
                print("🎉 All routes migrated successfully!")
            else:
                print("✅ All routes were already migrated")
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
        response = requests.get('http://localhost:1337/api/routes')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strapi connected - {len(data['data'])} existing routes")
            return True
        else:
            print(f"❌ Strapi connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Strapi connection error: {e}")
        return False

if __name__ == "__main__":
    print("🚌 ARKNET ROUTES MIGRATION")
    print("Migration: Remote PostgreSQL → Strapi API")
    print(f"Timestamp: {__import__('datetime').datetime.now()}")
    print()
    
    # Test connections first
    if not test_strapi_connection():
        print("❌ Cannot proceed - Strapi connection failed")
        sys.exit(1)
    
    # Run migration
    migrate_routes()