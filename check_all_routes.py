import requests

r = requests.get('http://localhost:1337/api/routes')
routes = r.json()['data']

print(f'Total routes: {len(routes)}\n')
for rt in routes:
    has_geojson = "YES" if rt.get('geojson_data') else "NO"
    print(f"Route {rt['short_name']:3s}: {rt.get('long_name', 'N/A'):30s} geojson: {has_geojson}")
