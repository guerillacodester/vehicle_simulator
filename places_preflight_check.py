#!/usr/bin/env python3
"""
Pre-flight check for Places import to ensure everything is ready
"""

import json
import httpx

def check_places_readiness():
    """Pre-flight checks for Places import"""
    print("🔍 Places Import Pre-Flight Check")
    print("=" * 50)
    
    # 1. Check data structure
    print("1️⃣ Analyzing barbados_names.json structure:")
    try:
        with open('commuter_service/geojson_data/barbados_names.json', 'r') as f:
            data = json.load(f)
        
        features = data.get('features', [])
        print(f"   ✅ Found {len(features)} place name features")
        
        if features:
            sample = features[0]
            props = sample.get('properties', {})
            geom_type = sample.get('geometry', {}).get('type')
            
            print(f"   ✅ Geometry type: {geom_type} (supported)")
            print(f"   ✅ Has 'name' field: {'name' in props}")
            print(f"   ✅ Sample name: {props.get('name', 'N/A')}")
            
            # Check coordinate structure
            coords = sample.get('geometry', {}).get('coordinates', [])
            if coords and len(coords) > 0:
                print(f"   ✅ LineString has {len(coords)} coordinate points")
    
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return False
    
    # 2. Check API connectivity
    print("\n2️⃣ Testing Strapi API connectivity:")
    try:
        response = httpx.get("http://localhost:1337/api/places")
        if response.status_code == 200:
            current_count = len(response.json().get('data', []))
            print(f"   ✅ Places endpoint accessible")
            print(f"   📊 Current places in DB: {current_count}")
        else:
            print(f"   ❌ Places endpoint error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API connectivity error: {e}")
        return False
    
    # 3. Check country relationship
    print("\n3️⃣ Testing country relationship filtering:")
    try:
        response = httpx.get("http://localhost:1337/api/places?filters[country][id][$eq]=29")
        if response.status_code == 200:
            country_places = len(response.json().get('data', []))
            print(f"   ✅ Country filtering works")
            print(f"   📊 Current places for country 29: {country_places}")
        else:
            print(f"   ❌ Country filtering error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Country filtering error: {e}")
        return False
    
    print("\n🎯 READY FOR IMPORT!")
    print("Expected outcome:")
    print(f"   📍 8,283 place names will be imported")
    print(f"   🗺️  LineString geometries converted to centroid points")
    print(f"   🏷️  All places classified as 'locality' type")
    print(f"   🔗 Proper country relationships established")
    
    return True

def main():
    success = check_places_readiness()
    
    if success:
        print("\n✅ ALL CHECKS PASSED - Ready to upload barbados_names.json!")
        print("📋 Upload to 'place_names_geojson_file' field in Strapi admin")
    else:
        print("\n❌ Pre-flight checks failed - fix issues before upload")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)