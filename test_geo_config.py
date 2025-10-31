from pathlib import Path
import configparser

# Simulate the routes.py config loading
config = configparser.ConfigParser()
config_path = Path('geospatial_service/api/routes.py').parent.parent.parent / 'config.ini'
print(f'Config path: {config_path}')
print(f'Exists: {config_path.exists()}')
config.read(config_path, encoding='utf-8')
strapi_url = config.get('infrastructure', 'strapi_url', fallback='NOT FOUND')
print(f'Strapi URL: {strapi_url}')

# Try direct request
import httpx
import asyncio

async def test():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f'{strapi_url}/api/routes?pagination[pageSize]=1')
            print(f'Request status: {r.status_code}')
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(test())
