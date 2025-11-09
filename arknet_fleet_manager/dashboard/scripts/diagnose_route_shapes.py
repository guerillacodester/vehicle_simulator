#!/usr/bin/env python3
"""
Diagnose route_shapes for a route - show all shapes and their metadata.
"""
import os
import sys
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

GRAPHQL_URL = os.environ.get('STRAPI_GRAPHQL_URL', 'http://localhost:1337/graphql')
DOCUMENT_ID = os.environ.get('ROUTE_DOCUMENT_ID', 'gg3pv3z19hhm117v9xth5ezq')
ROUTE_SHORT_NAME = os.environ.get('ROUTE_SHORT_NAME', '1')

GET_ALL_ROUTE_SHAPES = '''
query GetAllRouteShapes($routeShortName: String!, $limit: Int = 200) {
  routeShapes(filters: { route_id: { eq: $routeShortName } }, pagination: { limit: $limit }, sort: ["route_shape_id:asc"]) {
    route_shape_id
    route_id
    shape_id
    is_default
    variant_code
  }
}
'''

GET_SHAPE_METADATA = '''
query GetShapeMetadata($shapeIds: [String], $limit: Int = 5000) {
  shapes(filters: { shape_id: { in: $shapeIds } }, pagination: { limit: $limit }) {
    shape_id
    shape_pt_sequence
  }
}
'''


def post_graphql(query, variables=None):
    payload = {'query': query}
    if variables is not None:
        payload['variables'] = variables
    data = json.dumps(payload).encode('utf-8')
    req = Request(GRAPHQL_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        print('HTTPError', e.code, e.read().decode('utf-8'))
        sys.exit(1)
    except URLError as e:
        print('URLError', e)
        sys.exit(1)


def main():
    print('Diagnosing route_shapes for route:', ROUTE_SHORT_NAME)
    print('GraphQL URL:', GRAPHQL_URL)
    print()

    # Get all routeShapes for this route
    res1 = post_graphql(GET_ALL_ROUTE_SHAPES, {'routeShortName': ROUTE_SHORT_NAME})
    if 'errors' in res1:
        print('Errors:', json.dumps(res1['errors'], indent=2))
        sys.exit(1)

    routeShapes = res1.get('data', {}).get('routeShapes', [])
    print(f'Total routeShapes entries: {len(routeShapes)}')
    print()

    # Group by variant/is_default
    by_variant = {}
    for rs in routeShapes:
        key = (rs.get('variant_code'), rs.get('is_default'))
        by_variant.setdefault(key, []).append(rs)

    print('Grouped by (variant_code, is_default):')
    for key, entries in by_variant.items():
        variant, is_default = key
        print(f'  variant={variant}, is_default={is_default}: {len(entries)} entries')

    print()

    # Get point counts for each shape_id
    shape_ids = list(set(rs.get('shape_id') for rs in routeShapes if rs.get('shape_id')))
    print(f'Unique shape_ids referenced: {len(shape_ids)}')
    
    res2 = post_graphql(GET_SHAPE_METADATA, {'shapeIds': shape_ids})
    if 'errors' in res2:
        print('Errors:', json.dumps(res2['errors'], indent=2))
        sys.exit(1)

    shapes_data = res2.get('data', {}).get('shapes', [])
    
    # Count points per shape_id
    pts_by_shape = {}
    for s in shapes_data:
        sid = s.get('shape_id')
        if sid:
            pts_by_shape[sid] = pts_by_shape.get(sid, 0) + 1

    print()
    print('Point counts per shape_id:')
    for rs in routeShapes:
        sid = rs.get('shape_id')
        count = pts_by_shape.get(sid, 0)
        print(f'  {sid}: {count} points (variant={rs.get("variant_code")}, default={rs.get("is_default")})')

    print()
    print('Summary:')
    print(f'  Total routeShapes: {len(routeShapes)}')
    print(f'  Total unique shapes: {len(shape_ids)}')
    print(f'  Total shape points: {sum(pts_by_shape.values())}')
    
    # Find the shape with most points (likely the main route)
    if pts_by_shape:
        max_shape = max(pts_by_shape.items(), key=lambda x: x[1])
        print(f'  Largest shape: {max_shape[0]} with {max_shape[1]} points')
        # Find which routeShape entry references this
        for rs in routeShapes:
            if rs.get('shape_id') == max_shape[0]:
                print(f'    -> variant={rs.get("variant_code")}, is_default={rs.get("is_default")}')


if __name__ == '__main__':
    main()
