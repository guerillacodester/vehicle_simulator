import requests

STRAPI_URL = "http://localhost:1337"

# Speightstown documentId
depot_doc_id = "ft3t8jc5jnzg461uod6to898"

print("=" * 80)
print("TESTING DEPOT ROUTE QUERY (Current Implementation)")
print("=" * 80)

# Current query (what the spawner uses)
url = (
    f"{STRAPI_URL}/api/route-depots?"
    f"filters[depot][documentId][$eq]={depot_doc_id}&"
    f"fields[0]=route_short_name&"
    f"fields[1]=distance_from_route_m&"
    f"fields[2]=is_start_terminus&"
    f"fields[3]=is_end_terminus&"
    f"pagination[pageSize]=100"
)

print(f"\nQuery URL: {url}\n")

response = requests.get(url)
data = response.json()

print("Response:")
import json
print(json.dumps(data, indent=2))

print("\n" + "=" * 80)
print("TESTING WITH POPULATE (Correct Implementation)")
print("=" * 80)

# Correct query with populate
url2 = (
    f"{STRAPI_URL}/api/route-depots?"
    f"filters[depot][documentId][$eq]={depot_doc_id}&"
    f"populate=route&"
    f"pagination[pageSize]=100"
)

print(f"\nQuery URL: {url2}\n")

response2 = requests.get(url2)
data2 = response2.json()

print("Response:")
print(json.dumps(data2, indent=2))

print("\n" + "=" * 80)
print("EXTRACTING ROUTE INFO")
print("=" * 80)

for assoc in data2.get('data', []):
    route = assoc.get('route')
    if route:
        print(f"✅ Found route: {route.get('route_short_name')} (documentId: {route.get('documentId')})")
        print(f"   Distance: {assoc.get('distance_from_route_m')}m")
        print(f"   Start terminus: {assoc.get('is_start_terminus')}")
        print(f"   End terminus: {assoc.get('is_end_terminus')}")
