import requests
import os
from dotenv import load_dotenv

# Load .env from arknet-fleet-api
load_dotenv('arknet_fleet_manager/arknet-fleet-api/.env')

API_BASE = os.getenv('STRAPI_URL', 'http://localhost:1337')
USERNAME = os.getenv('STRAPI_USERNAME', 'vehicle_simulator')
PASSWORD = os.getenv('STRAPI_PASSWORD')

print(f"API_BASE= {API_BASE}")
print(f"USERNAME= {USERNAME}")

# Step 1: Login
response = requests.post(f"{API_BASE}/api/auth/local", json={
    "identifier": USERNAME,
    "password": PASSWORD
})
print(f"Login status: {response.status_code}")
if response.status_code == 200:
    jwt_token = response.json().get('jwt')
    headers = {'Authorization': f'Bearer {jwt_token}'}
    
    # Test vehicle endpoint
    resp = requests.get(f"{API_BASE}/api/vehicles", headers=headers)
    print(f"Vehicles status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Vehicles count: {len(resp.json().get('data', []))}")
    else:
        print(f"Vehicles response: {resp.json()}")
