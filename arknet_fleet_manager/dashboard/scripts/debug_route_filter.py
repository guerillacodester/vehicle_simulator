#!/usr/bin/env python3
"""
Debug: Show exactly what route_shapes are returned for route 1.
"""
import os
import sys
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

GRAPHQL_URL = os.environ.get('STRAPI_GRAPHQL_URL', 'http://localhost:1337/graphql')
ROUTE_SHORT_NAME = os.environ.get('ROUTE_SHORT_NAME', '1')

GET_ROUTE_SHAPES = '''
query GetRouteShapes($routeShortName: String!, $limit: Int = 500) {
  routeShapes(filters: { route_id: { eq: $routeShortName } }, pagination: { limit: $limit }, sort: ["route_shape_id:asc"]) {
    route_shape_id
    route_id
    shape_id
    is_default
  }
}
'''


def post_graphql(query, variables=None):
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    data = json.dumps(payload).encode('utf-8')
    req = Request(GRAPHQL_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (HTTPError, URLError) as e:
        print(f'GraphQL error: {e}')
        sys.exit(1)


def main():
    print(f'=== Debugging route_shapes filter for route_id="{ROUTE_SHORT_NAME}" ===\n')
    
    res = post_graphql(GET_ROUTE_SHAPES, {'routeShortName': ROUTE_SHORT_NAME})
    if 'errors' in res:
        print('GraphQL errors:', json.dumps(res['errors'], indent=2))
        sys.exit(1)
    
    routeShapes = res.get('data', {}).get('routeShapes', [])
    
    print(f'Total routeShapes returned: {len(routeShapes)}\n')
    
    # Group by route_id to see if filter is working
    by_route_id = {}
    for rs in routeShapes:
        rid = rs.get('route_id')
        by_route_id.setdefault(rid, []).append(rs)
    
    print('Grouped by route_id:')
    for rid, entries in sorted(by_route_id.items()):
        print(f'  route_id="{rid}": {len(entries)} entries')
    
    print('\n--- First 10 routeShapes entries ---')
    for i, rs in enumerate(routeShapes[:10], 1):
        print(f'{i:2d}. route_id="{rs.get("route_id")}" shape_id={rs.get("shape_id")} is_default={rs.get("is_default")}')
    
    if len(routeShapes) > 10:
        print(f'... and {len(routeShapes) - 10} more entries')
    
    # Check if route_id field actually matches what we filtered for
    wrong_route = [rs for rs in routeShapes if rs.get('route_id') != ROUTE_SHORT_NAME]
    if wrong_route:
        print(f'\n⚠️  WARNING: Found {len(wrong_route)} entries with route_id != "{ROUTE_SHORT_NAME}"')
        print('Sample:')
        for rs in wrong_route[:5]:
            print(f'  route_id="{rs.get("route_id")}" shape_id={rs.get("shape_id")}')


if __name__ == '__main__':
    main()
