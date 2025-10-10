"""
Create Simple Circle Geofences for All Depots
This script creates a geofence for each depot in the system
"""

import requests
import json

STRAPI_URL = "http://localhost:1337/api"

def get_all_depots():
    """Fetch all depots from Strapi"""
    response = requests.get(f"{STRAPI_URL}/depots")
    response.raise_for_status()
    return response.json()['data']

def create_geofence(geofence_id, name, depot_capacity):
    """Create geofence metadata"""
    response = requests.post(f"{STRAPI_URL}/geofences", json={
        "data": {
            "geofence_id": geofence_id,
            "name": name,
            "type": "depot",
            "enabled": True,
            "metadata": {
                "capacity": depot_capacity,
                "auto_generated": True,
                "source": "depot_import"
            }
        }
    })
    response.raise_for_status()
    return response.json()['data']

def create_center_point(geometry_id, lat, lon):
    """Create center point for circle geofence"""
    response = requests.post(f"{STRAPI_URL}/geometry-points", json={
        "data": {
            "geometry_id": geometry_id,
            "point_lat": lat,
            "point_lon": lon,
            "point_sequence": 0,
            "is_active": True
        }
    })
    response.raise_for_status()
    return response.json()['data']

def create_geometry_junction(geofence_id, geometry_id, radius_meters=100.0):
    """Create geofence-geometry junction (links geofence to geometry)"""
    response = requests.post(f"{STRAPI_URL}/geofence-geometries", json={
        "data": {
            "geofence": geofence_id,
            "geometry_id": geometry_id,
            "geometry_type": "circle",
            "is_primary": True,
            "buffer_meters": radius_meters
        }
    })
    response.raise_for_status()
    return response.json()['data']

def create_depot_geofence(depot, radius_meters=100.0):
    """
    Create a complete circle geofence for a depot (3 API calls)
    
    Args:
        depot: Depot object from Strapi
        radius_meters: Radius of circle in meters (default 100m)
    
    Returns:
        dict: Summary of created geofence
    """
    depot_id = depot['depot_id']
    name = depot['name']
    lat = depot['latitude']
    lon = depot['longitude']
    capacity = depot['capacity']
    
    print(f"\n{'='*60}")
    print(f"Creating geofence for: {name}")
    print(f"{'='*60}")
    
    # Step 1: Create geofence metadata
    geofence_id = f"geofence-{depot_id.lower()}"
    print(f"  Step 1/3: Creating geofence metadata...")
    geofence = create_geofence(geofence_id, f"{name} Geofence", capacity)
    print(f"    ✓ Geofence created (ID: {geofence['id']})")
    
    # Step 2: Create center point
    geometry_id = f"geom-{depot_id.lower()}-circle"
    print(f"  Step 2/3: Creating center point ({lat}, {lon})...")
    point = create_center_point(geometry_id, lat, lon)
    print(f"    ✓ Center point created (ID: {point['id']})")
    
    # Step 3: Create geometry junction
    print(f"  Step 3/3: Creating geometry junction (radius: {radius_meters}m)...")
    junction = create_geometry_junction(geofence['id'], geometry_id, radius_meters)
    print(f"    ✓ Junction created (ID: {junction['id']})")
    
    print(f"\n  ✅ SUCCESS: Geofence '{geofence_id}' created for {name}")
    
    return {
        'depot_id': depot_id,
        'depot_name': name,
        'geofence_id': geofence_id,
        'geometry_id': geometry_id,
        'center_lat': lat,
        'center_lon': lon,
        'radius_meters': radius_meters,
        'strapi_ids': {
            'geofence': geofence['id'],
            'point': point['id'],
            'junction': junction['id']
        }
    }

def main():
    """Create geofences for all depots"""
    
    print("\n" + "="*60)
    print("CREATE DEPOT GEOFENCES")
    print("="*60)
    
    # Fetch all depots
    print("\nFetching depots from Strapi...")
    depots = get_all_depots()
    print(f"Found {len(depots)} depots")
    
    # Create geofences
    results = []
    for depot in depots:
        try:
            result = create_depot_geofence(depot, radius_meters=100.0)
            results.append(result)
        except requests.exceptions.HTTPError as e:
            print(f"\n  ❌ ERROR: Failed to create geofence for {depot['name']}")
            print(f"     {e}")
            print(f"     Response: {e.response.text if e.response else 'No response'}")
        except Exception as e:
            print(f"\n  ❌ ERROR: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total depots: {len(depots)}")
    print(f"Geofences created: {len(results)}")
    print(f"Failed: {len(depots) - len(results)}")
    
    if results:
        print("\n📋 Created Geofences:")
        for r in results:
            print(f"  • {r['geofence_id']}: {r['depot_name']}")
            print(f"    Center: ({r['center_lat']}, {r['center_lon']})")
            print(f"    Radius: {r['radius_meters']}m")
        
        # Save results to file
        output_file = "depot_geofences_created.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
    
    print("\n" + "="*60)
    print("✅ DONE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run PostGIS views: create_geofence_postgis_views.sql")
    print("2. Test point-in-polygon queries")
    print("3. Integrate with LocationService")

if __name__ == "__main__":
    main()
