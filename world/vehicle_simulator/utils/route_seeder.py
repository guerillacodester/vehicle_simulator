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

# Optional: argcomplete for tab completion
try:
    import argcomplete
except ImportError:
    argcomplete = None

def parse_args():
    parser = argparse.ArgumentParser(description="Seed routes and shapes from a GeoJSON file.")
    parser.add_argument('--geojson', type=str, required=True, help='Path to the GeoJSON file')
    if argcomplete:
        argcomplete.autocomplete(parser)
    return parser.parse_args()

def main():
    args = parse_args()
    geojson_path = Path(args.geojson)
    if not geojson_path.exists():
        print(f"GeoJSON file not found: {geojson_path}")
        sys.exit(1)
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    # TODO: Connect to DB and seed routes/shapes using geojson['features']
    print(f"Loaded {len(geojson['features'])} features from {geojson_path}")
    print("Database seeding logic goes here...")

if __name__ == '__main__':
    main()
