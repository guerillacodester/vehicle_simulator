import asyncio
import math
from arknet_transit_simulator.core.dispatcher import StrapiStrategy

API_BASE_URL = "http://localhost:1337"
ROUTE_CODE = "1"
# Previous and end points for second leg
A = (13.288061, -59.640348)  # 01:55:06.168Z
B1 = (13.253837, -59.642372) # 01:58:06.231Z
B2 = (13.253114, -59.642225) # 01:58:26.239Z

T1 = 180.063  # seconds from A to B1
T2 = 200.071  # seconds from A to B2


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


async def run_one(coords, A, B, seconds):
    ia, da = nearest_index(coords, A[0], A[1])
    ib, db = nearest_index(coords, B[0], B[1])
    if ib < ia:
        ia, ib = ib, ia
    path_km = 0.0
    for i in range(ia, ib):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i+1]
        path_km += haversine(lat1, lon1, lat2, lon2)
    straight_km = haversine(A[0], A[1], B[0], B[1])
    possible_km = 90.0 * (seconds/3600.0)
    return {
        'ia': ia, 'ib': ib,
        'errA_km': da, 'errB_km': db,
        'straight_km': straight_km,
        'path_km': path_km,
        'possible_km': possible_km,
        'req_speed_straight': straight_km / (seconds/3600.0),
        'req_speed_path': path_km / (seconds/3600.0),
    }


async def main():
    strat = StrapiStrategy(API_BASE_URL)
    await strat.initialize()
    if not await strat.test_connection():
        print("Strapi not connected")
        return
    route = await strat.get_route_info(ROUTE_CODE)
    if not route or not route.geometry:
        print("No geometry")
        return
    coords = route.geometry['coordinates']

    r1 = await run_one(coords, A, B1, T1)
    r2 = await run_one(coords, A, B2, T2)

    def show(tag, r):
        print(f"--- {tag} ---")
        print(f"Indices {r['ia']}->{r['ib']} (count {r['ib']-r['ia']})")
        print(f"Nearest errors A/B: {r['errA_km']:.3f} / {r['errB_km']:.3f} km")
        print(f"Straight-line: {r['straight_km']:.3f} km")
        print(f"Path: {r['path_km']:.3f} km")
        print(f"Possible at 90 km/h: {r['possible_km']:.3f} km")
        print(f"Required avg speed straight: {r['req_speed_straight']:.1f} km/h")
        print(f"Required avg speed path: {r['req_speed_path']:.1f} km/h")

    show('A -> B1 (to 01:58:06.231Z)', r1)
    show('A -> B2 (to 01:58:26.239Z)', r2)

    await strat.close()

if __name__ == '__main__':
    asyncio.run(main())
