#!/usr/bin/env python3
"""
Analyze remaining GeoJSON files to understand their structure
"""

import json
import os

def analyze_geojson_file(filename):
    """Analyze a GeoJSON file and return structure info"""
    filepath = f"commuter_service/geojson_data/{filename}"
    
    print(f"📁 {filename}")
    print("=" * 50)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        features = data.get('features', [])
        print(f"   🔢 Total features: {len(features)}")
        
        if features:
            sample = features[0]
            props = sample.get('properties', {})
            geometry = sample.get('geometry', {})
            
            print(f"   🗺️  Geometry type: {geometry.get('type', 'Unknown')}")
            print(f"   🏷️  Property keys: {list(props.keys())[:10]}")
            
            if props:
                print("   📋 Sample properties:")
                for key, value in list(props.items())[:5]:
                    val_str = str(value)
                    display_val = val_str[:60] + "..." if len(val_str) > 60 else val_str
                    print(f"      {key}: {display_val}")
        
        print()
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading {filename}: {e}")
        print()
        return False

def main():
    """Analyze all remaining GeoJSON files"""
    print("🔍 Analyzing Remaining GeoJSON Files")
    print("=" * 60)
    print()
    
    files_to_check = ['barbados_names.json', 'barbados_busstops.json', 'barbados_highway.json']
    
    for filename in files_to_check:
        analyze_geojson_file(filename)

if __name__ == "__main__":
    main()