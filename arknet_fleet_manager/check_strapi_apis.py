"""
Check what content types Strapi actually has loaded
"""
import requests
import json

STRAPI_URL = "http://localhost:1337"

def check_content_types():
    """Check if we can introspect Strapi's content types"""
    
    # Try to get the GraphQL schema which lists all types
    try:
        response = requests.post(
            f"{STRAPI_URL}/graphql",
            json={
                "query": """
                {
                  __schema {
                    types {
                      name
                      kind
                    }
                  }
                }
                """
            }
        )
        print(f"GraphQL Schema Query: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            types = [t['name'] for t in data['data']['__schema']['types'] 
                    if not t['name'].startswith('__')]
            print(f"\nFound {len(types)} types:")
            for t in sorted(types):
                if 'operational' in t.lower() or 'config' in t.lower():
                    print(f"  ⭐ {t}")
                elif t[0].isupper() and not t.startswith('Upload'):
                    print(f"  - {t}")
    except Exception as e:
        print(f"GraphQL check failed: {e}")
    
    # Try some common API endpoints
    print("\n" + "="*80)
    print("Testing API Endpoints:")
    print("="*80)
    
    test_endpoints = [
        "/api/operational-configurations",
        "/api/operational-configuration", 
        "/content-type-builder/content-types",
        "/content-manager/content-types",
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(f"{STRAPI_URL}{endpoint}")
            print(f"{endpoint:50} -> {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
        except Exception as e:
            print(f"{endpoint:50} -> Error: {e}")

if __name__ == "__main__":
    check_content_types()
