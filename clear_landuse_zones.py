#!/usr/bin/env python3
"""
Clear all existing landuse zones that weren't properly linked to countries
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

sys.path.append('commuter_service')
from strapi_api_client import StrapiApiClient

def main():
    """Clear all landuse zones"""
    print("🧹 Clearing existing unlinked landuse zones...")
    
    # Initialize API client
    client = StrapiApiClient()
    
    try:
        # Get all landuse zones directly (not filtered by country)
        response = client.get('landuse-zones', params={'pagination[pageSize]': 5000})
        
        if response.status_code == 200:
            data = response.json()
            zones = data.get('data', [])
            print(f"Found {len(zones)} zones to delete")
            
            for zone in zones:
                zone_id = zone['id']
                delete_response = client.delete(f'landuse-zones/{zone_id}')
                if delete_response.status_code == 200:
                    print(f"✅ Deleted zone {zone_id}")
                else:
                    print(f"❌ Failed to delete zone {zone_id}: {delete_response.status_code}")
            
            print("🎯 Ready for clean re-import with fixed relationships!")
        else:
            print(f"❌ Failed to get landuse zones: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error clearing landuse zones: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)