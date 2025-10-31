import httpx
import asyncio
import json

async def check():
    client = httpx.AsyncClient()
    
    # Get route-depots with depot populated
    r = await client.get('http://localhost:1337/api/route-depots?populate=*&pagination[pageSize]=100')
    data = r.json()
    
    print("RAW DATA:")
    print(json.dumps(data, indent=2))

asyncio.run(check())
