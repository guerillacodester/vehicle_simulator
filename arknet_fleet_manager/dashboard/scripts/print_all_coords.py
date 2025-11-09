#!/usr/bin/env python3
"""Print all 415 GPS coordinates for Route 1's 13.394 km journey"""

import requests
from math import radians, sin, cos, sqrt, atan2

GRAPHQL_URL = 'http://localhost:1337/graphql'

def haversine(coord1, coord2):
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371.0
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Fetch route_shapes
result = requests.post(GRAPHQL_URL, json={
    'query': 'query { routeShapes(filters: { route_id: { eq: "1" } }, pagination: { limit: 100 }) { shape_id } }'
}).json()
shape_ids = [rs['shape_id'] for rs in result['data']['routeShapes']]

# Fetch all shape points
result = requests.post(GRAPHQL_URL, json={
    'query': '''query($ids: [String!]!) { 
        shapes(filters: { shape_id: { in: $ids } }, sort: ["shape_pt_sequence:asc"], pagination: { limit: 1000 }) { 
            shape_id shape_pt_sequence shape_pt_lat shape_pt_lon 
        } 
    }''',
    'variables': {'ids': shape_ids}
}).json()

# Group by shape_id
points_by_shape = {}
for pt in result['data']['shapes']:
    sid = pt['shape_id']
    if sid not in points_by_shape:
        points_by_shape[sid] = []
    points_by_shape[sid].append((pt['shape_pt_sequence'], pt['shape_pt_lon'], pt['shape_pt_lat']))

for pts in points_by_shape.values():
    pts.sort(key=lambda x: x[0])

# Build segments
result = requests.post(GRAPHQL_URL, json={
    'query': 'query { routeShapes(filters: { route_id: { eq: "1" } }, pagination: { limit: 100 }) { shape_id } }'
}).json()

segments = []
for rs in result['data']['routeShapes']:
    sid = rs['shape_id']
    if sid not in points_by_shape:
        continue
    coords = [(lon, lat) for (_, lon, lat) in points_by_shape[sid]]
    segments.append({
        'shape_id': sid,
        'coords': coords,
        'start': coords[0],
        'end': coords[-1]
    })

# Find optimal ordering
best_ordering = None
best_total_length = float('inf')

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
        
        ordered.append(next_seg)
    
    # Calculate total length
    all_coords = []
    for seg in ordered:
        all_coords.extend(seg['coords'])
    
    total_length = 0.0
    for i in range(len(all_coords) - 1):
        total_length += haversine(all_coords[i], all_coords[i + 1])
    
    if total_length < best_total_length:
        best_total_length = total_length
        best_ordering = ordered

# Assemble all coordinates
all_coords = []
for seg in best_ordering:
    all_coords.extend(seg['coords'])

print("=" * 80)
print(f"ROUTE 1: 13.394 KM JOURNEY - ALL {len(all_coords)} GPS COORDINATES")
print("=" * 80)
print()

for i, (lon, lat) in enumerate(all_coords, 1):
    print(f"{i:3d}. ({lon:.6f}, {lat:.6f})")

print()
print("=" * 80)
print(f"Total: {len(all_coords)} coordinates, {best_total_length:.3f} km")
print("=" * 80)
