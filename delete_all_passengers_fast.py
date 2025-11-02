#!/usr/bin/env python3
"""Delete all passengers from Strapi database - FAST BATCH VERSION"""

import requests
import concurrent.futures

API_URL = "http://localhost:1337/api/active-passengers"

def delete_passenger(doc_id):
    """Delete a single passenger"""
    try:
        requests.delete(f"{API_URL}/{doc_id}", timeout=5)
        return True
    except:
        return False

def delete_all_passengers_fast():
    """Delete all passengers using parallel requests"""
    total_deleted = 0
    
    while True:
        # Fetch batch of 100
        response = requests.get(f"{API_URL}?pagination[pageSize]=100")
        data = response.json().get("data", [])
        
        if not data:
            break
        
        doc_ids = [p["documentId"] for p in data]
        
        # Delete in parallel (100 at a time for MAXIMUM speed)
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            results = list(executor.map(delete_passenger, doc_ids))
        
        deleted_count = sum(results)
        total_deleted += deleted_count
        
        print(f"Deleted {deleted_count} passengers (total: {total_deleted})")
    
    print(f"\n✅ All done! Deleted {total_deleted} passengers total")

if __name__ == "__main__":
    print("🗑️  FAST DELETE: Removing all passengers from database...\n")
    delete_all_passengers_fast()
