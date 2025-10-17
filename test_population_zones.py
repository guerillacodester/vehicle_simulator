import asyncio
from commuter_service.poisson_geojson_spawner import GeoJSONDataLoader
from commuter_service.strapi_api_client import StrapiApiClient

async def test():
    async with StrapiApiClient() as client:
        loader = GeoJSONDataLoader(client)
        success = await loader.load_geojson_data('bb')  # Use 2-letter country code
        
        print(f"\n{'='*80}")
        print(f"GeoJSON Data Loading Test - After Fix")
        print(f"{'='*80}")
        print(f"Load successful: {success}")
        print(f"Population zones created: {len(loader.population_zones)}")
        print(f"Amenity zones created: {len(loader.amenity_zones)}")
        print(f"Transport hubs created: {len(loader.transport_hubs)}")
        
        if loader.population_zones:
            print(f"\n{'='*80}")
            print(f"Sample Population Zones (first 5):")
            print(f"{'='*80}")
            for i, zone in enumerate(loader.population_zones[:5]):
                print(f"\nZone {i+1}:")
                print(f"  ID: {zone.zone_id}")
                print(f"  Type: {zone.zone_type}")
                print(f"  Base Population: {zone.base_population:,}")
                print(f"  Spawn Rate/Hour: {zone.spawn_rate_per_hour:.2f}")
                print(f"  Center: {zone.center_point}")
                print(f"  Peak Hours: {zone.peak_hours}")
        
        print(f"\n{'='*80}")
        print(f"Zone Type Distribution:")
        print(f"{'='*80}")
        zone_types = {}
        for zone in loader.population_zones:
            zone_types[zone.zone_type] = zone_types.get(zone.zone_type, 0) + 1
        for ztype, count in sorted(zone_types.items()):
            print(f"  {ztype}: {count} zones")

asyncio.run(test())
