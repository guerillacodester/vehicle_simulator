"""Check passengers in database and show statistics"""
import asyncio
import httpx
from collections import Counter

async def check():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Get all passengers
        r = await client.get("http://localhost:1337/api/active-passengers?pagination[pageSize]=100")
        data = r.json()
        passengers = data.get("data", [])
        
        print(f"TOTAL PASSENGERS: {len(passengers)}")
        print()
        
        if len(passengers) > 0:
            # Count by route
            route_counts = Counter()
            depot_counts = Counter()
            hourly_counts = Counter()
            
            for p in passengers:
                route_id = p.get("route_id")
                depot_id = p.get("depot_id")
                spawned_at = p.get("spawned_at")
                
                if route_id:
                    route_counts[route_id] += 1
                if depot_id:
                    depot_counts["has_depot"] += 1
                else:
                    depot_counts["no_depot"] += 1
                    
                if spawned_at:
                    # Extract hour from timestamp
                    hour = spawned_at.split("T")[1].split(":")[0] if "T" in spawned_at else "unknown"
                    hourly_counts[hour] += 1
            
            print("BY ROUTE:")
            for route_id, count in sorted(route_counts.items()):
                print(f"  Route {route_id}: {count} passengers")
            print()
            
            print("DEPOT vs ROUTE PASSENGERS:")
            for category, count in sorted(depot_counts.items()):
                label = "Depot passengers" if category == "has_depot" else "Route passengers"
                print(f"  {label}: {count}")
            print()
            
            print("BY HOUR (spawned_at):")
            for hour, count in sorted(hourly_counts.items()):
                print(f"  {hour}:00 - {count} passengers")
            print()
            
            # Show first few passengers
            print("SAMPLE PASSENGERS (first 5):")
            for i, p in enumerate(passengers[:5]):
                route = p.get("route_id", "?")
                depot = p.get("depot_id", "None")
                spawned = p.get("spawned_at", "?")
                status = p.get("status", "?")
                print(f"  [{i+1}] Route: {route}, Depot: {depot}, Status: {status}")
                print(f"      Spawned: {spawned}")
        else:
            print("No passengers in database.")

asyncio.run(check())
