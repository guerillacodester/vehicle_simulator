import httpx
import json
r = httpx.get('http://localhost:1337/api/routes?filters[is_active][$eq]=true&pagination[pageSize]=100')
routes = r.json()['data']
print(f'Routes found: {len(routes)}')
print("\nRoute details:")
print(json.dumps(routes[0], indent=2))
