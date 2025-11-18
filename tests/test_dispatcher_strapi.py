import asyncio
import os
import logging
from arknet_transit_simulator.services.strapi_client import StrapiClient
from arknet_transit_simulator.core.dispatcher import StrapiStrategy

logging.basicConfig(level=logging.INFO)

STRAPI_URL = os.getenv('STRAPI_URL', 'http://localhost:1337')
STRAPI_USERNAME = os.getenv('STRAPI_USERNAME', 'vehicle_simulator')
STRAPI_PASSWORD = os.getenv('STRAPI_PASSWORD', 'Ga25w123')

async def test_dispatcher_route_geometry():
    client = StrapiClient(STRAPI_URL, STRAPI_USERNAME, STRAPI_PASSWORD)
    await client.initialize()
    dispatcher = StrapiStrategy(client)
    route_info = await dispatcher.get_route_info('1')
    assert route_info is not None, "RouteInfo should not be None"
    assert route_info.route_name == '1', f"Expected route_name '1', got {route_info.route_name}"
    assert route_info.coordinate_count > 0, "Expected coordinates for route"
    print(f"✅ Dispatcher route geometry test passed. Route: {route_info.route_name}, Coordinates: {route_info.coordinate_count}")
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_dispatcher_route_geometry())
