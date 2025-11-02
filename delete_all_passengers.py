#!/usr/bin/env python3
"""Delete all passengers from Strapi database"""

import requests
import time

API_URL = "http://localhost:1337/api/active-passengers"

def delete_all_passengers():
    """Delete all passengers in batches"""
    total_deleted = 0
    
    while True:
        # Fetch batch
        response = requests.get(f"{API_URL}?pagination[pageSize]=100")
        data = response.json().get("data", [])
        
        if not data:
            break
        
        # Delete batch
        for passenger in data:
            doc_id = passenger["documentId"]
            requests.delete(f"{API_URL}/{doc_id}")
            total_deleted += 1
        
        print(f"Deleted {len(data)} passengers (total: {total_deleted})")
        time.sleep(0.2)  # Rate limiting
    
    print(f"\n✅ All done! Deleted {total_deleted} passengers total")

if __name__ == "__main__":
    print("🗑️  Deleting all passengers from database...\n")
    delete_all_passengers()
