"""
Delete all operational configuration entries to reseed with new schema
"""
import requests
import json

STRAPI_URL = "http://localhost:1337"

# Get all entries
response = requests.get(f"{STRAPI_URL}/api/operational-configurations?pagination[pageSize]=100")
data = response.json()
entries = data.get("data", [])

print(f"Found {len(entries)} entries to delete")

# Delete each entry
for entry in entries:
    doc_id = entry.get("documentId")
    if doc_id:
        delete_response = requests.delete(f"{STRAPI_URL}/api/operational-configurations/{doc_id}")
        if delete_response.status_code in [200, 204]:
            print(f"✅ Deleted: {entry.get('section')}.{entry.get('parameter')}")
        else:
            print(f"❌ Failed to delete: {doc_id} - Status: {delete_response.status_code}")

print(f"\n🎉 Deleted {len(entries)} entries")
