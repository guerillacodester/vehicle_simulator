import asyncio
import math
from arknet_transit_simulator.core.dispatcher import StrapiStrategy

API_BASE_URL = "http://localhost:1337"
ROUTE_CODE = "1"
# Start and end points
A = (13.319009, -59.633851)  # lat, lon at 2025-11-08T01:51:22.098Z
C = (13.253114, -59.642225)  # lat, lon at 2025-11-08T01:58:26.239Z (latest repeated)
SECONDS = 424.141  # total elapsed seconds
SUSTAINED_SPEED_KMH = 90.0


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def nearest_index(coords, lat, lon):
    best_i, best_d = None, 1e18
    for i, (lo, la) in enumerate(coords):
        d = haversine(lat, lon, la, lo)
        if d < best_d:
            best_d, best_i = d, i
    return best_i, best_d


async def main():
    strat = StrapiStrategy(API_BASE_URL)
    await strat.initialize()
    ok = await strat.test_connection()
    if not ok:
        print("Failed to connect to Strapi API")
        return
    route = await strat.get_route_info(ROUTE_CODE)
    if not route or not route.geometry:
        print("No geometry")
        return
    coords = route.geometry['coordinates']  # [lon, lat]

    # Straight-line distance
    straight_km = haversine(A[0], A[1], C[0], C[1])

    # Nearest indices
    ia, da = nearest_index(coords, A[0], A[1])
    ic, dc = nearest_index(coords, C[0], C[1])

    if ia is None or ic is None:
        print("Failed to locate indices in route coords")
        return
    if ic < ia:
        ia, ic = ic, ia

    # Path distance along route between ia..ic
    path_km = 0.0
    for i in range(ia, ic):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i+1]
        path_km += haversine(lat1, lon1, lat2, lon2)

    # Distance by speed*time
    speed_time_km = SUSTAINED_SPEED_KMH * (SECONDS / 3600.0)

    print(f"Elapsed seconds: {SECONDS:.3f} s")
    print(f"Straight-line distance (A→C): {straight_km:.3f} km")
    print(f"Route path distance (indices {ia}->{ic}, steps {ic-ia}): {path_km:.3f} km")
    print(f"Nearest A error: {da:.3f} km; Nearest C error: {dc:.3f} km")
    print(f"Distance by {SUSTAINED_SPEED_KMH:.1f} km/h for {SECONDS:.3f}s: {speed_time_km:.3f} km")
    print(f"Required avg speed (straight): {straight_km / (SECONDS/3600):.1f} km/h")
    print(f"Required avg speed (path): {path_km / (SECONDS/3600):.1f} km/h")

    await strat.close()

if __name__ == "__main__":
    asyncio.run(main())
