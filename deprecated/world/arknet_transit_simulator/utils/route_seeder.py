"""
Route Seeder Tool

Usage:
    python route_seeder.py --geojson <path_to_geojson>

- Seeds the database with routes and shapes from a GeoJSON file.
- Supports tab completion for the geojson argument.
"""
import argparse
import os
import sys
import json
from pathlib import Path

try:
    import readline
except ImportError:
    readline = None
import requests

# Optional: argcomplete for tab completion
try:
    import argcomplete
except ImportError:
    argcomplete = None

def print_help():
        print(
"""
Route Seeder Help:
This tool interactively seeds a route and shape from a GeoJSON file using your API.
You will be prompted for:
    - API base URL (e.g. http://localhost:8000/api/v1)
    - Path to the route GeoJSON file (tab completion supported)
    - Country ISO code (e.g. BB)
    - Route short name (e.g. 1, 1A)
    - Route long name (optional)
    - Parishes (optional)
Type 'help' or '?' at any prompt to see this menu again.
Press Ctrl+C at any time to exit gracefully.
""")
    # Create the route

def input_with_completion(prompt, path_complete=False):
    if readline and path_complete:
        def complete(text, state):
            """Tab completion for file paths."""
            import os
            if not text:
                text = ""
            dirname, rest = os.path.split(text)
            if not dirname:
                dirname = "."
            try:
                matches = [os.path.join(dirname, f) for f in os.listdir(dirname) if f.startswith(rest)]
            except FileNotFoundError:
                print(f"[ERROR] Directory not found: {dirname}")
                matches = []
            return matches[state] if state < len(matches) else None
        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind('tab: complete')
        readline.set_completer(complete)
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user (Ctrl+C). Exiting.")
        sys.exit(0)

def main():
    print("Welcome to the Route Seeder CLI. Type 'help' or '?' at any prompt for help.")
    while True:
        api_base = input_with_completion("Enter API base URL (default: http://localhost:8000/api/v1): ").strip()
        if not api_base:
            api_base = "http://localhost:8000/api/v1"
        if api_base.lower() in ('help', '?'):
            print_help()
            continue
        if api_base:
            break
    api_base = api_base.rstrip('/')
    countries_url = api_base + '/countries'
    routes_url = api_base + '/routes'
    shapes_url = api_base + '/shapes'
    route_shapes_url = api_base + '/route_shapes'

    while True:
        geojson_path = input_with_completion("Enter path to route GeoJSON file: ", path_complete=True).strip()
        if geojson_path.lower() in ('help', '?'):
            print_help()
            continue
        if not geojson_path:
            continue
        geojson_path = Path(geojson_path)
        if not geojson_path.exists():
            print(f"GeoJSON file not found: {geojson_path}")
            continue
        break
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson = json.load(f)
    except Exception as e:
        print(f"Failed to read GeoJSON: {e}")
        sys.exit(1)
    features = geojson.get('features', [])
    if not features:
        print("No features found in GeoJSON.")
        sys.exit(1)

    while True:
        iso_code = input_with_completion("Enter country ISO code (default: BB): ").strip().upper()
        if not iso_code:
            iso_code = "BB"
        if iso_code.lower() in ('help', '?'):
            print_help()
            continue
        if iso_code:
            break
    try:
        resp = requests.get(countries_url)
        if resp.status_code != 200:
            print(f"Failed to fetch countries: {resp.status_code} {resp.text}")
            sys.exit(1)
        countries = resp.json()
        country_id = None
        for c in countries:
            if c.get('iso_code', '').upper() == iso_code:
                country_id = c.get('country_id')
                break
        if not country_id:
            print(f"Country with ISO code '{iso_code}' not found in the database. Please seed it first.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user (Ctrl+C). Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"Error fetching country: {e}")
        sys.exit(1)

    while True:
        short_name = input_with_completion("Enter route short_name (e.g. '1'): ").strip()
        if short_name.lower() in ('help', '?'):
            print_help()
            continue
        if short_name:
            break
    long_name = input_with_completion("Enter route long_name (optional): ").strip()
    if long_name.lower() in ('help', '?'):
        print_help()
        long_name = ''
    parishes = input_with_completion("Enter parishes (comma-separated, optional): ").strip()
    if parishes.lower() in ('help', '?'):
        print_help()
        parishes = ''

    # Create the route
    route_payload = {
        'country_id': country_id,
        'short_name': short_name,
        'long_name': long_name or None,
        'parishes': parishes or None,
        'is_active': True
    }
    try:
        route_resp = requests.post(routes_url, json=route_payload)
        if route_resp.status_code not in (200, 201):
            print(f"Failed to create route: {route_resp.status_code} {route_resp.text}")
            sys.exit(1)
        route = route_resp.json()
        print(f"Route created: {route}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user (Ctrl+C). Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"Error creating route: {e}")
        sys.exit(1)

    # For each feature, create a shape and link to the route
    for idx, feature in enumerate(features):
        geometry = feature.get('geometry')
        if not geometry or geometry.get('type') != 'LineString':
            print(f"Skipping feature {idx}: not a LineString.")
            continue
        # Create shape
        shape_payload = {
            'geom': {
                'type': 'LineString',
                'coordinates': geometry['coordinates']
            }
        }
        try:
            shape_resp = requests.post(shapes_url, json=shape_payload)
            if shape_resp.status_code not in (200, 201):
                print(f"Failed to create shape for feature {idx}: {shape_resp.status_code} {shape_resp.text}")
                continue
            shape = shape_resp.json()
            print(f"Shape created: {shape}")
            # Link route and shape
            route_shape_payload = {
                'route_id': route['route_id'],
                'shape_id': shape['shape_id'],
                'variant_code': None,
                'is_default': idx == 0
            }
            rs_resp = requests.post(route_shapes_url, json=route_shape_payload)
            if rs_resp.status_code not in (200, 201):
                print(f"Failed to link route and shape: {rs_resp.status_code} {rs_resp.text}")
                continue
            print(f"Linked route and shape: {rs_resp.json()}")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user (Ctrl+C). Exiting.")
            sys.exit(0)
        except Exception as e:
            print(f"Error creating shape or linking: {e}")
            continue

    print("\nRoute seeding complete.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user (Ctrl+C). Exiting.")
        sys.exit(0)
