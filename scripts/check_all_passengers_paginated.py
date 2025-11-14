"""Get ALL passengers using proper pagination"""
import asyncio
import httpx
from collections import Counter

async def check():
    all_passengers = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, get pagination info
        r = await client.get("http://localhost:1337/api/active-passengers")
        data = r.json()
        meta = data.get("meta", {})
        pagination = meta.get("pagination", {})
        page_count = pagination.get("pageCount", 1)
        total = pagination.get("total", 0)
        
        print(f"Fetching {total} passengers across {page_count} pages...")
        print()
        
        # Fetch all pages
        for page in range(1, page_count + 1):
            r = await client.get(f"http://localhost:1337/api/active-passengers?pagination[page]={page}&pagination[pageSize]=100")
            data = r.json()
            passengers = data.get("data", [])
            all_passengers.extend(passengers)
            print(f"  Page {page}/{page_count}: {len(passengers)} passengers")
        
        print()
        print(f"TOTAL PASSENGERS FETCHED: {len(all_passengers)}")
        print()
        
        if len(all_passengers) > 0:
            # Count by hour
            hourly_counts = Counter()
            depot_vs_route = Counter()
            
            for p in all_passengers:
                depot_id = p.get("depot_id")
                spawned_at = p.get("spawned_at")
                
                if depot_id:
                    depot_vs_route["depot"] += 1
                else:
                    depot_vs_route["route"] += 1
                    
                if spawned_at:
                    # Extract hour from timestamp
                    hour = spawned_at.split("T")[1].split(":")[0] if "T" in spawned_at else "unknown"
                    hourly_counts[hour] += 1
            
            print("DEPOT vs ROUTE PASSENGERS:")
            print(f"  Depot passengers: {depot_vs_route.get('depot', 0)}")
            print(f"  Route passengers: {depot_vs_route.get('route', 0)}")
            print()
            
            print("HOURLY DISTRIBUTION (all 24 hours):")
            max_count = max(hourly_counts.values()) if hourly_counts else 1
            for hour in range(24):
                hour_str = f"{hour:02d}"
                count = hourly_counts.get(hour_str, 0)
                bar_len = int((count / max_count) * 40) if count > 0 else 0
                bar = "█" * bar_len
                print(f"  {hour_str}:00 - {count:>3} passengers {bar}")
            print()
            
            print(f"TOTAL spawns: {sum(hourly_counts.values())}")
            hours_with_spawns = sum(1 for c in hourly_counts.values() if c > 0)
            print(f"Hours with spawns: {hours_with_spawns}/24")

asyncio.run(check())
