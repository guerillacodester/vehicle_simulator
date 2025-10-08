"""
Quick test to verify route data is available for visualization
"""
import asyncio
import httpx

async def test_routes():
    async with httpx.AsyncClient() as client:
        # Test routes endpoint
        routes_response = await client.get('http://localhost:1337/api/routes?filters[is_active][$eq]=true')
        routes_data = routes_response.json()
        print(f'Found {len(routes_data.get("data", []))} active routes')
        
        if routes_data.get('data'):
            route = routes_data['data'][0]
            print(f'Route example: {route.get("short_name", "Unknown")} - {route.get("long_name", "No description")}')
            
            # Test route shapes
            route_id = route.get('short_name', '1A')
            shapes_response = await client.get(f'http://localhost:1337/api/route-shapes?filters[route_id][$eq]={route_id}')
            shapes_data = shapes_response.json()
            print(f'Found {len(shapes_data.get("data", []))} shapes for route {route_id}')
            
            if shapes_data.get('data'):
                shape = shapes_data['data'][0]
                print(f'Shape example: {shape.get("shape_id", "Unknown")} with {shape.get("sequence", 0)} points')

if __name__ == "__main__":
    asyncio.run(test_routes())