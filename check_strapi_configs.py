import httpx
import json

# Try without populate
r = httpx.get("http://localhost:1337/api/operational-configurations?pagination[pageSize]=100&populate=*")
data = r.json()

print(f"\nTotal configurations in response: {len(data.get('data', []))}")
print(f"\nPagination info: {data.get('meta', {}).get('pagination', {})}")

print("\n First configuration (full):")
if data.get("data"):
    print(json.dumps(data["data"][0], indent=2))

print("\nConfigurations found:")
for config in data.get("data", []):
    attrs = config.get("attributes", {})
    section = attrs.get("section", "")
    param = attrs.get("parameter_name", "")
    value = attrs.get("value", "")
    print(f"  • {section}.{param} = {value}")
