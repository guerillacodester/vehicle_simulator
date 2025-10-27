import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        url = "http://localhost:1337/api/routes?populate=*&filters[short_name][$eq]=1"
        print(f"Fetching: {url}")
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Found routes: {len(data['data'])}")
        if data['data']:
            route = data['data'][0]
            print(f"Route name: {route['long_name']}")
            print(f"Features: {len(route['geojson_data']['features'])}")

asyncio.run(test())
