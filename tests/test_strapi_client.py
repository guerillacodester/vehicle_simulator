import asyncio
import os
import logging
from arknet_transit_simulator.services.strapi_client import StrapiClient, AuthenticationError

logging.basicConfig(level=logging.INFO)

STRAPI_URL = os.getenv('STRAPI_URL', 'http://localhost:1337')
STRAPI_USERNAME = os.getenv('STRAPI_USERNAME', 'vehicle_simulator')
STRAPI_PASSWORD = os.getenv('STRAPI_PASSWORD', 'Ga25w123')

async def test_authentication():
    client = StrapiClient(STRAPI_URL, STRAPI_USERNAME, STRAPI_PASSWORD)
    await client.initialize()
    assert client._token is not None, "JWT token should not be None after authentication"
    print("✅ Authentication test passed.")
    await client.close()

async def test_get_route_geometry():
    client = StrapiClient(STRAPI_URL, STRAPI_USERNAME, STRAPI_PASSWORD)
    await client.initialize()
    data = await client.get('/api/routes/1/geometry')
    assert 'routeName' in data, "routeName should be in response"
    print(f"✅ Route geometry test passed. Route: {data['routeName']}")
    await client.close()

async def main():
    try:
        await test_authentication()
        await test_get_route_geometry()
        print("All StrapiClient tests passed.")
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
