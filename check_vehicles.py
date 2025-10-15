"""Check what vehicles are in Strapi"""
import asyncio
import aiohttp
import json

async def list_vehicles():
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:1337/api/vehicles"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    print("Raw response:")
                    print(json.dumps(data, indent=2))
                else:
                    print(f"❌ HTTP {response.status}")
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(list_vehicles())
