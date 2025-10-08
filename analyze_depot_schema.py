"""
DEPOT SCHEMA ANALYZER
====================
Analyzes current depot schema structure and prepares for migration.
"""

import requests
import json
import sys
from typing import Dict, Any, List

def analyze_depot_schema():
    """Analyze current depot schema and data structure."""
    base_url = "http://localhost:1337/api"
    headers = {"Content-Type": "application/json"}
    
    try:
        print("🔍 Analyzing current depot schema...")
        
        # Test API connectivity
        response = requests.get(f"{base_url}/depots", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Cannot access depot API: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        depots = data.get('data', [])
        
        print(f"📊 Found {len(depots)} existing depots")
        
        if depots:
            # Analyze first depot structure
            first_depot = depots[0]
            attrs = first_depot.get('attributes', {})
            
            print(f"\n📋 Current depot schema structure:")
            print(f"Depot ID: {first_depot.get('id')}")
            print(f"Available fields: {list(attrs.keys())}")
            
            # Check for coordinate fields
            has_latitude = 'latitude' in attrs
            has_longitude = 'longitude' in attrs  
            has_location = 'location' in attrs
            
            print(f"\n🗺️  Coordinate field analysis:")
            print(f"✅ latitude field: {'EXISTS' if has_latitude else 'MISSING'}")
            print(f"✅ longitude field: {'EXISTS' if has_longitude else 'MISSING'}")
            print(f"⚠️  location field: {'EXISTS (should be removed)' if has_location else 'REMOVED'}")
            
            if has_location:
                location_data = attrs.get('location')
                print(f"Location data structure: {type(location_data)} = {location_data}")
            
            if has_latitude and has_longitude:
                lat_val = attrs.get('latitude')
                lon_val = attrs.get('longitude')
                print(f"📍 Coordinates: latitude={lat_val}, longitude={lon_val}")
                
                # Validate Barbados bounds
                if lat_val and lon_val:
                    valid_lat = 13.0 <= lat_val <= 13.35
                    valid_lon = -59.65 <= lon_val <= -59.4
                    
                    print(f"✅ Latitude in Barbados bounds (13.0-13.35): {'YES' if valid_lat else 'NO'}")
                    print(f"✅ Longitude in Barbados bounds (-59.65 to -59.4): {'YES' if valid_lon else 'NO'}")
            
            # Show full depot structure for analysis
            print(f"\n📄 Full depot structure sample:")
            print(json.dumps(first_depot, indent=2))
            
        else:
            print("ℹ️  No existing depots found - clean slate for new schema")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing depot schema: {e}")
        return False

if __name__ == "__main__":
    success = analyze_depot_schema()
    sys.exit(0 if success else 1)