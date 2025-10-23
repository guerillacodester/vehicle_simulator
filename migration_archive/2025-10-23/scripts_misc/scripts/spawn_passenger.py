"""
Spawn a test passenger via PassengerDatabase (Strapi API) for manual integration testing.

Usage (PowerShell):
    python .\\scripts\\spawn_passenger.py --route 1A --lat 13.319443 --lon -59.636900

By default this will create a passenger near the vehicle start location on route '1A'.
"""
import asyncio
import uuid
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from commuter_service.passenger_db import PassengerDatabase

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--route', default='1A')
    parser.add_argument('--lat', type=float, default=13.319443)
    parser.add_argument('--lon', type=float, default=-59.636900)
    parser.add_argument('--dest-lat', type=float, default=13.319500)
    parser.add_argument('--dest-lon', type=float, default=-59.636800)
    parser.add_argument('--strapi', default='http://localhost:1337')
    # Strapi validation requires direction to be one of: OUTBOUND, INBOUND
    parser.add_argument('--direction', default='OUTBOUND')
    args = parser.parse_args()

    passenger_db = PassengerDatabase(strapi_url=args.strapi)
    await passenger_db.connect()

    passenger_id = f"test-{uuid.uuid4().hex[:8]}"
    ok = await passenger_db.insert_passenger(
        passenger_id=passenger_id,
        route_id=args.route,
        latitude=args.lat,
        longitude=args.lon,
        destination_lat=args.dest_lat,
        destination_lon=args.dest_lon,
        destination_name='TestDest',
        depot_id=None,
        direction=args.direction,
        priority=5,
        expires_minutes=60
    )

    if ok:
        print(f"Inserted passenger {passenger_id} on route {args.route}")
    else:
        print("Failed to insert passenger")

    await passenger_db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
