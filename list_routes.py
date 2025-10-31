#!/usr/bin/env python3
"""
List Routes from Geospatial API

Uses the new production-grade Geospatial Services API to list all routes
and their details. This script helps verify route IDs for spawn configuration.

Usage:
    python list_routes.py
    python list_routes.py --detailed  # Show full route details
    python list_routes.py --geometry  # Include geometry information
"""

import sys
import requests
import argparse
from typing import Dict, List, Optional
from datetime import datetime

# Add common to path for config_provider
sys.path.insert(0, ".")

try:
    from common.config_provider import get_config
    config = get_config()
    GEOSPATIAL_URL = config.infrastructure.geospatial_url
except ImportError:
    GEOSPATIAL_URL = "http://localhost:6000"  # Fallback

STRAPI_URL = "http://localhost:1337"


def get_routes_from_api(detailed: bool = False) -> Optional[List[Dict]]:
    """
    Get all routes from Geospatial API.
    
    Args:
        detailed: If True, include full route details
        
    Returns:
        List of route dictionaries or None if failed
    """
    try:
        url = f"{GEOSPATIAL_URL}/routes/all"
        print(f"🔍 Fetching routes from: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 503:
            print("❌ Geospatial API reports Strapi is unavailable (503)")
            print("   Make sure Strapi is running on http://localhost:1337")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        routes = data.get('routes', [])
        count = data.get('count', 0)
        
        print(f"✅ Retrieved {count} routes")
        return routes
        
    except requests.ConnectionError:
        print(f"❌ Cannot connect to Geospatial API at {GEOSPATIAL_URL}")
        print("   Make sure the geospatial service is running (port 6000)")
        return None
    except requests.Timeout:
        print("❌ Request timed out")
        return None
    except Exception as e:
        print(f"❌ Error fetching routes: {e}")
        return None


def get_route_geometry(route_id: int) -> Optional[Dict]:
    """Get geometry for a specific route."""
    try:
        url = f"{GEOSPATIAL_URL}/routes/{route_id}/geometry"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        print(f"  ⚠️ Could not fetch geometry for route {route_id}: {e}")
        return None


def get_spawn_config(route_doc_id: int) -> Optional[Dict]:
    """Check if spawn config exists for this route."""
    try:
        url = f"{STRAPI_URL}/api/spawn-configs"
        params = {
            'filters[route][documentId][$eq]': route_doc_id,
            'populate': 'route'
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            configs = data.get('data', [])
            if configs:
                # Strapi v5 has flat structure (no 'attributes')
                return configs[0]
        return None
        
    except Exception:
        return None


def display_routes(routes: List[Dict], detailed: bool = False, show_geometry: bool = False):
    """
    Display routes in a formatted table.
    
    Args:
        routes: List of route dictionaries
        detailed: Show full details
        show_geometry: Include geometry information
    """
    if not routes:
        print("\n📭 No routes found")
        return
    
    print("\n" + "="*100)
    print("🚌 ROUTES LISTING")
    print("="*100)
    
    for i, route in enumerate(routes, 1):
        route_id = route.get('id')
        doc_id = route.get('documentId')
        short_name = route.get('route_short_name', 'N/A')
        long_name = route.get('route_long_name', 'N/A')
        route_type = route.get('route_type', 'N/A')
        
        print(f"\n[{i}] Route ID: {route_id} | Document ID: {doc_id}")
        print(f"    Short Name: {short_name}")
        print(f"    Long Name: {long_name}")
        print(f"    Type: {route_type}")
        
        # Check for spawn config
        spawn_config = get_spawn_config(doc_id) if doc_id else None
        if spawn_config:
            # Strapi v5 flat structure
            config_id = spawn_config.get('id')
            name = spawn_config.get('name', 'N/A')
            
            # Config is stored in a JSON field
            config_data = spawn_config.get('config', {})
            dist_params = config_data.get('distribution_params', {})
            pass_per_bldg = dist_params.get('passengers_per_building_per_hour', 'N/A')
            buffer = dist_params.get('spawn_radius_meters', 'N/A')
            
            print(f"    ✅ Spawn Config: ID {config_id}")
            print(f"       - Name: {name}")
            print(f"       - Passengers/building/hour: {pass_per_bldg}")
            print(f"       - Spawn radius meters: {buffer}")
            print(f"       - Has POI weights: {'poi_weights' in config_data}")
            print(f"       - Has hourly rates: {'hourly_rates' in config_data}")
        else:
            print(f"    ❌ No spawn config found")
        
        if detailed:
            print(f"    Color: {route.get('route_color', 'N/A')}")
            print(f"    Text Color: {route.get('route_text_color', 'N/A')}")
            print(f"    Description: {route.get('route_desc', 'N/A')}")
            print(f"    URL: {route.get('route_url', 'N/A')}")
        
        if show_geometry and route_id:
            geom_data = get_route_geometry(route_id)
            if geom_data and geom_data.get('geometry'):
                geom = geom_data['geometry']
                coords_count = len(geom.get('coordinates', []))
                print(f"    📍 Geometry: {geom.get('type', 'N/A')} ({coords_count} coordinates)")
    
    print("\n" + "="*100)
    print(f"Total: {len(routes)} routes")
    print("="*100)


def check_api_health():
    """Check if Geospatial API is healthy."""
    try:
        url = f"{GEOSPATIAL_URL}/meta/health"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Geospatial API: {data.get('status', 'unknown')}")
            print(f"   Database: {data.get('database', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
            return True
        else:
            print(f"⚠️ Geospatial API health check returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Geospatial API health check failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='List routes from Geospatial API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python list_routes.py                    # Basic listing
  python list_routes.py --detailed         # Show full details
  python list_routes.py --geometry         # Include geometry info
  python list_routes.py --detailed --geometry  # Everything
        """
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed route information'
    )
    
    parser.add_argument(
        '--geometry',
        action='store_true',
        help='Include geometry information (requires additional API calls)'
    )
    
    parser.add_argument(
        '--health-check',
        action='store_true',
        help='Only check API health'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*100}")
    print(f"🚌 Route Listing Tool - Using Geospatial API")
    print(f"{'='*100}")
    print(f"Geospatial API: {GEOSPATIAL_URL}")
    print(f"Strapi API: {STRAPI_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")
    
    # Health check
    if not check_api_health():
        print("\n⚠️ Warning: API health check failed, but continuing anyway...")
    
    if args.health_check:
        print("\n✅ Health check complete")
        return
    
    # Get routes
    routes = get_routes_from_api(detailed=args.detailed)
    
    if routes is None:
        print("\n❌ Failed to retrieve routes")
        sys.exit(1)
    
    # Display routes
    display_routes(routes, detailed=args.detailed, show_geometry=args.geometry)
    
    # Summary
    routes_with_config = sum(1 for r in routes if get_spawn_config(r.get('documentId')))
    routes_without_config = len(routes) - routes_with_config
    
    print(f"\n📊 Spawn Config Summary:")
    print(f"   ✅ Routes with spawn config: {routes_with_config}")
    print(f"   ❌ Routes without spawn config: {routes_without_config}")
    
    if routes_without_config > 0:
        print(f"\n💡 Next Steps:")
        print(f"   1. Create spawn-config entries for routes without configs")
        print(f"   2. Use the Strapi admin UI or API to add spawn-configs")
        print(f"   3. Link spawn-configs to route documentId (not id)")


if __name__ == "__main__":
    main()

