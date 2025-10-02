"""
Depot GPS Coordinates Migration
==============================

Add realistic GPS coordinates to depot records in Strapi database.
This is CRITICAL for the commuter reservoir system to work properly.
"""

import asyncio
import logging
import httpx
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Realistic GPS coordinates for Barbados depots
DEPOT_GPS_COORDINATES = {
    # Main depots in key locations
    "bridgetown": {
        "lat": 13.0969,
        "lon": -59.6168,
        "description": "Bridgetown Main Terminal - Central business district"
    },
    "test-depot": {
        "lat": 13.1134,  # Bridgetown suburbs
        "lon": -59.6237,
        "description": "Test depot in Bridgetown area"
    },
    # Additional realistic depot locations for future use
    "speightstown": {
        "lat": 13.2416,
        "lon": -59.6367,
        "description": "Speightstown North Terminal"
    },
    "oistins": {
        "lat": 13.0735,
        "lon": -59.5343,
        "description": "Oistins South Coast Terminal"
    },
    "airport": {
        "lat": 13.0707,
        "lon": -59.4925,
        "description": "Grantley Adams Airport Terminal"
    }
}

async def update_depot_coordinates():
    """Update depot coordinates in Strapi"""
    print("🗺️  UPDATING DEPOT GPS COORDINATES")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            # Get current depots
            response = await client.get("http://localhost:1337/api/depots")
            response.raise_for_status()
            depots_data = response.json()
            
            print(f"Found {len(depots_data['data'])} depots to update:")
            
            for depot in depots_data['data']:
                depot_id = depot['depot_id']
                depot_name = depot['name']
                document_id = depot['documentId']  # Use documentId for Strapi v5
                
                print(f"\n🏢 Processing: {depot_name} (ID: {depot_id})")
                
                # Determine coordinates based on depot ID/name
                coordinates = None
                
                if "bridgetown" in depot_id.lower() or "bridgetown" in depot_name.lower():
                    coordinates = DEPOT_GPS_COORDINATES["bridgetown"]
                elif "test" in depot_id.lower():
                    coordinates = DEPOT_GPS_COORDINATES["test-depot"]
                elif "speightstown" in depot_name.lower():
                    coordinates = DEPOT_GPS_COORDINATES["speightstown"]
                elif "oistins" in depot_name.lower():
                    coordinates = DEPOT_GPS_COORDINATES["oistins"]
                elif "airport" in depot_name.lower():
                    coordinates = DEPOT_GPS_COORDINATES["airport"]
                else:
                    # Default to Bridgetown area for unknown depots
                    coordinates = DEPOT_GPS_COORDINATES["bridgetown"]
                    print(f"   ⚠️  Using default Bridgetown coordinates")
                
                if coordinates:
                    # Update depot with GPS coordinates
                    update_data = {
                        "data": {
                            "location": {
                                "lat": coordinates["lat"],
                                "lon": coordinates["lon"]
                            }
                        }
                    }
                    
                    print(f"   📍 Setting GPS: {coordinates['lat']:.6f}, {coordinates['lon']:.6f}")
                    print(f"   📝 {coordinates['description']}")
                    
                    # PUT request to update depot
                    update_response = await client.put(
                        f"http://localhost:1337/api/depots/{document_id}",
                        json=update_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if update_response.status_code == 200:
                        print(f"   ✅ Successfully updated depot coordinates")
                    else:
                        print(f"   ❌ Failed to update depot: HTTP {update_response.status_code}")
                        print(f"      Response: {update_response.text}")
                
            print(f"\n🎯 DEPOT GPS MIGRATION COMPLETED!")
            print(f"   All depots should now have realistic GPS coordinates.")
            print(f"   Ready for commuter reservoir spatial spawning!")
            
        except Exception as e:
            print(f"❌ Error updating depot coordinates: {e}")
            import traceback
            traceback.print_exc()

async def verify_depot_coordinates():
    """Verify the GPS coordinates were set correctly"""
    print(f"\n🔍 VERIFYING DEPOT GPS COORDINATES")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:1337/api/depots")
            response.raise_for_status()
            depots_data = response.json()
            
            success_count = 0
            
            for depot in depots_data['data']:
                depot_name = depot['name']
                location = depot.get('location')
                
                print(f"\n🏢 {depot_name}:")
                
                if location and isinstance(location, dict) and 'lat' in location and 'lon' in location:
                    lat, lon = location['lat'], location['lon']
                    print(f"   ✅ GPS: {lat:.6f}, {lon:.6f}")
                    
                    # Validate coordinates are in Barbados area
                    if 13.0 <= lat <= 13.3 and -59.7 <= lon <= -59.4:
                        print(f"   ✅ Coordinates valid for Barbados")
                        success_count += 1
                    else:
                        print(f"   ⚠️  Coordinates outside Barbados area")
                else:
                    print(f"   ❌ No valid GPS coordinates")
            
            print(f"\n📊 VERIFICATION SUMMARY:")
            print(f"   Depots with valid GPS: {success_count}/{len(depots_data['data'])}")
            
            if success_count == len(depots_data['data']):
                print(f"   🎉 All depots have valid GPS coordinates!")
                return True
            else:
                print(f"   ⚠️  Some depots still missing coordinates")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying coordinates: {e}")
            return False

async def main():
    """Main migration process"""
    print("🚀 DEPOT GPS COORDINATES MIGRATION")
    print("=" * 60)
    print("This will add realistic GPS coordinates to all depot records.")
    print("Required for commuter reservoir spatial spawning to work correctly.")
    print()
    
    # Step 1: Update coordinates
    await update_depot_coordinates()
    
    # Step 2: Verify coordinates
    success = await verify_depot_coordinates()
    
    if success:
        print(f"\n🎉 MIGRATION SUCCESSFUL!")
        print(f"   Depot GPS coordinates are now ready for commuter spawning.")
        print(f"   You can proceed with reservoir system testing.")
    else:
        print(f"\n❌ MIGRATION INCOMPLETE!")
        print(f"   Some depots may still be missing GPS coordinates.")
        print(f"   Check Strapi admin panel to verify data.")

if __name__ == "__main__":
    asyncio.run(main())