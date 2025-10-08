"""
Get the actual shape points with coordinates
"""
import asyncio
import httpx
import json

async def get_shape_points():
    async with httpx.AsyncClient() as client:
        # First get the shape IDs for route 1A
        route_shapes_response = await client.get('http://localhost:1337/api/route-shapes?filters[route_id][$eq]=1A')
        route_shapes_data = route_shapes_response.json()
        
        if route_shapes_data.get('data'):
            shape_id = route_shapes_data['data'][0]['shape_id']
            print(f"Getting points for shape_id: {shape_id}")
            
            # Now get the actual shape points
            shapes_response = await client.get(f'http://localhost:1337/api/shapes?filters[shape_id][$eq]={shape_id}')
            shapes_data = shapes_response.json()
            
            print(f"Response status: {shapes_response.status_code}")
            
            if shapes_data.get('data'):
                print(f"Found {len(shapes_data['data'])} shape points")
                
                # Show first few points with coordinates
                for i, point in enumerate(shapes_data['data'][:5]):
                    print(f"\nPoint {i+1}:")
                    print(f"  Shape ID: {point.get('shape_id')}")
                    print(f"  Sequence: {point.get('shape_pt_sequence')}")
                    print(f"  Latitude: {point.get('shape_pt_lat')}")
                    print(f"  Longitude: {point.get('shape_pt_lon')}")
                    print(f"  Distance: {point.get('shape_dist_traveled')}")
            else:
                print("No shape points found")
                print(f"Response: {json.dumps(shapes_data, indent=2)}")
        else:
            print("No route shapes found")

if __name__ == "__main__":
    asyncio.run(get_shape_points())