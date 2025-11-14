#!/usr/bin/env python3
"""
Route Geometry Validator

Validates route geometry fetched from Strapi against quality thresholds.
Can be used in CI/CD pipelines or as a standalone validation tool.
"""
import os
import sys
import json
import math
from typing import List, Tuple, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

GRAPHQL_URL = os.environ.get('STRAPI_GRAPHQL_URL', 'http://localhost:1337/graphql')
SEAM_THRESHOLD_KM = float(os.environ.get('SEAM_THRESHOLD_KM', '0.5'))
MIN_POINTS = int(os.environ.get('MIN_POINTS', '10'))
MIN_LENGTH_KM = float(os.environ.get('MIN_LENGTH_KM', '1.0'))

GET_ROUTE_SHAPES = '''
query GetRouteShapes($routeShortName: String!, $limit: Int = 500) {
  routeShapes(
    filters: { route_id: { eq: $routeShortName } }
    pagination: { limit: $limit }
    sort: ["route_shape_id:asc"]
  ) {
    route_shape_id
    shape_id
  }
}
'''

GET_SHAPES_BY_IDS = '''
query GetShapesByIds($shapeIds: [String]!, $limit: Int = 5000) {
  shapes(
    filters: { shape_id: { in: $shapeIds } }
    pagination: { limit: $limit }
    sort: ["shape_id:asc", "shape_pt_sequence:asc"]
  ) {
    shape_id
    shape_pt_sequence
    shape_pt_lat
    shape_pt_lon
  }
}
'''


