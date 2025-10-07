#!/usr/bin/env python3
"""
Monitor landuse zones count during file deletion test
"""

import httpx
import time

def check_landuse_count():
    """Check current landuse zone count"""
    try:
        # Check total zones in system
        response = httpx.get("http://localhost:1337/api/landuse-zones")
        if response.status_code == 200:
            total = len(response.json().get('data', []))
            
            # Check zones for country 29
            response2 = httpx.get("http://localhost:1337/api/landuse-zones?filters[country][id][$eq]=29")
            if response2.status_code == 200:
                country_zones = len(response2.json().get('data', []))
                print(f"📊 Landuse Zones - Total: {total}, Country 29: {country_zones}")
                return total, country_zones
            
        print("❌ Failed to check landuse count")
        return 0, 0
    except Exception as e:
        print(f"❌ Error checking count: {e}")
        return 0, 0

def main():
    print("🔍 Monitoring Landuse Zone Deletion Test")
    print("=" * 50)
    
    # Initial count
    print("📊 BEFORE file deletion:")
    initial_total, initial_country = check_landuse_count()
    
    print()
    print("⏳ Waiting for file deletion... (monitoring every 2 seconds)")
    print("   Delete the landuse_geojson_file in Strapi admin now!")
    print()
    
    # Monitor for changes
    last_total = initial_total
    last_country = initial_country
    
    for i in range(60):  # Monitor for 2 minutes
        time.sleep(2)
        current_total, current_country = check_landuse_count()
        
        if current_total != last_total or current_country != last_country:
            print(f"🔄 CHANGE DETECTED at {time.strftime('%H:%M:%S')}")
            print(f"   Total: {last_total} → {current_total}")
            print(f"   Country 29: {last_country} → {current_country}")
            
            if current_total == 0 and current_country == 0:
                print("✅ SUCCESS: All landuse zones deleted!")
                break
                
            last_total = current_total
            last_country = current_country
            print()
    
    print()
    print("📊 FINAL RESULT:")
    final_total, final_country = check_landuse_count()
    
    if final_total == 0 and final_country == 0:
        print("✅ File deletion successfully triggered landuse cleanup!")
        print("🎯 Lifecycle deletion logic working correctly!")
    else:
        print("⚠️  Some landuse zones remain - check lifecycle logs")

if __name__ == "__main__":
    main()