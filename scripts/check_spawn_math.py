"""Check spawn calculation math"""
import asyncio
import httpx

async def test():
    # Get spawn config
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:1337/api/spawn-configs?filters[route][short_name][$eq]=1&populate=*")
    data = r.json()["data"][0]
    config = data["config"]
    
    # Get parameters
    base_rate = config["distribution_params"]["passengers_per_building_per_hour"]
    hourly_8am = float(config["hourly_rates"]["8"])
    day_monday = float(config["day_multipliers"]["0"])
    
    depot_buildings = 450
    route_buildings = 325
    
    effective_rate = base_rate * hourly_8am * day_monday
    
    depot_per_hour = depot_buildings * effective_rate
    route_per_hour = route_buildings * effective_rate
    total_per_hour = depot_per_hour + route_per_hour
    
    print(f"BASE RATE: {base_rate}")
    print(f"HOURLY (8AM): {hourly_8am}")
    print(f"DAY (Monday): {day_monday}")
    print(f"EFFECTIVE RATE: {effective_rate}")
    print(f"")
    print(f"DEPOT BUILDINGS: {depot_buildings}")
    print(f"ROUTE BUILDINGS: {route_buildings}")
    print(f"")
    print(f"EXPECTED PER HOUR:")
    print(f"  Depot: {depot_per_hour:.1f}")
    print(f"  Route: {route_per_hour:.1f}")
    print(f"  Total: {total_per_hour:.1f}")

asyncio.run(test())
