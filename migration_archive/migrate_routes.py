#!/usr/bin/env python3
"""
Migrate Routes from remote database to Strapi API
Migration order: 4/5 (depends on depots and countries)
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

def get_remote_routes():
    """Fetch all routes from remote database"""
    try:
        conn = psycopg2.connect(**REMOTE_DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM routes ORDER BY route_id")
        routes = cursor.fetchall()
        
        conn.close()
        return routes
        
    except Exception as e:
        print(f"Error fetching remote routes: {e}")
        return None

def get_existing_strapi_routes():
    """Get existing routes from Strapi to avoid duplicates"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/routes?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            existing = {}
            for route in data['data']:
                # Use route_uuid as unique identifier
                if 'route_uuid' in route['attributes']:
                    existing[route['attributes']['route_uuid']] = route
            return existing
        else:
            print(f"Error fetching existing routes: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error connecting to Strapi: {e}")
        return {}

def get_strapi_depots():
    """Get depots from Strapi for relationship mapping"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/depots?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            depots = {}
            for depot in data['data']:
                # Map by depot_uuid for lookup
                if 'depot_uuid' in depot['attributes']:
                    depots[depot['attributes']['depot_uuid']] = depot['id']
            return depots
        else:
            print(f"Error fetching Strapi depots: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching depots from Strapi: {e}")
        return {}

def get_strapi_countries():
    """Get countries from Strapi for relationship mapping"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/countries?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            countries = {}
            for country in data['data']:
                # Map by country_uuid for lookup (if available)
                if 'country_uuid' in country['attributes']:
                    countries[country['attributes']['country_uuid']] = country['id']
            return countries
        else:
            print(f"Error fetching Strapi countries: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching countries from Strapi: {e}")
        return {}

def find_depot_id_by_uuid(depot_uuid, strapi_depots):
    """Find Strapi depot ID by remote depot UUID"""
    return strapi_depots.get(str(depot_uuid))

def find_country_id_by_uuid(country_uuid, strapi_countries):
    """Find Strapi country ID by remote country UUID"""
    return strapi_countries.get(str(country_uuid))

def create_strapi_route(remote_route, strapi_depots, strapi_countries):
    """Create a route in Strapi via API"""
    
    # Map remote fields to Strapi fields
    strapi_data = {
        "data": {
            "route_uuid": str(remote_route['route_id']),  # Map UUID to string
            "route_number": remote_route.get('route_number'),
            "route_name": remote_route.get('route_name'),
            "description": remote_route.get('description'),
            "start_location": remote_route.get('start_location'),
            "end_location": remote_route.get('end_location'),
            "distance_km": float(remote_route['distance_km']) if remote_route.get('distance_km') else None,
            "estimated_duration": remote_route.get('estimated_duration'),
            "fare": float(remote_route['fare']) if remote_route.get('fare') else None,
            "service_type": remote_route.get('service_type'),
            "frequency": remote_route.get('frequency'),
            "operating_hours": remote_route.get('operating_hours'),
            "status": remote_route.get('status', 'unknown'),
            "notes": remote_route.get('notes')
        }
    }
    
    # Handle depot relationship (origin depot)
    if remote_route.get('origin_depot_id'):
        depot_strapi_id = find_depot_id_by_uuid(remote_route['origin_depot_id'], strapi_depots)
        if depot_strapi_id:
            strapi_data["data"]["depot"] = depot_strapi_id
    
    # Handle country relationship if available
    if remote_route.get('country_id'):
        country_strapi_id = find_country_id_by_uuid(remote_route['country_id'], strapi_countries)
        if country_strapi_id:
            strapi_data["data"]["country"] = country_strapi_id
    
    # Remove None values
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    try:
        response = requests.post(
            f"{STRAPI_API_URL}/routes",
            headers=STRAPI_HEADERS,
            json=strapi_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error creating route: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling Strapi API: {e}")
        return None

def migrate_routes():
    """Main migration function for routes"""
    
    print("=== ROUTES MIGRATION ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Get Strapi depots for relationship mapping
    print("Loading depots from Strapi for relationship mapping...")
    strapi_depots = get_strapi_depots()
    print(f"Found {len(strapi_depots)} depots in Strapi")
    
    # Get Strapi countries for relationship mapping
    print("Loading countries from Strapi for relationship mapping...")
    strapi_countries = get_strapi_countries()
    print(f"Found {len(strapi_countries)} countries in Strapi")
    
    # Fetch remote routes
    print("Fetching routes from remote database...")
    remote_routes = get_remote_routes()
    
    if not remote_routes:
        print("No routes found or error occurred")
        return
    
    print(f"Found {len(remote_routes)} routes in remote database")
    
    # Get existing Strapi routes
    print("Checking existing routes in Strapi...")
    existing_routes = get_existing_strapi_routes()
    print(f"Found {len(existing_routes)} existing routes in Strapi")
    
    # Migration counters
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    print("\nStarting migration...\n")
    
    for i, route in enumerate(remote_routes, 1):
        route_uuid = str(route['route_id'])
        route_name = route.get('route_name', route.get('route_number', 'Unknown'))
        
        print(f"[{i}/{len(remote_routes)}] Processing {route_name} ({route_uuid})")
        
        # Check if route already exists
        if route_uuid in existing_routes:
            print(f"  → Skipped (already exists)")
            skipped_count += 1
            continue
        
        # Create the route
        result = create_strapi_route(route, strapi_depots, strapi_countries)
        
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
    print(f"Total routes processed: {len(remote_routes)}")
    print(f"Created: {created_count}")
    print(f"Skipped (already exist): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Completed at: {datetime.now()}")
    
    if error_count == 0:
        print("✅ All routes migrated successfully!")
    else:
        print(f"⚠️  {error_count} routes failed to migrate")

def verify_migration():
    """Verify the migration by comparing counts"""
    print("\n=== VERIFICATION ===")
    
    # Count remote routes
    remote_routes = get_remote_routes()
    remote_count = len(remote_routes) if remote_routes else 0
    
    # Count Strapi routes
    strapi_routes = get_existing_strapi_routes()
    strapi_count = len(strapi_routes)
    
    print(f"Remote routes: {remote_count}")
    print(f"Strapi routes: {strapi_count}")
    
    if remote_count == strapi_count:
        print("✅ Counts match - migration verified!")
    else:
        print(f"⚠️  Count mismatch - {remote_count - strapi_count} routes missing")

if __name__ == "__main__":
    migrate_routes()
    verify_migration()