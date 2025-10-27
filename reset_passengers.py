#!/usr/bin/env python3
"""
Reset active-passengers table by deleting all records
"""

import asyncio
import httpx


async def reset_passengers():
    """Delete all passengers from the database"""
    async with httpx.AsyncClient() as client:
        # Get all passengers
        response = await client.get(
            'http://localhost:1337/api/active-passengers',
            params={'pagination[pageSize]': 1000}
        )
        data = response.json()
        passengers = data.get('data', [])
        
        print(f"Found {len(passengers)} passengers to delete...")
        
        # Delete each passenger
        for passenger in passengers:
            try:
                await client.delete(f"http://localhost:1337/api/active-passengers/{passenger['id']}")
            except Exception as e:
                print(f"Error deleting passenger {passenger['id']}: {e}")
        
        print(f"✓ Deleted {len(passengers)} passengers")


if __name__ == '__main__':
    asyncio.run(reset_passengers())
