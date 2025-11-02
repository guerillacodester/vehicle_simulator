"""Get ALL passengers and show complete statistics"""
import asyncio
import httpx
from collections import Counter

async def check():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get ALL passengers (increase page size)
        r = await client.get("http://localhost:1337/api/active-passengers?pagination[pageSize]=500")
        data = r.json()
        passengers = data.get("data", [])
        
        print(f"TOTAL PASSENGERS: {len(passengers)}")
        print()
        
        if len(passengers) > 0:
            # Count by hour
            hourly_counts = Counter()
            depot_vs_route = Counter()
            
            for p in passengers:
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
            for hour in range(24):
                hour_str = f"{hour:02d}"
                count = hourly_counts.get(hour_str, 0)
                bar = "█" * (count // 5) if count > 0 else ""
                print(f"  {hour_str}:00 - {count:>3} passengers {bar}")
            print()
            
            print(f"TOTAL spawns: {sum(hourly_counts.values())}")
            hours_with_spawns = sum(1 for c in hourly_counts.values() if c > 0)
            print(f"Hours with spawns: {hours_with_spawns}/24")

asyncio.run(check())
