import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        r = await client.get('http://localhost:1337/api/routes?pagination[pageSize]=1')
        print(f"Status: {r.status_code}")
        print(f"Success: {r.status_code == 200}")

asyncio.run(test())
