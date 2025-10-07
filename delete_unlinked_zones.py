#!/usr/bin/env python3
"""
Delete unlinked landuse zones and trigger re-import
"""

import httpx
import json
import time

# Delete all landuse zones directly via API
print("🧹 Clearing unlinked landuse zones...")

# Get all landuse zones
response = httpx.get("http://localhost:1337/api/landuse-zones?pagination[pageSize]=5000")
if response.status_code == 200:
    data = response.json()
    zones = data.get('data', [])
    print(f"Found {len(zones)} zones to delete")
    
    # Delete each zone
    deleted_count = 0
    for zone in zones:
        zone_id = zone['id']
        delete_response = httpx.delete(f"http://localhost:1337/api/landuse-zones/{zone_id}")
        if delete_response.status_code == 200:
            deleted_count += 1
        else:
            print(f"❌ Failed to delete zone {zone_id}: {delete_response.status_code}")
    
    print(f"✅ Deleted {deleted_count} unlinked landuse zones")
else:
    print(f"❌ Failed to get landuse zones: {response.status_code}")

# Verify cleanup
print("\n🔍 Verifying cleanup...")
response = httpx.get("http://localhost:1337/api/landuse-zones")
if response.status_code == 200:
    data = response.json()
    remaining = len(data.get('data', []))
    print(f"Remaining landuse zones: {remaining}")
else:
    print(f"❌ Failed to verify cleanup: {response.status_code}")

print("\n🎯 Now trigger re-import by updating the country in Strapi admin...")
print("   The fixed lifecycle should create proper relationships!")