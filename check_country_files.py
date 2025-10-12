import requests
import json

token = "b127418caf99e995d561f1c787005e328c8b9168e7fcc313460e43e032259a2b26d209b260b1dd8c0ca5dced2f20db90823984a50e2ec7429070552acad2b81f94bcad87ddf09e3314ded62538163e55e7f11a8909de45f67dd95890311211f5c1af76b86452a9e4f585ea9e4d3832e434c6cb46b97823c103801323a0214442"

r = requests.get(
    'http://localhost:1337/api/countries/y5qsd8a1it9bfxmlpg6gvt4c?populate=*',
    headers={'Authorization': f'Bearer {token}'}
)

print(f"Status: {r.status_code}")
print(f"Response: {json.dumps(r.json(), indent=2)[:1000]}")

if r.status_code == 200:
    data = r.json().get('data')
    if data:
        print(f"\nPOI file: {data.get('pois_geojson_file')}")
        print(f"Landuse file: {data.get('landuse_geojson_file')}")
        print(f"Regions file: {data.get('regions_geojson_file')}")
        print(f"Highways file: {data.get('highways_geojson_file')}")
