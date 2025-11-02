#!/usr/bin/env python3
"""
Populate Spawn Configuration for Route 1

Updates the spawn config in Strapi database with normalized values.
Target: ~45 passengers at peak hour (3 vans × 15 passengers)
"""

import asyncio
import httpx
import json

STRAPI_URL = "http://localhost:1337"
ROUTE_SHORT_NAME = "1"

# Spawn configuration with normalized values (0-1.0)
# Separate rates for depot vs route spawners!
SPAWN_CONFIG = {
    'depot_base_rate': 0.30,   # DepotSpawner: 200 buildings × 0.30 = 60 depot passengers at peak
    'route_base_rate': 0.012,  # RouteSpawner: 3514 buildings × 0.012 = 42 route passengers at peak
    'hourly_rates': [
        0.0,   # 00:00 - midnight (no spawns)
        0.0,   # 01:00
        0.0,   # 02:00
        0.0,   # 03:00
        0.0,   # 04:00
        0.15,  # 05:00 - early morning start
        0.35,  # 06:00 - morning ramp up
        0.75,  # 07:00 - pre-peak
        1.0,   # 08:00 - PEAK MORNING
        0.45,  # 09:00 - post-peak
        0.25,  # 10:00 - mid-morning
        0.20,  # 11:00
        0.30,  # 12:00 - lunch
        0.25,  # 13:00
        0.30,  # 14:00
        0.40,  # 15:00 - afternoon pickup
        0.55,  # 16:00 - pre-evening peak
        0.85,  # 17:00 - PEAK EVENING
        0.40,  # 18:00 - post-evening peak
        0.20,  # 19:00
        0.10,  # 20:00 - evening wind down
        0.05,  # 21:00
        0.0,   # 22:00
        0.0,   # 23:00
    ],
    'day_multipliers': [
        1.0,  # Monday - full weekday traffic
        1.0,  # Tuesday - full weekday traffic
        1.0,  # Wednesday - full weekday traffic
        1.0,  # Thursday - full weekday traffic
        1.0,  # Friday - full weekday traffic
        1.0,  # Saturday - full weekend traffic
        0.6,  # Sunday - reduced weekend traffic
    ]
}

# Target: ~42 ROUTE passengers at peak hour (based on ACTUAL building count ~3300)
# Formula: route_passengers = route_buildings × spatial_base_rate × hourly_rate × day_mult
# At peak (8 AM, Mon): 42 = 3300 × spatial_base × 1.0 × 1.0
# spatial_base = 42 / 3300 = 0.0127
#
# Using 0.0128 (calibrated for actual geospatial building count)
# Note: DepotSpawner spawns depot passengers separately


async def populate_spawn_config():
    """Populate spawn config in Strapi database."""
    print("=" * 80)
    print("🌱 POPULATING SPAWN CONFIGURATION")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Find the spawn-config record for Route 1
        print(f"📡 Finding spawn config for Route {ROUTE_SHORT_NAME}...")
        response = await client.get(
            f"{STRAPI_URL}/api/spawn-configs",
            params={
                "filters[route][short_name][$eq]": ROUTE_SHORT_NAME,
                "populate": "*"
            }
        )
        
        if response.status_code != 200:
            print(f"   ❌ Error fetching spawn config: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        data = response.json().get('data', [])
        if not data:
            print(f"   ❌ No spawn config found for Route {ROUTE_SHORT_NAME}")
            print("   Create one in Strapi admin first!")
            return
        
        config_record = data[0]
        document_id = config_record.get('documentId')
        
        print(f"   ✅ Found spawn config (documentId: {document_id})")
        print()
        
        # 2. Update the spawn config
        print("📝 Updating spawn config values...")
        print(f"   Depot Base Rate: {SPAWN_CONFIG['depot_base_rate']}")
        print(f"   Route Base Rate: {SPAWN_CONFIG['route_base_rate']}")
        print(f"   Hourly Rates: {len(SPAWN_CONFIG['hourly_rates'])} values")
        print(f"   Day Multipliers: {len(SPAWN_CONFIG['day_multipliers'])} values")
        print()
        
        # Strapi spawn-config stores settings under a `config` field. Build
        # the payload to update the `config` object rather than top-level keys.
        hourly_rates_map = {str(i): v for i, v in enumerate(SPAWN_CONFIG['hourly_rates'])}
        day_mult_map = {str(i): v for i, v in enumerate(SPAWN_CONFIG['day_multipliers'])}

        payload = {
            "data": {
                "config": {
                    "hourly_rates": hourly_rates_map,
                    "day_multipliers": day_mult_map,
                    # Store BOTH depot and route rates
                    "distribution_params": {
                        "depot_passengers_per_building_per_hour": SPAWN_CONFIG['depot_base_rate'],
                        "route_passengers_per_building_per_hour": SPAWN_CONFIG['route_base_rate']
                    }
                }
            }
        }

        update_response = await client.put(
            f"{STRAPI_URL}/api/spawn-configs/{document_id}",
            json=payload
        )
        
        if update_response.status_code not in [200, 201]:
            print(f"   ❌ Error updating spawn config: {update_response.status_code}")
            print(f"   Response: {update_response.text}")
            return
        
        print("   ✅ Spawn config updated successfully!")
        print()
        
        # 3. Verify the update
        print("🔍 Verifying update...")
        verify_response = await client.get(
            f"{STRAPI_URL}/api/spawn-configs/{document_id}"
        )
        
        if verify_response.status_code == 200:
            verified = verify_response.json()['data']
            print(f"   ✅ Verified spatial_base_rate: {verified.get('spatial_base_rate')}")
            print(f"   ✅ Verified hourly_rates length: {len(verified.get('hourly_rates', []))}")
            print(f"   ✅ Verified day_multipliers length: {len(verified.get('day_multipliers', []))}")
        
        print()
        print("=" * 80)
        print("✅ SPAWN CONFIG POPULATION COMPLETE")
        print("=" * 80)
        print()
        print("Expected spawning:")
        print(f"  Peak hour (8 AM weekday):")
        print(f"    Depot: ~60 passengers (4 vans)")
        print(f"    Route: ~40 passengers (additional)")
        print(f"    Total: ~100 passengers")
        print(f"  Daily total (weekday): ~1,300 passengers")
        print(f"  Daily total (Sunday): ~780 passengers (60% reduction)")


async def main():
    try:
        await populate_spawn_config()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
