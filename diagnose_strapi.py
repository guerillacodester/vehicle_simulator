"""
Quick diagnostic to check Strapi content types
"""
import requests

STRAPI_URL = "http://localhost:1337"

print("🔍 Checking Strapi content types...")
print(f"   URL: {STRAPI_URL}")

# Try to access the content type without auth
response = requests.get(f"{STRAPI_URL}/api/operational-configurations")
print(f"\n📊 GET /api/operational-configurations")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:200]}")

# Check if it's a permissions issue (403) vs not found (404)
if response.status_code == 404:
    print("\n❌ 404 = Content type not loaded OR wrong API path")
    print("\nPossible causes:")
    print("1. Strapi didn't restart properly")
    print("2. Schema has syntax errors")
    print("3. API route not registered")
    
    # Try alternate API paths
    print("\n🔍 Trying alternate paths...")
    
    paths = [
        "/api/operational-configuration",  # Singular
        "/content-manager/collection-types/api::operational-configuration.operational-configuration",
    ]
    
    for path in paths:
        try:
            r = requests.get(f"{STRAPI_URL}{path}", timeout=2)
            print(f"   {path}: {r.status_code}")
        except Exception as e:
            print(f"   {path}: Error - {e}")

elif response.status_code == 403:
    print("\n⚠️  403 = Content type exists but permissions not enabled")
    print("\nTo fix:")
    print("1. Go to: http://localhost:1337/admin")
    print("2. Settings → Roles → Public")
    print("3. Scroll to 'Operational-configuration'")
    print("4. Enable: find, findOne, create, update")
    print("5. Save")

elif response.status_code == 200:
    print("\n✅ Content type is accessible!")
    data = response.json()
    print(f"   Data: {data}")

else:
    print(f"\n❓ Unexpected status: {response.status_code}")
