import asyncio
from commuter_service.strapi_api_client import StrapiApiClient

async def test():
    async with StrapiApiClient() as client:
        country = await client.get_country_by_code('BB')  # Use 2-letter code
        zones = await client.get_landuse_zones_by_country(country['id'])
        
        types = set([z.get('landuse_type', 'NONE') for z in zones])
        print(f'Found {len(zones)} zones with landuse types: {sorted(types)}')
        
        # Show first 5 zones
        print("\nFirst 5 zones:")
        for i, zone in enumerate(zones[:5]):
            print(f"  Zone {i+1}: landuse_type={zone.get('landuse_type', 'MISSING')}, zone_type={zone.get('zone_type', 'MISSING')}")

asyncio.run(test())
