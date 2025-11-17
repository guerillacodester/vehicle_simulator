import asyncio
import os
import logging
from arknet_transit_simulator.services.strapi_client import StrapiClient
from arknet_transit_simulator.services.config_service import ConfigurationService

logging.basicConfig(level=logging.INFO)

STRAPI_URL = os.getenv('STRAPI_URL', 'http://localhost:1337')
STRAPI_USERNAME = os.getenv('STRAPI_USERNAME', 'vehicle_simulator')
STRAPI_PASSWORD = os.getenv('STRAPI_PASSWORD', 'Ga25w123')

async def test_config_service():
    client = StrapiClient(STRAPI_URL, STRAPI_USERNAME, STRAPI_PASSWORD)
    await client.initialize()
    print(f"Login status: {'Authenticated' if client._token else 'Failed'}")
    print(f"JWT token: {client._token}")
    config_service = ConfigurationService(strapi_client=client)
    await config_service.initialize()
    print(f"Loaded {len(config_service._flat_cache)} config parameters.")
    # Print a sample config value if available
    if config_service._flat_cache:
        sample_key = next(iter(config_service._flat_cache))
        print(f"Sample config: {sample_key} = {config_service._flat_cache[sample_key]}")
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_config_service())
