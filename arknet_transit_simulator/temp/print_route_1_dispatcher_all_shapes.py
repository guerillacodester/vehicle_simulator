
import asyncio
from arknet_transit_simulator.core.dispatcher import StrapiStrategy

API_BASE_URL = "http://localhost:1337"  # Change if needed
ROUTE_CODE = "1"

async def main():
    strategy = StrapiStrategy(API_BASE_URL)
    await strategy.initialize()
    connected = await strategy.test_connection()
    if not connected:
        print("Failed to connect to Strapi API")
        return
    route_info = await strategy.get_route_info(ROUTE_CODE)
    if not route_info or not route_info.geometry:
        print("No route info or geometry found.")
        return
    coords = route_info.geometry['coordinates']
    print(f"Route 1 coordinates from dispatcher (ALL shapes):")
    for idx, pt in enumerate(coords, 1):
        print(f"{idx}: [{pt[0]}, {pt[1]}]")
    # Calculate total distance
    import math
    def haversine(lon1, lat1, lon2, lat2):
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    total_km = 0.0
    for i in range(len(coords)-1):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i+1]
        total_km += haversine(lon1, lat1, lon2, lat2)
    print(f"\nTotal route 1 distance (dispatcher ALL shapes): {total_km:.3f} km")
    await strategy.close()

if __name__ == "__main__":
    asyncio.run(main())
