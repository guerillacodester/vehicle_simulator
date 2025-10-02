"""
Check Depot GPS Coordinates
===========================

Verify if depots have proper GPS coordinates and identify missing location data.
"""

import asyncio
import logging
from commuter_service.strapi_api_client import StrapiApiClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def check_depot_coordinates():
    """Check depot GPS coordinates in Strapi"""
    print("🗺️  CHECKING DEPOT GPS COORDINATES")
    print("=" * 50)
    
    api_client = StrapiApiClient()
    
    try:
        await api_client.connect()
        depots = await api_client.get_all_depots()
        
        print(f"Found {len(depots)} depots:")
        print()
        
        depots_with_location = 0
        depots_without_location = 0
        
        for depot in depots:
            print(f"🏢 Depot: {depot.name}")
            print(f"   ID: {depot.depot_id}")
            print(f"   Capacity: {depot.capacity}")
            print(f"   Active: {depot.is_active}")
            
            if depot.location:
                print(f"   ✅ Location: {depot.location}")
                if 'lat' in depot.location and 'lon' in depot.location:
                    lat, lon = depot.location['lat'], depot.location['lon']
                    print(f"   📍 GPS: {lat:.6f}, {lon:.6f}")
                    depots_with_location += 1
                else:
                    print(f"   ❌ Location format invalid: {depot.location}")
                    depots_without_location += 1
            else:
                print(f"   ❌ No location data")
                depots_without_location += 1
            
            print()
        
        print(f"📊 SUMMARY:")
        print(f"   Depots with GPS: {depots_with_location}")
        print(f"   Depots without GPS: {depots_without_location}")
        
        if depots_without_location > 0:
            print(f"\n⚠️  ISSUE: {depots_without_location} depots missing GPS coordinates!")
            print(f"   This will break realistic commuter spawning.")
            print(f"   Need to add proper lat/lon coordinates to depot database.")
            
            # Suggest realistic coordinates for Barbados depots
            print(f"\n💡 SUGGESTED GPS COORDINATES (Barbados):")
            print(f"   Bridgetown Main Depot: 13.0969° N, 59.6168° W")
            print(f"   Speightstown Depot: 13.2416° N, 59.6367° W") 
            print(f"   Oistins Depot: 13.0735° N, 59.5343° W")
            print(f"   Airport Depot: 13.0707° N, 59.4925° W")
        else:
            print(f"\n✅ All depots have GPS coordinates!")
        
    except Exception as e:
        print(f"❌ Error checking depot coordinates: {e}")
    
    finally:
        await api_client.close()

if __name__ == "__main__":
    asyncio.run(check_depot_coordinates())