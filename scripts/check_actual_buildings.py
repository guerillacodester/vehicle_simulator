"""Check actual building count from geospatial service"""
import asyncio
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def check():
    from commuter_service.infrastructure.geospatial.client import GeospatialClient
    
    # Get Route 1 geometry
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:1337/api/routes?filters[short_name][$eq]=1")
        route_doc_id = r.json()['data'][0]['documentId']
        
        r = await client.get(f"http://localhost:6000/spatial/route-geometry/{route_doc_id}")
        route_geom = r.json()
        route_coords = route_geom.get('coordinates', [])
    
    print(f"Route 1 has {len(route_coords)} coordinate points")
    
    # Query buildings using same method as RouteSpawner
    geo_client = GeospatialClient(base_url="http://localhost:6000")
    result = geo_client.buildings_along_route(
        route_coordinates=route_coords,
        buffer_meters=500,
        limit=5000
    )
    
    buildings = result.get('buildings', [])
    print(f"\nGeospatial service returned: {len(buildings)} buildings")
    print(f"Calibrated for: 325 buildings")
    print(f"Ratio: {len(buildings) / 325:.2f}x")
    print()
    print(f"If we keep spatial_base_rate=0.13:")
    print(f"  Expected spawns at peak: {len(buildings) * 0.13:.1f} (WRONG!)")
    print(f"  Should be: 42 route passengers")
    print()
    print(f"Corrected spatial_base_rate should be:")
    print(f"  {42 / len(buildings):.6f} passengers/building/hour")

asyncio.run(check())
