import requests
import json

# Test what Strapi returns for Route 1
url = "http://localhost:1337/api/routes/gg3pv3z19hhm117v9xth5ezq?populate=*"
response = requests.get(url)

print(f"Status: {response.status_code}")
print("\nFull Response:")
print(json.dumps(response.json(), indent=2))

# Check where depot is
data = response.json()
print("\n\n=== CHECKING DEPOT LOCATION ===")
print(f"data.get('data'): {type(data.get('data'))}")
print(f"data['data'].keys(): {data.get('data', {}).keys()}")

route_data = data.get('data', {})
print(f"\nChecking data.depot: {route_data.get('depot')}")

attrs = route_data.get('attributes', {})
print(f"Checking data.attributes.depot: {attrs.get('depot')}")
print(f"\nAll attributes keys: {attrs.keys()}")
