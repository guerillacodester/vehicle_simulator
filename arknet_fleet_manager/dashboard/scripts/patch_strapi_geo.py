"""
Patch Strapi route's geojson_data with canonical GeoJSON from repo.

Usage:
  Set environment variables STRAPI_URL (e.g. http://localhost:1337/graphql) and
  STRAPI_TOKEN (Strapi admin API token or bearer token with write access).

  python patch_strapi_geo.py --document-id gg3pv3z19hhm117v9xth5ezq --geo-file ../../arknet_transit_simulator/data/route_1.geojson

This script performs a GraphQL mutation using the UPDATE_ROUTE_MUTATION defined by the dashboard GraphQL documents.
It will ask for confirmation before modifying Strapi and will first attempt a dry-run if --dry-run is provided.
"""

import os
import json
import argparse
import requests

GRAPHQL_URL = os.environ.get('STRAPI_URL', 'http://localhost:1337/graphql')
AUTH_TOKEN = os.environ.get('STRAPI_TOKEN')

UPDATE_MUTATION = '''
mutation UpdateRoute($documentId: ID!, $data: JSON!) {
  updateRoute(documentId: $documentId, data: $data) {
    documentId
  }
}
'''

def load_geojson(path):
    with open(path, 'r', encoding='utf8') as fh:
        return json.load(fh)

def run_mutation(document_id, geojson, dry_run=False):
    variables = {
        'documentId': document_id,
        'data': { 'geojson_data': geojson }
    }
    payload = { 'query': UPDATE_MUTATION, 'variables': variables }
    headers = { 'Content-Type': 'application/json' }
    if AUTH_TOKEN:
        headers['Authorization'] = f'Bearer {AUTH_TOKEN}'

    if dry_run:
        print('DRY RUN: would send mutation to', GRAPHQL_URL)
        print('Headers:', {k:v for k,v in headers.items() if k!='Authorization'})
        print('Variables keys:', list(variables.keys()))
        return None

    resp = requests.post(GRAPHQL_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if 'errors' in data:
        raise RuntimeError('GraphQL errors: %s' % data['errors'])
    return data['data']

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--document-id', required=True)
    p.add_argument('--geo-file', required=True)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    geo = load_geojson(args.geo_file)

    print('Loaded geojson file:', args.geo_file)
    print('Document ID:', args.document_id)
    if args.dry_run:
        run_mutation(args.document_id, geo, dry_run=True)
        print('Dry run complete. No changes made.')
        return

    confirm = input('Proceed to update Strapi route geojson_data? Type YES to continue: ')
    if confirm != 'YES':
        print('Aborted by user.')
        return

    result = run_mutation(args.document_id, geo, dry_run=False)
    print('Mutation result:', result)

if __name__ == '__main__':
    main()
