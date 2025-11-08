import asyncio
import math
from arknet_transit_simulator.core.dispatcher import StrapiStrategy

API_BASE_URL = "http://localhost:1337"
ROUTE_CODE = "1"
# Previous and current points
A = (13.319009, -59.633851)  # lat, lon
B = (13.288061, -59.640348)
# Times (ISO) for reference only
SECONDS = 224.07


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
    straight_km = haversine(A[0], A[1], B[0], B[1])

    # Nearest indices
    ia, da = nearest_index(coords, A[0], A[1])
    ib, db = nearest_index(coords, B[0], B[1])

    # Ensure forward order
    if ia is None or ib is None:
        print("Failed to locate indices in route coords")
        return
    if ib < ia:
        ia, ib = ib, ia

    # Path distance along route between ia..ib
    path_km = 0.0
    for i in range(ia, ib):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i+1]
        path_km += haversine(lat1, lon1, lat2, lon2)

    # Possible distance at 90 km/h in given seconds
    possible_km = 90.0 * (SECONDS / 3600.0)

    print(f"Straight-line km: {straight_km:.3f}")
    print(f"Path km (indices {ia}->{ib}, count {ib-ia}): {path_km:.3f}")
    print(f"Nearest A error km: {da:.003f}; Nearest B error km: {db:.003f}")
    print(f"Possible at 90 km/h for {SECONDS:.2f}s: {possible_km:.3f} km")
    print(f"Required avg speed (straight): {straight_km / (SECONDS/3600):.1f} km/h")
    print(f"Required avg speed (path): {path_km / (SECONDS/3600):.1f} km/h")

    await strat.close()

if __name__ == "__main__":
    asyncio.run(main())
