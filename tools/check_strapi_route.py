import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env from arknet-fleet-api directory
env_path = Path(__file__).parent.parent / 'arknet_fleet_manager' / 'arknet-fleet-api' / '.env'
load_dotenv(env_path)

API_BASE = os.getenv('STRAPI_URL', 'http://localhost:1337')
USERNAME = os.getenv('STRAPI_USERNAME')
PASSWORD = os.getenv('STRAPI_PASSWORD')

print('API_BASE=', API_BASE)
print('USERNAME=', USERNAME)

# Login to Strapi
r = requests.post(f"{API_BASE}/api/auth/local", json={"identifier": USERNAME, "password": PASSWORD})
print('Login status:', r.status_code)
print('Login response:', r.text)
if r.status_code != 200:
    raise SystemExit('Strapi login failed')

jwt = r.json().get('jwt')
headers = {'Authorization': f'Bearer {jwt}'}

# Try to fetch route geometry
resp = requests.get(f"{API_BASE}/api/routes/1/geometry", headers=headers)
print('Geometry status:', resp.status_code)
print('Geometry response:', resp.text)

# Also try with no auth
resp2 = requests.get(f"{API_BASE}/api/routes/1/geometry")
print('No-auth geometry status:', resp2.status_code)
print('No-auth geometry response:', resp2.text)

# Also try listing routes
resp3 = requests.get(f"{API_BASE}/api/routes", headers=headers)
print('Routes list status:', resp3.status_code)
print('Routes list response:', resp3.text)
