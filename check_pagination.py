import asyncio
import json
from commuter_service.strapi_api_client import StrapiApiClient

async def test():
    async with StrapiApiClient() as client:
        # Check pagination info
        response = await client.session.get(
            f"{client.base_url}/api/landuse-zones",
            params={
                "filters[country][id][$eq]": 29,
                "pagination[pageSize]": 5000,
                "sort": "zone_type:asc"
            }
        )
        data = response.json()
        
        print("Pagination info:")
        print(json.dumps(data.get('meta', {}), indent=2))
        print(f"\nActual data returned: {len(data.get('data', []))} records")
        
        # Also check without country filter to see total
        response_all = await client.session.get(
            f"{client.base_url}/api/landuse-zones",
            params={
                "pagination[pageSize]": 1,  # Just get count
            }
        )
        data_all = response_all.json()
        print(f"\nTotal landuse zones in database (all countries):")
        print(json.dumps(data_all.get('meta', {}), indent=2))

asyncio.run(test())
