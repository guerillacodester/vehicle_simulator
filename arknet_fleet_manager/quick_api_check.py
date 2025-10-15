import requests

url = "http://localhost:1337/api/operational-configurations"
params = {"pagination[pageSize]": 100}

r = requests.get(url, params=params)
print(f"Status: {r.status_code}")
data = r.json()
print(f"Count: {len(data.get('data', []))}")
print(f"First item: {data.get('data', [{}])[0] if data.get('data') else 'None'}")
