import requests
import json

try:
    print("🔍 Testing /fleet/countries endpoint...")
    response = requests.get("http://localhost:8000/fleet/countries")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
