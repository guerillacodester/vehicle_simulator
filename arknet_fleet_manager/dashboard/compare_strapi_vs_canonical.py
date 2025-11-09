import json
import math
from pathlib import Path

# Haversine formula
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371.0088
    return c * r


def parse_coord(pt):
    lon = float(pt[0])
    lat = float(pt[1])
    return lon, lat


def sort_layer_key(layer_str):
    try:
        parts = layer_str.split('_')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return (major, minor)
    except Exception:
        return (9999, 9999)


def concat_features_points(features):
    features_sorted = sorted(features, key=lambda ft: sort_layer_key(ft.get('properties', {}).get('layer', '')))
    pts = []
    for ft in features_sorted:
        coords = ft['geometry']['coordinates']
        for pt in coords:
            lon, lat = parse_coord(pt)
            if not pts or (abs(pts[-1][0]-lon) > 1e-9 or abs(pts[-1][1]-lat) > 1e-9):
                pts.append((lon, lat))
    return pts


def load_strapi(path):
    payload = json.load(open(path, 'r', encoding='utf-8'))
    features = payload['data']['routes'][0]['geojson_data']['features']
    pts = concat_features_points(features)
    return pts


def load_canonical(path):
    payload = json.load(open(path, 'r', encoding='utf-8'))
    features = payload['features']
    pts = concat_features_points(features)
    return pts


STRAPI_PATH = Path('temp_route1.json')
CANON_PATH = Path('../../arknet_transit_simulator/data/route_1.geojson')
# Adjust canonical path relative to this script location
CANON_PATH = (Path(__file__).parent / '..' / '..' / 'arknet_transit_simulator' / 'data' / 'route_1.geojson').resolve()

strapi_pts = load_strapi(STRAPI_PATH)
canon_pts = load_canonical(CANON_PATH)

print(f"Strapi points: {len(strapi_pts)}")
print(f"Canonical points: {len(canon_pts)}")

# compute lengths
def route_length_km(pts):
    s = 0.0
    for i in range(1, len(pts)):
        s += haversine(pts[i-1][0], pts[i-1][1], pts[i][0], pts[i][1])
    return s

strapi_len = route_length_km(strapi_pts)
canon_len = route_length_km(canon_pts)
print(f"Strapi route length: {strapi_len:.6f} km")
print(f"Canonical route length: {canon_len:.6f} km")

# For each canonical point, find nearest strapi point distance
from math import inf

threshold_m = 10.0  # 10 meters threshold
unmatched_indices = []
for idx, cpt in enumerate(canon_pts):
    best_m = inf
    for spt in strapi_pts:
        km = haversine(cpt[0], cpt[1], spt[0], spt[1])
        m = km * 1000.0
        if m < best_m:
            best_m = m
    if best_m > threshold_m:
        unmatched_indices.append((idx, best_m))

print(f"Canonical points unmatched (>{threshold_m} m): {len(unmatched_indices)}")

# Group unmatched into consecutive ranges and compute missing distance along canonical between those ranges
ranges = []
if unmatched_indices:
    start_idx = unmatched_indices[0][0]
    last_idx = start_idx
    for idx, dist in unmatched_indices[1:]:
        if idx == last_idx + 1:
            last_idx = idx
        else:
            ranges.append((start_idx, last_idx))
            start_idx = idx
            last_idx = idx
    ranges.append((start_idx, last_idx))

# compute distance missing for each range
missing_total_km = 0.0
range_details = []
for a,b in ranges:
    km = 0.0
    # sum distances between a..b along canonical
    for i in range(a+1, b+1):
        km += haversine(canon_pts[i-1][0], canon_pts[i-1][1], canon_pts[i][0], canon_pts[i][1])
    missing_total_km += km
    range_details.append({'start_idx':a, 'end_idx':b, 'missing_km':km})

print("Missing ranges on canonical route (by index) and approximate length in km:")
for r in range_details:
    print(f" - {r['start_idx']}..{r['end_idx']}: {r['missing_km']:.6f} km")

print(f"Total missing canonical distance (approx): {missing_total_km:.6f} km")

# Also report overall gap between canonical length and strapi length
gap_km = canon_len - strapi_len
print(f"Canonical - Strapi length difference: {gap_km:.6f} km")

# Save a small JSON report
report = {
    'strapi_points': len(strapi_pts),
    'canonical_points': len(canon_pts),
    'strapi_length_km': strapi_len,
    'canonical_length_km': canon_len,
    'missing_total_km': missing_total_km,
    'canonical_minus_strapi_km': gap_km,
    'unmatched_point_count': len(unmatched_indices),
    'unmatched_ranges': range_details
}

with open('compare_report.json', 'w', encoding='utf-8') as rf:
    json.dump(report, rf, indent=2)

print('\nWrote compare_report.json')
