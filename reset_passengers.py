#!/usr/bin/env python3
"""
Reset Passenger Database

Deletes all passengers from Strapi database.
Use this to start fresh for testing.

Usage:
    python reset_passengers.py
"""

import asyncio
import httpx


STRAPI_URL = "http://localhost:1337"


async def delete_all_passengers():
    """Delete all passengers from Strapi"""
    print("=" * 80)
    print("🗑️  RESETTING PASSENGER DATABASE")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, check if Strapi is running
        print("📡 Checking Strapi connection...")
        try:
            health = await client.get(f"{STRAPI_URL}/_health")
            print(f"   ✅ Strapi is running")
        except Exception as e:
            print(f"   ❌ Cannot connect to Strapi: {e}")
            return
        print()
        
        # Try different possible endpoints
        endpoints = [
            "/api/active-passengers",
            "/api/passengers",
            "/api/commuter-passengers", 
            "/api/commuter-passenger",
            "/api/passenger"
        ]
        
        passengers = []
        working_endpoint = None
        
        print("📊 Finding passenger endpoint and fetching ALL passengers...")
        for endpoint in endpoints:
            try:
                # Fetch ALL passengers with pagination
                page = 1
                page_size = 100  # Smaller batches
                all_passengers = []
                
                while True:
                    response = await client.get(
                        f"{STRAPI_URL}{endpoint}",
                        params={
                            'pagination[page]': page,
                            'pagination[pageSize]': page_size
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        page_passengers = data.get('data', [])
                        
                        if not page_passengers:
                            # No more passengers
                            break
                        
                        all_passengers.extend(page_passengers)
                        
                        # Check if there are more pages
                        meta = data.get('meta', {})
                        pagination = meta.get('pagination', {})
                        total_pages = pagination.get('pageCount', 1)
                        
                        print(f"   Page {page}/{total_pages}: {len(page_passengers)} passengers")
                        
                        if page >= total_pages:
                            break
                        
                        page += 1
                    else:
                        break
                
                # If we got a 200 response, this endpoint works (even if empty)
                if response.status_code == 200:
                    passengers = all_passengers
                    working_endpoint = endpoint
                    if all_passengers:
                        print(f"   ✅ Found {len(passengers)} passengers at {endpoint}")
                    else:
                        print(f"   ✅ Found endpoint {endpoint} (0 passengers)")
                    break
                    
            except Exception as e:
                continue
        
        if not working_endpoint:
            print("   ❌ Could not find passenger endpoint")
            print("   Tried:", ", ".join(endpoints))
            return
        
        total = len(passengers)
        
        if total == 0:
            print("✅ Database is already empty")
            return
        
        print()
        print("🗑️  Deleting all passengers...")
        deleted = 0
        failed = 0
        
        # Delete all passengers we already fetched
        for passenger in passengers:
            doc_id = passenger.get("documentId")
            if not doc_id:
                failed += 1
                continue
            
            try:
                delete_response = await client.delete(
                    f"{STRAPI_URL}{working_endpoint}/{doc_id}"
                )
                if delete_response.status_code in [200, 204]:
                    deleted += 1
                    if deleted % 50 == 0:
                        print(f"   Deleted {deleted}/{total}...")
                else:
                    failed += 1
            except Exception as e:
                failed += 1
        
        print()
        print("=" * 80)
        print("✅ RESET COMPLETE")
        print("=" * 80)
        print()
        print(f"   Deleted: {deleted}")
        print(f"   Failed: {failed}")
        print(f"   Total: {total}")
        print()


async def main():
    try:
        await delete_all_passengers()
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
