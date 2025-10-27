import requests
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor

async def delete_passengers_async(batch_size=10):
    """Delete passengers using concurrent HTTP requests for speed"""
    
    # Get all passengers
    r = requests.get('http://localhost:1337/api/active-passengers?pagination[pageSize]=1000')
    data = r.json()
    passengers = data.get('data', [])
    print(f'Found {len(passengers)} passengers to delete')
    
    # Delete concurrently using httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = []
        for p in passengers:
            doc_id = p.get('documentId')
            url = f'http://localhost:1337/api/active-passengers/{doc_id}'
            tasks.append(client.delete(url))
        
        print(f'Sending {len(tasks)} concurrent delete requests...')
        responses = await asyncio.gather(*tasks)
        
        deleted = sum(1 for r in responses if r.status_code in [200, 204])
        failed = sum(1 for r in responses if r.status_code not in [200, 204])
    
    print(f'\n[RESULT] Deleted: {deleted}')
    print(f'[RESULT] Failed: {failed}')
    
    # Verify
    r2 = requests.get('http://localhost:1337/api/active-passengers?pagination[pageSize]=1000')
    remaining = len(r2.json().get('data', []))
    print(f'[RESULT] Remaining in DB: {remaining}')

if __name__ == '__main__':
    asyncio.run(delete_passengers_async())
