"""
Countries Seeder Tool

Usage:
    python countries_seeder.py --api http://localhost:8000/api/v1 --name "Barbados" --iso_code "BB"
    python countries_seeder.py --api http://localhost:8000/api/v1 --csv countries.csv
    python countries_seeder.py --api http://localhost:8000/api/v1 --all_online

- Seeds the database with one or more countries using the API endpoint.
- The API base URL should include the version prefix (e.g., /api/v1)
- CSV file should have columns: name,iso_code
- --all_online will fetch all countries from the REST Countries API and seed them automatically.
"""
import argparse
import requests
import sys
import csv
from typing import List, Dict

def parse_args():
    parser = argparse.ArgumentParser(description="Seed one or more countries using the Fleet Manager API.")
    parser.add_argument('--api', type=str, required=True, help='Base URL of the Fleet Manager API (e.g. http://localhost:8000/api/v1)')
    parser.add_argument('--name', type=str, help='Country name (e.g. Barbados)')
    parser.add_argument('--iso_code', type=str, help='Country ISO code (e.g. BB)')
    parser.add_argument('--csv', type=str, help='Path to CSV file with columns: name,iso_code')
    parser.add_argument('--all_online', action='store_true', help='Fetch all countries from the REST Countries API and seed them automatically')
    return parser.parse_args()
def fetch_all_countries_online(caribbean_only=False) -> List[Dict[str, str]]:
    url = 'https://restcountries.com/v3.1/all?fields=name,cca2,region,subregion'
    print("Fetching all countries from REST Countries API...")
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; CountrySeeder/1.0)'}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    countries = []
    for entry in resp.json():
        name = entry.get('name', {}).get('common')
        iso_code = entry.get('cca2')
        region = entry.get('region')
        subregion = entry.get('subregion')
        if caribbean_only:
            if region == 'Americas' and subregion == 'Caribbean' and name and iso_code:
                countries.append({'name': name, 'iso_code': iso_code})
        else:
            if name and iso_code:
                countries.append({'name': name, 'iso_code': iso_code})
    if caribbean_only:
        print(f"Fetched {len(countries)} Caribbean countries from online source.")
    else:
        print(f"Fetched {len(countries)} countries from online source.")
    return countries

def load_countries_from_csv(csv_path: str) -> List[Dict[str, str]]:
    countries = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'name' in row and 'iso_code' in row:
                countries.append({'name': row['name'], 'iso_code': row['iso_code']})
    return countries


def seed_country(countries_url, name, iso_code, existing_countries):
    # Check if country exists in the cached list
    print(f"Checking if country with ISO code '{iso_code}' exists...")
    for c in existing_countries:
        if c.get('iso_code', '').upper() == iso_code.upper():
            print(f"Country already exists: {c}")
            return
    payload = {'name': name, 'iso_code': iso_code}
    # Create country
    print(f"Creating country '{name}' (ISO: {iso_code})...")
    response = requests.post(countries_url, json=payload)
    if response.status_code in (200, 201):
        print(f"Country created: {response.json()}")
        existing_countries.append({'name': name, 'iso_code': iso_code})
    else:
        print(f"Failed to create country: {response.status_code} {response.text}")

def main():
    args = parse_args()
    base_url = args.api.rstrip('/')
    countries_url = base_url + '/countries'
    try:
        # Fetch all existing countries once
        resp = requests.get(countries_url)
        if resp.status_code == 200:
            existing_countries = resp.json()
        else:
            print(f"Warning: Could not fetch existing countries: {resp.status_code} {resp.text}")
            existing_countries = []

        if args.all_online:
            countries = fetch_all_countries_online(caribbean_only=True)
            for c in countries:
                seed_country(countries_url, c['name'], c['iso_code'], existing_countries)
        elif args.csv:
            countries = load_countries_from_csv(args.csv)
            for c in countries:
                seed_country(countries_url, c['name'], c['iso_code'], existing_countries)
        elif args.name and args.iso_code:
            seed_country(countries_url, args.name, args.iso_code, existing_countries)
        else:
            print("You must provide --all_online, --csv, or both --name and --iso_code.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user (Ctrl+C). Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