def post_graphql(query: str, variables: Optional[Dict] = None) -> Dict:
    """Execute GraphQL query"""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    
    data = json.dumps(payload).encode('utf-8')
    req = Request(GRAPHQL_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (HTTPError, URLError) as e:
        raise Exception(f'GraphQL request failed: {e}')


def haversine(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate haversine distance in km"""
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371.0
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def fetch_and_order_geometry(route_short_name: str) -> Tuple[List[Tuple[float, float]], List[Dict]]:
    """Fetch route geometry and order by spatial continuity using optimal starting point"""
    
    # Fetch route_shapes
    result = post_graphql(GET_ROUTE_SHAPES, {'routeShortName': route_short_name})
    if 'errors' in result:
        raise Exception(f"GraphQL errors: {result['errors']}")
    
    route_shapes = result.get('data', {}).get('routeShapes', [])
    if not route_shapes:
        raise Exception(f"No route shapes found for route {route_short_name}")
    
    shape_ids = [rs['shape_id'] for rs in route_shapes]
    
    # Fetch shape points
    result = post_graphql(GET_SHAPES_BY_IDS, {'shapeIds': shape_ids})
    if 'errors' in result:
        raise Exception(f"GraphQL errors: {result['errors']}")
    
    shape_points = result.get('data', {}).get('shapes', [])
    if not shape_points:
        raise Exception(f"No shape points found for route {route_short_name}")
    
    # Group by shape_id
    points_by_shape = {}
    for pt in shape_points:
        sid = pt['shape_id']
        if sid not in points_by_shape:
            points_by_shape[sid] = []
        points_by_shape[sid].append((
            pt['shape_pt_sequence'],
            pt['shape_pt_lon'],
            pt['shape_pt_lat']
        ))
    
    # Sort each shape by sequence
    for sid in points_by_shape:
        points_by_shape[sid].sort(key=lambda x: x[0])
    
    # Build segments
    segments = []
    for rs in route_shapes:
        sid = rs['shape_id']
        pts = points_by_shape.get(sid, [])
        if not pts:
            continue
        
        coords = [(lon, lat) for (_, lon, lat) in pts]
        segments.append({
            'shape_id': sid,
            'coords': coords,
            'start': coords[0],
            'end': coords[-1]
        })
    
    # Order by spatial continuity - try all starting points and pick best
    if not segments:
        return [], []
    
    best_ordering = None
    best_total_length = float('inf')
    
    # Try each segment as starting point
    for start_idx in range(len(segments)):
        unused = segments.copy()
        ordered = [unused.pop(start_idx)]
        
        while unused:
            current_end = ordered[-1]['end']
            best_idx = 0
            best_dist = float('inf')
            best_reversed = False
            
            for i, seg in enumerate(unused):
                dist_start = haversine(current_end, seg['start'])
                dist_end = haversine(current_end, seg['end'])
                
                if dist_start < best_dist:
                    best_dist = dist_start
                    best_idx = i
                    best_reversed = False
                if dist_end < best_dist:
                    best_dist = dist_end
                    best_idx = i
                    best_reversed = True
            
            next_seg = unused.pop(best_idx).copy()
            if best_reversed:
                next_seg['coords'] = list(reversed(next_seg['coords']))
                next_seg['start'], next_seg['end'] = next_seg['end'], next_seg['start']
                next_seg['reversed'] = True
            
            ordered.append(next_seg)
        
        # Calculate total length for this ordering
        all_coords = []
        for seg in ordered:
            all_coords.extend(seg['coords'])
        
        total_length = 0.0
        for i in range(len(all_coords) - 1):
            total_length += haversine(all_coords[i], all_coords[i + 1])
        
        # Keep the ordering with shortest total length
        if total_length < best_total_length:
            best_total_length = total_length
            best_ordering = ordered
    
    # Assemble coordinates from best ordering
    all_coords = []
    for seg in best_ordering:
        all_coords.extend(seg['coords'])
    
    return all_coords, best_ordering


def validate_geometry(route_short_name: str) -> Dict:
    """Validate route geometry and return validation report"""
    
    try:
        coords, segments = fetch_and_order_geometry(route_short_name)
    except Exception as e:
        return {
            'route_id': route_short_name,
            'valid': False,
            'errors': [str(e)],
            'warnings': [],
            'metrics': {}
        }
    
    errors = []
    warnings = []
    
    # Compute metrics
    total_length = 0.0
    for i in range(len(coords) - 1):
        total_length += haversine(coords[i], coords[i + 1])
    
    # Check seams
    seams = []
    for i in range(len(segments) - 1):
        gap = haversine(segments[i]['end'], segments[i + 1]['start'])
        seams.append(gap)
    
    max_seam = max(seams) if seams else 0
    large_seams = [s for s in seams if s > SEAM_THRESHOLD_KM]
    
    # Validation checks
    if len(coords) < MIN_POINTS:
        errors.append(f"Route has only {len(coords)} points (minimum: {MIN_POINTS})")
    
    if total_length < MIN_LENGTH_KM:
        errors.append(f"Route length {total_length:.3f} km is below minimum {MIN_LENGTH_KM} km")
    
    if large_seams:
        warnings.append(
            f"Route has {len(large_seams)} seams > {SEAM_THRESHOLD_KM} km "
            f"(max: {max_seam:.3f} km). Geometry may be fragmented."
        )
    
    reversed_count = sum(1 for s in segments if s.get('reversed', False))
    if reversed_count > 0:
        warnings.append(
            f"{reversed_count} of {len(segments)} segments were reversed for continuity"
        )
    
    metrics = {
        'total_points': len(coords),
        'total_segments': len(segments),
        'route_length_km': round(total_length, 3),
        'max_seam_km': round(max_seam, 3),
        'large_seams_count': len(large_seams),
        'reversed_segments': reversed_count
    }
    
    return {
        'route_id': route_short_name,
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'metrics': metrics
    }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate route geometry from Strapi')
    parser.add_argument('routes', nargs='+', help='Route short names to validate')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--fail-on-warnings', action='store_true', help='Exit with error code if warnings exist')
    
    args = parser.parse_args()
    
    results = []
    for route in args.routes:
        result = validate_geometry(route)
        results.append(result)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            route_id = result['route_id']
            status = '✓ PASS' if result['valid'] else '✗ FAIL'
            print(f"\n{status} Route {route_id}")
            print(f"  Points: {result['metrics'].get('total_points', 'N/A')}")
            print(f"  Length: {result['metrics'].get('route_length_km', 'N/A')} km")
            print(f"  Max seam: {result['metrics'].get('max_seam_km', 'N/A')} km")
            
            if result['errors']:
                print("  Errors:")
                for err in result['errors']:
                    print(f"    - {err}")
            
            if result['warnings']:
                print("  Warnings:")
                for warn in result['warnings']:
                    print(f"    - {warn}")
    
    # Exit code
    has_errors = any(not r['valid'] for r in results)
    has_warnings = any(r['warnings'] for r in results)
    
    if has_errors:
        sys.exit(1)
    elif args.fail_on_warnings and has_warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
