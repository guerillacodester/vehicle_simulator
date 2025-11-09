#!/usr/bin/env python3
"""
Automate route geometry checks against Strapi shapes.

What this does:
- Queries Strapi GraphQL for `routeShapes` and `shapes` for a given route.
- Assembles coordinates in `routeShapes` order.
- Computes distances between consecutive assembled points.
- Reports "seams" where the distance between consecutive points exceeds a configurable threshold (default 0.5 km).
- Prints a human-readable summary and a JSON report to stdout.
- Exits with code 0 when no seams exceed threshold, 2 when seams are found, 1 on other errors.

Usage:
  STRAPI_GRAPHQL_URL=http://localhost:1337/graphql \
  ROUTE_DOCUMENT_ID=gg3pv3z19hhm117v9xth5ezq \
  ROUTE_SHORT_NAME=1 \
  THRESHOLD_KM=0.5 \
  python automate_route_checks.py

"""
import os
import sys
import json
import math
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

GRAPHQL_URL = os.environ.get('STRAPI_GRAPHQL_URL', 'http://localhost:1337/graphql')
DOCUMENT_ID = os.environ.get('ROUTE_DOCUMENT_ID', 'gg3pv3z19hhm117v9xth5ezq')
ROUTE_SHORT_NAME = os.environ.get('ROUTE_SHORT_NAME', '1')
THRESHOLD_KM = float(os.environ.get('THRESHOLD_KM', '0.5'))

GET_ROUTE_SHAPES = '''
query GetRouteShapes($documentId: ID!, $routeShortName: String!, $limit: Int = 200) {
  route(documentId: $documentId) {
    documentId
    short_name
    long_name
  }

  routeShapes(filters: { route_id: { eq: $routeShortName }, is_default: { eq: true } }, pagination: { limit: $limit }, sort: ["route_shape_id:asc"]) {
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


def haversine_km(a, b):
    lon1, lat1 = a
    lon2, lat2 = b
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(x))


def assemble_coords(routeShapes, shapes_rows):
    pts_by_shape = {}
    for r in shapes_rows:
        sid = r.get('shape_id')
        if sid is None:
            continue
        pts_by_shape.setdefault(sid, []).append((r.get('shape_pt_sequence'), r.get('shape_pt_lon'), r.get('shape_pt_lat')))

    coords_concat = []
    seams_info = []
    for rs in routeShapes:
        sid = rs.get('shape_id')
        pts = pts_by_shape.get(sid, [])
        pts_sorted = sorted([p for p in pts if p[1] is not None and p[2] is not None], key=lambda x: x[0])
        seg_coords = [(lon, lat) for (_, lon, lat) in pts_sorted]
        if not seg_coords:
            continue
        # if we have existing coords, compute seam between last and first of new seg
        if coords_concat:
            prev = coords_concat[-1]
            cur_first = seg_coords[0]
            dist = haversine_km(prev, cur_first)
            seams_info.append({'from': prev, 'to': cur_first, 'distance_km': dist, 'shape_prev': None, 'shape_next': sid})
        coords_concat.extend(seg_coords)

    return coords_concat, seams_info


def run_check():
    print('GraphQL URL:', GRAPHQL_URL)
    print('DocumentId:', DOCUMENT_ID, 'Route short name:', ROUTE_SHORT_NAME)
    print('Seam threshold (km):', THRESHOLD_KM)

    print('\n1) Querying routeShapes...')
    res1 = post_graphql(GET_ROUTE_SHAPES, {'documentId': DOCUMENT_ID, 'routeShortName': ROUTE_SHORT_NAME})
    if 'errors' in res1:
        print('Errors from GraphQL (routeShapes):', json.dumps(res1['errors'], indent=2))
        return 1
    route = res1.get('data', {}).get('route')
    routeShapes = res1.get('data', {}).get('routeShapes', [])
    print(f' route found: {route}')
    print(f' routeShapes count: {len(routeShapes)}')
    shape_ids = [rs.get('shape_id') for rs in routeShapes if rs.get('shape_id')]
    print(' shape_ids:', shape_ids)

    if not shape_ids:
        print('No shape_ids found for routeShapes. Exiting.')
        return 0

    print('\n2) Querying shapes for shape_ids...')
    res2 = post_graphql(GET_SHAPES_BY_IDS, {'shapeIds': shape_ids})
    if 'errors' in res2:
        print('Errors from GraphQL (shapes):', json.dumps(res2['errors'], indent=2))
        return 1
    shapes_data = res2.get('data', {}).get('shapes', [])
    print(f' total shape point rows returned: {len(shapes_data)}')

    coords_concat, seams = assemble_coords(routeShapes, shapes_data)
    print(f' concatenated coordinates count: {len(coords_concat)}')
    total_km = 0.0
    distances = []
    for a, b in zip(coords_concat, coords_concat[1:]):
        d = haversine_km(a, b)
        distances.append(d)
        total_km += d
    print(f' assembled route length (km): {total_km:.6f}')

    # examine seams (the seam list has distance from the previous last point to the new segment's first)
    detected_seams = [s for s in seams if s['distance_km'] > THRESHOLD_KM]

    report = {
        'route': route,
        'routeShapes_count': len(routeShapes),
        'shape_point_rows': len(shapes_data),
        'coords_count': len(coords_concat),
        'assembled_km': total_km,
        'threshold_km': THRESHOLD_KM,
        'seams_total': len(seams),
        'seams_detected': len(detected_seams),
        'detected_seams': detected_seams
    }

    print('\n--- Seam summary ---')
    if not seams:
        print('No segment joins found (routeShapes produced a single contiguous shape or no segments).')
    else:
        print(f'Total joins (seams): {len(seams)}')
        if detected_seams:
            print(f'Seams exceeding {THRESHOLD_KM} km: {len(detected_seams)}')
            for i, s in enumerate(detected_seams, 1):
                a = s['from']
                b = s['to']
                print(f"{i:02d}: distance_km={s['distance_km']:.3f} between {a} -> {b}")
        else:
            print(f'No seams exceed threshold {THRESHOLD_KM} km.')

    # print JSON summary to stdout
    print('\n--- JSON report ---')
    print(json.dumps(report, indent=2))

    # exit code: 0 ok, 2 seams found (fail), 0 ok
    if detected_seams:
        return 2
    return 0


if __name__ == '__main__':
    code = run_check()
    sys.exit(code)
