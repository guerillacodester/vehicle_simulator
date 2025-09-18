#!/usr/bin/env python3
"""
Migrate Vehicles from remote database to Strapi API
Migration order: 5/5 (depends on all other entities: countries, depots, routes, drivers, gps-devices, vehicle-status)
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

def get_remote_vehicles():
    """Fetch all vehicles from remote database"""
    try:
        conn = psycopg2.connect(**REMOTE_DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM vehicles ORDER BY vehicle_id")
        vehicles = cursor.fetchall()
        
        conn.close()
        return vehicles
        
    except Exception as e:
        print(f"Error fetching remote vehicles: {e}")
        return None

def get_existing_strapi_vehicles():
    """Get existing vehicles from Strapi to avoid duplicates"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/vehicles?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            existing = {}
            for vehicle in data['data']:
                # Use vehicle_uuid as unique identifier
                if 'vehicle_uuid' in vehicle['attributes']:
                    existing[vehicle['attributes']['vehicle_uuid']] = vehicle
            return existing
        else:
            print(f"Error fetching existing vehicles: {response.status_code}")
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
                if 'country_uuid' in country['attributes']:
                    countries[country['attributes']['country_uuid']] = country['id']
            return countries
        else:
            print(f"Error fetching Strapi countries: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching countries from Strapi: {e}")
        return {}

def get_strapi_depots():
    """Get depots from Strapi for relationship mapping"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/depots?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            depots = {}
            for depot in data['data']:
                if 'depot_uuid' in depot['attributes']:
                    depots[depot['attributes']['depot_uuid']] = depot['id']
            return depots
        else:
            print(f"Error fetching Strapi depots: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching depots from Strapi: {e}")
        return {}

def get_strapi_routes():
    """Get routes from Strapi for relationship mapping"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/routes?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            routes = {}
            for route in data['data']:
                if 'route_uuid' in route['attributes']:
                    routes[route['attributes']['route_uuid']] = route['id']
            return routes
        else:
            print(f"Error fetching Strapi routes: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching routes from Strapi: {e}")
        return {}

def get_strapi_drivers():
    """Get drivers from Strapi for relationship mapping"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/drivers?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            drivers = {}
            for driver in data['data']:
                if 'driver_uuid' in driver['attributes']:
                    drivers[driver['attributes']['driver_uuid']] = driver['id']
            return drivers
        else:
            print(f"Error fetching Strapi drivers: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching drivers from Strapi: {e}")
        return {}

def get_strapi_gps_devices():
    """Get GPS devices from Strapi for relationship mapping"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/gps-devices?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            devices = {}
            for device in data['data']:
                if 'device_uuid' in device['attributes']:
                    devices[device['attributes']['device_uuid']] = device['id']
            return devices
        else:
            print(f"Error fetching Strapi GPS devices: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching GPS devices from Strapi: {e}")
        return {}

