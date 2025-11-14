#!/usr/bin/env python3
import os
import sys
import json
import math
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

GRAPHQL_URL = os.environ.get('STRAPI_GRAPHQL_URL', 'http://localhost:1337/graphql')
DOCUMENT_ID = os.environ.get('ROUTE_DOCUMENT_ID', 'gg3pv3z19hhm117v9xth5ezq')
ROUTE_SHORT_NAME = os.environ.get('ROUTE_SHORT_NAME', '1')

GET_ROUTE_SHAPES = '''
query GetRouteShapes($documentId: ID!, $routeShortName: String!, $limit: Int = 200) {
  route(documentId: $documentId) {
    documentId
    short_name
    long_name
  }

  routeShapes(filters: { route_id: { eq: $routeShortName } }, pagination: { limit: $limit }, sort: ["route_shape_id:asc"]) {
    route_shape_id
    shape_id
    is_default
    variant_code
  }
}
'''

GET_SHAPES_BY_IDS = '''
query GetShapesForRoute($shapeIds: [String], $limit: Int = 5000) {
    shapes(filters: { shape_id: { in: $shapeIds } }, pagination: { limit: $limit }, sort: ["shape_id:asc", "shape_pt_sequence:asc"]) {
        shape_id
        shape_pt_sequence
        shape_pt_lat
        shape_pt_lon
        shape_dist_traveled
    }
}
'''


def post_graphql(query, variables=None):
    payload = { 'query': query }
    if variables is not None:
        payload['variables'] = variables
    data = json.dumps(payload).encode('utf-8')
    req = Request(GRAPHQL_URL, data=data, headers={ 'Content-Type': 'application/json' })
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        print('HTTPError', e.code, e.read().decode('utf-8'))
        sys.exit(1)
    except URLError as e:
        print('URLError', e)
        sys.exit(1)


def haversine_km(a, b):
    # a,b are (lon,lat)
    lon1, lat1 = a
    lon2, lat2 = b
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(x))


def load_canonical(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            gj = json.load(f)
    except Exception as e:
        print('Cannot load canonical geojson:', e)
        return None
    # assume single FeatureCollection with LineString coords in first feature
    coords = []
    if gj.get('type') == 'FeatureCollection':
        feats = gj.get('features', [])
        for feat in feats:
            geom = feat.get('geometry') or {}
            if geom.get('type') == 'LineString':
                coords.extend(geom.get('coordinates', []))
            elif geom.get('type') == 'MultiLineString':
                for line in geom.get('coordinates', []):
                    coords.extend(line)
    elif gj.get('type') == 'Feature':
        geom = gj.get('geometry', {})
        if geom.get('type') == 'LineString':
            coords = geom.get('coordinates', [])
    return coords


def compute_length(coords):
    if not coords or len(coords) < 2:
        return 0.0
    total = 0.0
    prev = coords[0]
    for c in coords[1:]:
        total += haversine_km((prev[0], prev[1]), (c[0], c[1]))
        prev = c
    return total


def main():
    print('GraphQL URL:', GRAPHQL_URL)
    print('DocumentId:', DOCUMENT_ID, 'Route short name:', ROUTE_SHORT_NAME)

    print('\n1) Querying routeShapes...')
    res1 = post_graphql(GET_ROUTE_SHAPES, { 'documentId': DOCUMENT_ID, 'routeShortName': ROUTE_SHORT_NAME })
    if 'errors' in res1:
        print('Errors from GraphQL (routeShapes):', json.dumps(res1['errors'], indent=2))
        sys.exit(1)
    route = res1.get('data', {}).get('route')
    routeShapes = res1.get('data', {}).get('routeShapes', [])
    print(f' route found: {route}')
    print(f' routeShapes count: {len(routeShapes)}')
    shape_ids = [rs.get('shape_id') for rs in routeShapes if rs.get('shape_id')]
    print(' shape_ids:', shape_ids)

    if not shape_ids:
        print('No shape_ids found for routeShapes. Exiting.')
        sys.exit(0)

    print('\n2) Querying shapes for shape_ids...')
    res2 = post_graphql(GET_SHAPES_BY_IDS, { 'shapeIds': shape_ids })
    if 'errors' in res2:
        print('Errors from GraphQL (shapes):', json.dumps(res2['errors'], indent=2))
        sys.exit(1)
    shapes_data = res2.get('data', {}).get('shapes', [])
    print(f' total shape point rows returned: {len(shapes_data)}')

    # group
    pts_by_shape = {}
    total_points = 0
    for attrs in shapes_data:
        sid = attrs.get('shape_id')
        if sid is None:
            continue
        pts_by_shape.setdefault(sid, []).append((attrs.get('shape_pt_sequence'), attrs.get('shape_pt_lon'), attrs.get('shape_pt_lat')))
        total_points += 1
    print(' grouped shapes:', {k: len(v) for k, v in pts_by_shape.items()})

    # sort each by sequence
    coords_concat = []
    for rs in routeShapes:
        sid = rs.get('shape_id')
        pts = pts_by_shape.get(sid, [])
        pts_sorted = sorted([p for p in pts if p[1] is not None and p[2] is not None], key=lambda x: x[0])
        seg_coords = [(lon, lat) for (_, lon, lat) in pts_sorted]
        coords_concat.extend(seg_coords)

    print(f' concatenated coordinates count: {len(coords_concat)}')
    km = compute_length(coords_concat)
    print(f' assembled route length (km): {km:.6f}')
    # Print every assembled coordinate pair to stdout (lon, lat)
    if len(coords_concat) == 0:
        print('No coordinates assembled.')
    else:
        print('\n--- Assembled coordinates (lon, lat) ---')
        for idx, c in enumerate(coords_concat, 1):
            # print index to make it easier to reference points
            print(f'{idx:04d}: {c[0]:.8f}, {c[1]:.8f}')
        print('--- end of coordinates ---')

    # compare to canonical
    canonical_path = os.path.join('..', '..', 'arknet_transit_simulator', 'data', 'route_1.geojson')
    canonical_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'arknet_transit_simulator', 'data', 'route_1.geojson'))
    canonical_coords = load_canonical(canonical_path)
    if canonical_coords is None:
        print('Canonical not found or could not be loaded at', canonical_path)
    else:
        print(f' canonical coords count: {len(canonical_coords)}')
        canonical_km = compute_length(canonical_coords)
        print(f' canonical route length (km): {canonical_km:.6f}')
        print(f' delta km (canonical - assembled): {canonical_km - km:.6f}')

if __name__ == '__main__':
    main()
