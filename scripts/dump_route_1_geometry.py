import re
import json

path = r"e:\projects\github\vehicle_simulator\arknet_transit_simulator\data\route_1_db_points.txt"
coords = []
float_re = re.compile(r"(-?\d+\.\d+)")
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split('|')
        if len(parts) >= 3:
            lat_str = parts[1].strip()
            lon_str = parts[2].strip()
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                coords.append([lon, lat])
            except ValueError:
                continue

geojson = {
    "type": "Feature",
    "properties": {"source": "route_1_db_points.txt"},
    "geometry": {
        "type": "LineString",
        "coordinates": coords
    }
}

print(json.dumps(geojson, indent=2))
print('\n# Points:', len(coords))
if coords:
    print('# First:', coords[0])
    print('# Last: ', coords[-1])
