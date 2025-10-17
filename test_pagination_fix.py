import asyncio
from commuter_service.strapi_api_client import StrapiApiClient

async def test():
    async with StrapiApiClient() as client:
        country = await client.get_country_by_code('BB')
        zones = await client.get_landuse_zones_by_country(country['id'])
        
        print(f"\n{'='*80}")
        print(f"Pagination Test - After Fix")
        print(f"{'='*80}")
        print(f"Total landuse zones retrieved: {len(zones)}")
        
        # Check zone type distribution
        zone_types = {}
        for zone in zones:
            ztype = zone.get('zone_type', 'unknown')
            zone_types[ztype] = zone_types.get(ztype, 0) + 1
        
        print(f"\nZone type distribution:")
        for ztype, count in sorted(zone_types.items(), key=lambda x: -x[1]):
            print(f"  {ztype}: {count} zones")

asyncio.run(test())
