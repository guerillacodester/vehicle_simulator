import asyncio
import json
from commuter_service.strapi_api_client import StrapiApiClient

async def test():
    async with StrapiApiClient() as client:
        country = await client.get_country_by_code('BB')
        zones = await client.get_landuse_zones_by_country(country['id'])
        
        print(f"First zone fields:")
        print(json.dumps(zones[0], indent=2, default=str))

asyncio.run(test())
