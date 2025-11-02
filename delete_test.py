import httpx
import asyncio

async def delete_passengers():
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            'http://localhost:4000/api/manifest',
            params={
                'day': 'monday',
                'route': 'gg3pv3z19hhm117v9xth5ezq',
                'confirm': 'true'
            }
        )
        print(response.json())

asyncio.run(delete_passengers())
