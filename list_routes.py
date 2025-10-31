import requests
import json

r = requests.get('http://localhost:1337/api/routes?pagination[pageSize]=100&populate=*')
data = r.json()

print(f"Total routes: {len(data.get('data', []))}\n")

for route in data.get('data', []):
    route_id = route['id']
    attrs = route['attributes']
    name = attrs.get('route_long_name', 'Unknown')
    short = attrs.get('route_short_name', 'N/A')
    
    # Check for depot relations
    depot_relation = attrs.get('depot')  # Might be singular
    depots_relation = attrs.get('depots')  # Might be plural
    
    print(f"Route {route_id}: {short} - {name}")
    if depot_relation:
        print(f"  Has 'depot' relation: {depot_relation}")
    if depots_relation:
        print(f"  Has 'depots' relation: {depots_relation}")
    print()
