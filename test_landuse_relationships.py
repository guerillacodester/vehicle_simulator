#!/usr/bin/env python3
"""
Verify landuse zones are properly linked to countries after lifecycle fix
"""

import sys
import os
sys.path.append('commuter_service')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import httpx
import json

def test_landuse_relationships():
    """Test if landuse zones are properly linked to countries"""
    print("🔍 Testing Landuse Zone Relationships After Fix")
    print("=" * 50)
    
    # 1. Check total landuse zones in system
    response = httpx.get("http://localhost:1337/api/landuse-zones")
    if response.status_code == 200:
        total_zones = len(response.json().get('data', []))
        print(f"📊 Total landuse zones in system: {total_zones}")
    else:
        print(f"❌ Failed to get landuse zones: {response.status_code}")
        return False
    
    # 2. Test zone with populated country relationship
    response = httpx.get("http://localhost:1337/api/landuse-zones?populate=country&pagination[pageSize]=1")
    if response.status_code == 200:
        zones = response.json().get('data', [])
        if zones:
            zone = zones[0]
            country_field = zone.get('country')
            print(f"🧪 Sample zone country field: {country_field}")
            
            if country_field and country_field.get('id'):
                print(f"✅ Zone properly linked to country ID {country_field['id']}")
            else:
                print("❌ Zone NOT properly linked to country")
                return False
        else:
            print("ℹ️  No zones found to test")
    else:
        print(f"❌ Failed to get zones with country: {response.status_code}")
        return False
    
    # 3. Test country filtering (this should work now)
    response = httpx.get("http://localhost:1337/api/landuse-zones?filters[country][id][$eq]=29")
    if response.status_code == 200:
        filtered_zones = len(response.json().get('data', []))
        print(f"🎯 Landuse zones filtered by country 29: {filtered_zones}")
        
        if filtered_zones > 0:
            print("✅ Country filtering is working!")
            return True
        else:
            print("⚠️  Country filtering returns 0 results")
            return False
    else:
        print(f"❌ Country filtering failed: {response.status_code}")
        return False

def main():
    success = test_landuse_relationships()
    if success:
        print("\n🎉 All relationship tests passed!")
        print("🚀 Landuse zones are properly linked to countries!")
    else:
        print("\n❌ Relationship tests failed")
        print("💡 You may need to trigger re-import in Strapi admin")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)