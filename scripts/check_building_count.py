"""Check how many buildings the geospatial service returns for Route 1"""
import asyncio
import httpx

async def check():
    # Get route documentId
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get("http://localhost:1337/api/routes?filters[short_name][$eq]=1")
        data = r.json()
        route_doc_id = data['data'][0]['documentId']
        
        print(f"Route 1 documentId: {route_doc_id}")
        print()
        
        # Get route geometry from geospatial service
        r = await client.get(f"http://localhost:6000/spatial/route-geometry/{route_doc_id}")
        route_geom = r.json()
        route_coords = route_geom.get('coordinates', [])
        
        print(f"Route has {len(route_coords)} coordinate points")
        print()
        
        # Query buildings along route (same as RouteSpawner does)
        # Default spawn_radius is 500m
        from urllib.parse import urlencode
        
        # Simplified - just get buildings within 500m buffer
        print("Querying buildings along route (500m buffer)...")
        
        # The geospatial service endpoint
        # route_spawner uses: geo_client.buildings_along_route()
        # Let me check the actual query

asyncio.run(check())
