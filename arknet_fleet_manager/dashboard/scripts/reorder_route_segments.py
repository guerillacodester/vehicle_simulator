#!/usr/bin/env python3
"""
Intelligently reorder route shape segments by spatial continuity.

Loads canonical route_1.geojson and Strapi shapes, then finds the correct
ordering of segments that minimizes spatial gaps (seams).
"""
import os
import sys
import json
import math
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

GRAPHQL_URL = os.environ.get('STRAPI_GRAPHQL_URL', 'http://localhost:1337/graphql')
ROUTE_SHORT_NAME = os.environ.get('ROUTE_SHORT_NAME', '1')
CANONICAL_PATH = os.environ.get('CANONICAL_PATH', '../../arknet_transit_simulator/data/route_1.geojson')

GET_ROUTE_SHAPES = '''
query GetRouteShapes($routeShortName: String!, $limit: Int = 200) {
  routeShapes(filters: { route_id: { eq: $routeShortName } }, pagination: { limit: $limit }, sort: ["route_shape_id:asc"]) {
    route_shape_id
    shape_id
    is_default
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


def load_canonical():
    """Load canonical route geometry"""
    path = os.path.normpath(os.path.join(os.path.dirname(__file__), CANONICAL_PATH))
    try:
        with open(path, 'r', encoding='utf-8') as f:
            gj = json.load(f)
    except Exception as e:
        print(f'Cannot load canonical geojson from {path}: {e}')
        return []
    
    coords = []
    if gj.get('type') == 'FeatureCollection':
        for feat in gj.get('features', []):
            geom = feat.get('geometry', {})
            if geom.get('type') == 'LineString':
                coords.extend(geom.get('coordinates', []))
    return coords


def fetch_shapes():
    """Fetch all shapes for the route"""
    res1 = post_graphql(GET_ROUTE_SHAPES, {'routeShortName': ROUTE_SHORT_NAME})
    if 'errors' in res1:
        print('GraphQL errors:', json.dumps(res1['errors'], indent=2))
        sys.exit(1)
    
    routeShapes = res1.get('data', {}).get('routeShapes', [])
    shape_ids = [rs.get('shape_id') for rs in routeShapes if rs.get('shape_id')]
    
    res2 = post_graphql(GET_SHAPES_BY_IDS, {'shapeIds': shape_ids})
    if 'errors' in res2:
        print('GraphQL errors:', json.dumps(res2['errors'], indent=2))
        sys.exit(1)
    
    shapes_data = res2.get('data', {}).get('shapes', [])
    
    # Group points by shape_id
    pts_by_shape = {}
    for s in shapes_data:
        sid = s.get('shape_id')
        if sid:
            pts_by_shape.setdefault(sid, []).append((s.get('shape_pt_sequence'), s.get('shape_pt_lon'), s.get('shape_pt_lat')))
    
    # Build segment list with endpoints
    segments = []
    for rs in routeShapes:
        sid = rs.get('shape_id')
        pts = pts_by_shape.get(sid, [])
        if not pts:
            continue
        pts_sorted = sorted([p for p in pts if p[1] is not None and p[2] is not None], key=lambda x: x[0])
        coords = [(lon, lat) for (_, lon, lat) in pts_sorted]
        if coords:
            segments.append({
                'route_shape_id': rs.get('route_shape_id'),
                'shape_id': sid,
                'coords': coords,
                'start': coords[0],
                'end': coords[-1]
            })
    
    return segments


def find_optimal_ordering(segments, canonical_coords):
    """
    Find ordering of segments that best matches canonical route.
    Uses greedy nearest-neighbor approach starting from first canonical point.
    """
    if not segments or not canonical_coords:
        return []
    
    unused = segments.copy()
    ordered = []
    
    # Find segment closest to canonical start
    start_pt = canonical_coords[0]
    best_idx = 0
    best_dist = float('inf')
    best_reversed = False
    
    for i, seg in enumerate(unused):
        dist_start = haversine_km(start_pt, seg['start'])
        dist_end = haversine_km(start_pt, seg['end'])
        if dist_start < best_dist:
            best_dist = dist_start
            best_idx = i
            best_reversed = False
        if dist_end < best_dist:
            best_dist = dist_end
            best_idx = i
            best_reversed = True
    
    first = unused.pop(best_idx)
    if best_reversed:
        first['coords'] = list(reversed(first['coords']))
        first['start'], first['end'] = first['end'], first['start']
        first['reversed'] = True
    ordered.append(first)
    
    # Greedy: repeatedly find segment whose start is closest to current end
    while unused:
        current_end = ordered[-1]['end']
        best_idx = 0
        best_dist = float('inf')
        best_reversed = False
        
        for i, seg in enumerate(unused):
            dist_start = haversine_km(current_end, seg['start'])
            dist_end = haversine_km(current_end, seg['end'])
            if dist_start < best_dist:
                best_dist = dist_start
                best_idx = i
                best_reversed = False
            if dist_end < best_dist:
                best_dist = dist_end
                best_idx = i
                best_reversed = True
        
        next_seg = unused.pop(best_idx)
        if best_reversed:
            next_seg['coords'] = list(reversed(next_seg['coords']))
            next_seg['start'], next_seg['end'] = next_seg['end'], next_seg['start']
            next_seg['reversed'] = True
        ordered.append(next_seg)
    
    return ordered


def compute_route_length(ordered_segments):
    """Compute total route length from ordered segments"""
    all_coords = []
    for seg in ordered_segments:
        all_coords.extend(seg['coords'])
    
    total = 0.0
    for i in range(len(all_coords) - 1):
        total += haversine_km(all_coords[i], all_coords[i+1])
    return total, len(all_coords)


def main():
    print('=== Intelligent Route Segment Reordering ===')
    print(f'Route: {ROUTE_SHORT_NAME}')
    print()
    
    print('1) Loading canonical route geometry...')
    canonical = load_canonical()
    if not canonical:
        print('ERROR: Could not load canonical geometry')
        sys.exit(1)
    canonical_len = sum(haversine_km(canonical[i], canonical[i+1]) for i in range(len(canonical)-1))
    print(f'   Canonical: {len(canonical)} points, {canonical_len:.3f} km')
    
    print('\n2) Fetching Strapi shape segments...')
    segments = fetch_shapes()
    print(f'   Found {len(segments)} segments')
    
    print('\n3) Finding optimal segment ordering...')
    ordered = find_optimal_ordering(segments, canonical)
    new_length, new_count = compute_route_length(ordered)
    print(f'   Reordered: {new_count} points, {new_length:.3f} km')
    print(f'   Delta from canonical: {abs(canonical_len - new_length):.3f} km')
    
    # Compute seams in new ordering
    seams = []
    for i in range(len(ordered) - 1):
        gap = haversine_km(ordered[i]['end'], ordered[i+1]['start'])
        seams.append(gap)
    
    large_seams = [s for s in seams if s > 0.5]
    print(f'   Seams > 0.5km: {len(large_seams)} (max: {max(seams) if seams else 0:.3f} km)')
    
    print('\n4) Recommended ordering:')
    print('   route_shape_id -> shape_id (reversed?)')
    for i, seg in enumerate(ordered, 1):
        rev_marker = ' [REVERSED]' if seg.get('reversed') else ''
        print(f'   {i:2d}. {seg["route_shape_id"]} -> {seg["shape_id"]}{rev_marker}')
    
    print('\n5) Export as JSON (for patching Strapi):')
    export = {
        'route_id': ROUTE_SHORT_NAME,
        'ordered_segments': [
            {
                'new_sequence': i,
                'route_shape_id': seg['route_shape_id'],
                'shape_id': seg['shape_id'],
                'reversed': seg.get('reversed', False)
            }
            for i, seg in enumerate(ordered, 1)
        ],
        'metrics': {
            'total_points': new_count,
            'route_length_km': new_length,
            'canonical_length_km': canonical_len,
            'delta_km': abs(canonical_len - new_length),
            'seams_above_threshold': len(large_seams),
            'max_seam_km': max(seams) if seams else 0
        }
    }
    print(json.dumps(export, indent=2))
    
    # Write to file
    output_path = f'route_{ROUTE_SHORT_NAME}_reordered.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2)
    print(f'\n✓ Saved to {output_path}')


if __name__ == '__main__':
    main()
