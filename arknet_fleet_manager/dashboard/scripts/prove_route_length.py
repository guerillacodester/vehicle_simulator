#!/usr/bin/env python3
"""
Prove route length calculation by showing all data from GraphQL and computing length step-by-step
"""

import requests
import json
from math import radians, sin, cos, sqrt, atan2

GRAPHQL_URL = 'http://localhost:1337/graphql'

GET_ROUTE_SHAPES = """
query GetRouteShapes($routeShortName: String!) {
  routeShapes(
    filters: { route_id: { eq: $routeShortName } }
    pagination: { limit: 100 }
  ) {
    documentId
    route_id
    shape_id
  }
}
"""

GET_SHAPES_BY_IDS = """
query GetShapesByIds($shapeIds: [String!]!) {
  shapes(
    filters: { shape_id: { in: $shapeIds } }
    sort: ["shape_pt_sequence:asc"]
    pagination: { limit: 1000 }
  ) {
    shape_id
    shape_pt_sequence
    shape_pt_lat
    shape_pt_lon
  }
}
"""

def post_graphql(query: str, variables: dict) -> dict:
    """Execute GraphQL query"""
    response = requests.post(
        GRAPHQL_URL,
        json={'query': query, 'variables': variables},
        headers={'Content-Type': 'application/json'}
    )
    response.raise_for_status()
    return response.json()

def haversine(coord1, coord2):
    """Calculate great-circle distance between two points in kilometers"""
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    
    R = 6371.0  # Earth radius in kilometers
    
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c

def main():
    route_short_name = "1"
    
    print("=" * 80)
    print(f"PROVING ROUTE LENGTH FOR ROUTE {route_short_name} FROM GRAPHQL")
    print("=" * 80)
    print()
    
    # Step 1: Fetch route_shapes
    print("STEP 1: Fetching route_shapes from GraphQL...")
    print(f"Query: {GET_ROUTE_SHAPES}")
    print(f"Variables: {{'routeShortName': '{route_short_name}'}}")
    print()
    
    result = post_graphql(GET_ROUTE_SHAPES, {'routeShortName': route_short_name})
    route_shapes = result.get('data', {}).get('routeShapes', [])
    
    print(f"Found {len(route_shapes)} route_shapes:")
    for i, rs in enumerate(route_shapes, 1):
        print(f"  {i}. shape_id={rs['shape_id']}, route_id={rs['route_id']}")
    print()
    
    # Step 2: Fetch shape points
    shape_ids = [rs['shape_id'] for rs in route_shapes]
    print("STEP 2: Fetching shape points from GraphQL...")
    print(f"Query: {GET_SHAPES_BY_IDS}")
    print(f"Variables: shape_ids count={len(shape_ids)}")
    print()
    
    result = post_graphql(GET_SHAPES_BY_IDS, {'shapeIds': shape_ids})
    shape_points = result.get('data', {}).get('shapes', [])
    
    print(f"Found {len(shape_points)} total shape points")
    print()
    
    # Step 3: Group by shape_id
    print("STEP 3: Grouping points by shape_id and sorting by sequence...")
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
    
    for sid in points_by_shape:
        points_by_shape[sid].sort(key=lambda x: x[0])
    
    for sid, pts in points_by_shape.items():
        print(f"  {sid}: {len(pts)} points (seq {pts[0][0]} to {pts[-1][0]})")
    print()
    
    # Step 4: Build segments
    print("STEP 4: Building segments...")
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
            'end': coords[-1],
            'point_count': len(coords)
        })
    
    for i, seg in enumerate(segments, 1):
        print(f"  Segment {i}: {seg['shape_id']}")
        print(f"    Points: {seg['point_count']}")
        print(f"    Start: ({seg['start'][0]:.6f}, {seg['start'][1]:.6f})")
        print(f"    End: ({seg['end'][0]:.6f}, {seg['end'][1]:.6f})")
    print()
    
    # Step 5: Find optimal ordering
    print("STEP 5: Finding optimal segment ordering (trying all starting points)...")
    best_ordering = None
    best_total_length = float('inf')
    best_start_idx = -1
    
    for start_idx in range(len(segments)):
        unused = [seg.copy() for seg in segments]
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
        
        # Calculate total length
        all_coords = []
        for seg in ordered:
            all_coords.extend(seg['coords'])
        
        total_length = 0.0
        for i in range(len(all_coords) - 1):
            total_length += haversine(all_coords[i], all_coords[i + 1])
        
        print(f"  Starting from segment {start_idx + 1}: total length = {total_length:.3f} km")
        
        if total_length < best_total_length:
            best_total_length = total_length
            best_ordering = ordered
            best_start_idx = start_idx
    
    print()
    print(f"Best ordering found starting from segment {best_start_idx + 1}")
    print()
    
    # Step 6: Show optimal ordering
    print("STEP 6: Optimal segment ordering:")
    for i, seg in enumerate(best_ordering, 1):
        reversed_marker = " [REVERSED]" if seg.get('reversed') else ""
        print(f"  {i}. {seg['shape_id']} ({seg['point_count']} points){reversed_marker}")
    print()
    
    # Step 7: Assemble all coordinates
    print("STEP 7: Assembling all coordinates in optimal order...")
    all_coords = []
    for seg in best_ordering:
        all_coords.extend(seg['coords'])
    
    print(f"Total coordinates: {len(all_coords)}")
    print()
    
    # Step 8: Display first 10 and last 10 coordinates
    print("STEP 8: Showing coordinates (first 10 and last 10)...")
    print()
    print("First 10 coordinates:")
    for i, (lon, lat) in enumerate(all_coords[:10], 1):
        print(f"  {i}. ({lon:.6f}, {lat:.6f})")
    
    print()
    print(f"... ({len(all_coords) - 20} coordinates omitted) ...")
    print()
    
    print("Last 10 coordinates:")
    for i, (lon, lat) in enumerate(all_coords[-10:], len(all_coords) - 9):
        print(f"  {i}. ({lon:.6f}, {lat:.6f})")
    print()
    
    # Step 9: Calculate distance step by step (sample)
    print("STEP 9: Calculating distance between consecutive points (showing first 10 segments)...")
    cumulative = 0.0
    for i in range(min(10, len(all_coords) - 1)):
        dist = haversine(all_coords[i], all_coords[i + 1])
        cumulative += dist
        print(f"  Point {i+1} to {i+2}: {dist*1000:.2f} meters (cumulative: {cumulative:.6f} km)")
    print()
    
    # Step 10: Calculate total length
    print("STEP 10: Calculating TOTAL route length...")
    total_length = 0.0
    for i in range(len(all_coords) - 1):
        dist = haversine(all_coords[i], all_coords[i + 1])
        total_length += dist
    
    print()
    print("=" * 80)
    print(f"FINAL RESULT: Route {route_short_name} total length = {total_length:.3f} km")
    print(f"  - {len(all_coords)} total GPS coordinates")
    print(f"  - {len(best_ordering)} segments assembled")
    print(f"  - {sum(1 for s in best_ordering if s.get('reversed'))} segments reversed")
    print("=" * 80)
    print()
    print("All data pulled from GraphQL at http://localhost:1337/graphql")
    print("No cheating! ✓")

if __name__ == '__main__':
    main()
