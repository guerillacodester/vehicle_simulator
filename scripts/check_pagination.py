"""Check total passenger count with pagination"""
import asyncio
import httpx

async def check():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get("http://localhost:1337/api/active-passengers")
        data = r.json()
        meta = data.get("meta", {})
        pagination = meta.get("pagination", {})
        
        print("PAGINATION INFO:")
        print(f"  Page: {pagination.get('page', '?')}")
        print(f"  PageSize: {pagination.get('pageSize', '?')}")
        print(f"  PageCount: {pagination.get('pageCount', '?')}")
        print(f"  Total: {pagination.get('total', '?')}")

asyncio.run(check())