def get_strapi_vehicle_statuses():
    """Get vehicle statuses from Strapi for relationship mapping"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/vehicle-statuses?pagination[limit]=1000")
        if response.status_code == 200:
            data = response.json()
            statuses = {}
            for status in data['data']:
                if 'status_name' in status['attributes']:
                    statuses[status['attributes']['status_name'].lower()] = status['id']
            return statuses
        else:
            print(f"Error fetching Strapi vehicle statuses: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching vehicle statuses from Strapi: {e}")
        return {}

def find_relationship_id(uuid_value, lookup_dict):
    """Generic function to find Strapi ID by UUID"""
    return lookup_dict.get(str(uuid_value)) if uuid_value else None

def map_vehicle_status(remote_status, strapi_statuses):
    """Map remote vehicle status to Strapi vehicle-status relationship"""
    if not remote_status:
        return None
    
    # Map common status values (you may need to adjust based on your data)
    status_mapping = {
        'active': 'active',
        'inactive': 'inactive', 
        'maintenance': 'maintenance',
        'retired': 'retired',
        'out_of_service': 'out_of_service',
        'repair': 'maintenance',  # Map repair to maintenance
        'available': 'active',    # Map available to active
        'unavailable': 'inactive' # Map unavailable to inactive
    }
    
    mapped_status = status_mapping.get(remote_status.lower(), remote_status.lower())
    return strapi_statuses.get(mapped_status)

def create_strapi_vehicle(remote_vehicle, relationship_lookups):
    """Create a vehicle in Strapi via API"""
    
    # Extract relationship lookups
    countries = relationship_lookups['countries']
    depots = relationship_lookups['depots']
    routes = relationship_lookups['routes']
    drivers = relationship_lookups['drivers']
    gps_devices = relationship_lookups['gps_devices']
    vehicle_statuses = relationship_lookups['vehicle_statuses']
    
    # Map direct fields
    strapi_data = {
        "data": {
            "vehicle_uuid": str(remote_vehicle['vehicle_id']),
            "reg_code": remote_vehicle.get('reg_code'),
            "make": remote_vehicle.get('make'),
            "model": remote_vehicle.get('model'),
            "year": remote_vehicle.get('year'),
            "capacity": remote_vehicle.get('capacity'),
            "fuel_type": remote_vehicle.get('fuel_type'),
            "engine_size": remote_vehicle.get('engine_size'),
            "odometer": remote_vehicle.get('odometer'),
            "purchase_date": remote_vehicle.get('purchase_date'),
            "purchase_cost": float(remote_vehicle['purchase_cost']) if remote_vehicle.get('purchase_cost') else None,
            "insurance_policy": remote_vehicle.get('insurance_policy'),
            "insurance_expiry": remote_vehicle.get('insurance_expiry'),
            "last_service": remote_vehicle.get('last_service'),
            "next_service_due": remote_vehicle.get('next_service_due'),
            "notes": remote_vehicle.get('notes')
        }
    }
    
    # Map relationships
    if remote_vehicle.get('country_id'):
        country_id = find_relationship_id(remote_vehicle['country_id'], countries)
        if country_id:
            strapi_data["data"]["country"] = country_id
    
    if remote_vehicle.get('home_depot_id'):
        depot_id = find_relationship_id(remote_vehicle['home_depot_id'], depots)
        if depot_id:
            strapi_data["data"]["depot"] = depot_id
    
    if remote_vehicle.get('preferred_route_id'):
        route_id = find_relationship_id(remote_vehicle['preferred_route_id'], routes)
        if route_id:
            strapi_data["data"]["route"] = route_id
    
    if remote_vehicle.get('assigned_driver_id'):
        driver_id = find_relationship_id(remote_vehicle['assigned_driver_id'], drivers)
        if driver_id:
            strapi_data["data"]["driver"] = driver_id
    
    if remote_vehicle.get('assigned_gps_device_id'):
        gps_device_id = find_relationship_id(remote_vehicle['assigned_gps_device_id'], gps_devices)
        if gps_device_id:
            strapi_data["data"]["gps_device"] = gps_device_id
    
    # Map vehicle status
    if remote_vehicle.get('status'):
        status_id = map_vehicle_status(remote_vehicle['status'], vehicle_statuses)
        if status_id:
            strapi_data["data"]["vehicle_status"] = status_id
    
    # Remove None values
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    try:
        response = requests.post(
            f"{STRAPI_API_URL}/vehicles",
            headers=STRAPI_HEADERS,
            json=strapi_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error creating vehicle: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling Strapi API: {e}")
        return None

def migrate_vehicles():
    """Main migration function for vehicles"""
    
    print("=== VEHICLES MIGRATION ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Load all relationship mappings
    print("Loading relationship mappings from Strapi...")
    
    relationship_lookups = {
        'countries': get_strapi_countries(),
        'depots': get_strapi_depots(),
        'routes': get_strapi_routes(),
        'drivers': get_strapi_drivers(),
        'gps_devices': get_strapi_gps_devices(),
        'vehicle_statuses': get_strapi_vehicle_statuses()
    }
    
    for name, lookup in relationship_lookups.items():
        print(f"  - {name}: {len(lookup)} records")
    
    # Fetch remote vehicles
    print("\nFetching vehicles from remote database...")
    remote_vehicles = get_remote_vehicles()
    
    if not remote_vehicles:
        print("No vehicles found or error occurred")
        return
    
    print(f"Found {len(remote_vehicles)} vehicles in remote database")
    
    # Get existing Strapi vehicles
    print("Checking existing vehicles in Strapi...")
    existing_vehicles = get_existing_strapi_vehicles()
    print(f"Found {len(existing_vehicles)} existing vehicles in Strapi")
    
    # Migration counters
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    print("\nStarting migration...\n")
    
    for i, vehicle in enumerate(remote_vehicles, 1):
        vehicle_uuid = str(vehicle['vehicle_id'])
        reg_code = vehicle.get('reg_code', 'Unknown')
        
        print(f"[{i}/{len(remote_vehicles)}] Processing {reg_code} ({vehicle_uuid})")
        
        # Check if vehicle already exists
        if vehicle_uuid in existing_vehicles:
            print(f"  → Skipped (already exists)")
            skipped_count += 1
            continue
        
        # Create the vehicle
        result = create_strapi_vehicle(vehicle, relationship_lookups)
        
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
    print(f"Total vehicles processed: {len(remote_vehicles)}")
    print(f"Created: {created_count}")
    print(f"Skipped (already exist): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Completed at: {datetime.now()}")
    
    if error_count == 0:
        print("✅ All vehicles migrated successfully!")
    else:
        print(f"⚠️  {error_count} vehicles failed to migrate")

def verify_migration():
    """Verify the migration by comparing counts"""
    print("\n=== VERIFICATION ===")
    
    # Count remote vehicles
    remote_vehicles = get_remote_vehicles()
    remote_count = len(remote_vehicles) if remote_vehicles else 0
    
    # Count Strapi vehicles
    strapi_vehicles = get_existing_strapi_vehicles()
    strapi_count = len(strapi_vehicles)
    
    print(f"Remote vehicles: {remote_count}")
    print(f"Strapi vehicles: {strapi_count}")
    
    if remote_count == strapi_count:
        print("✅ Counts match - migration verified!")
    else:
        print(f"⚠️  Count mismatch - {remote_count - strapi_count} vehicles missing")

if __name__ == "__main__":
    migrate_vehicles()
    verify_migration()