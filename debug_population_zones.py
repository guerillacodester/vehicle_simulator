import asyncio
import logging
from commuter_service.poisson_geojson_spawner import GeoJSONDataLoader
from commuter_service.strapi_api_client import StrapiApiClient

logging.basicConfig(level=logging.DEBUG)

async def test():
    async with StrapiApiClient() as client:
        loader = GeoJSONDataLoader(client)
        
        # Get zones manually to debug
        country = await client.get_country_by_code('BB')
        zones = await client.get_landuse_zones_by_country(country['id'])
        
        print(f"\nProcessing {len(zones)} zones...")
        for i, zone_data in enumerate(zones[:5]):  # Test first 5
            try:
                from shapely.geometry import shape
                geometry_data = zone_data.get('geometry')
                if not geometry_data:
                    print(f"  Zone {i+1}: NO GEOMETRY")
                    continue
                
                geometry = shape(geometry_data)
                zone_type = zone_data.get('zone_type', 'unknown')
                
                # Check density
                density_map = {
                    'residential': 120.0,
                    'commercial': 34.0,
                    'industrial': 14.0,
                    'mixed': 95.0,
                }
                population_density = density_map.get(zone_type.lower(), 3.0)
                
                area = geometry.area
                base_pop = int(area * 1000000 * population_density)
                
                print(f"  Zone {i+1}:")
                print(f"    Type: {zone_type}")
                print(f"    Density: {population_density}")
                print(f"    Area: {area}")
                print(f"    Base Population: {base_pop}")
                print(f"    Would create zone: {population_density > 0}")
                
            except Exception as e:
                print(f"  Zone {i+1}: ERROR - {e}")

asyncio.run(test())
