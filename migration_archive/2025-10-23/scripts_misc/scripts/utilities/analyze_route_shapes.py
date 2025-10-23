"""
Detailed analysis of route shapes data structure
"""
import asyncio
import httpx
import json

async def analyze_route_shapes():
    async with httpx.AsyncClient() as client:
        # Get route shapes with detailed structure
        shapes_response = await client.get('http://localhost:1337/api/route-shapes?filters[route_id][$eq]=1A')
        print(f"Response status: {shapes_response.status_code}")
        shapes_data = shapes_response.json()
        
        print(f"Response data: {json.dumps(shapes_data, indent=2)[:500]}...")
        
        data = shapes_data.get('data', [])
        print(f"Total shapes for route 1A: {len(data) if data else 0}")
        
        if shapes_data.get('data'):
            print("\n=== First 3 shape points ===")
            for i, shape in enumerate(shapes_data['data'][:3]):
                print(f"\nShape {i+1}:")
                print(f"  ID: {shape.get('id')}")
                print(f"  Shape ID: {shape.get('shape_id')}")
                print(f"  Sequence: {shape.get('sequence')}")
                print(f"  Latitude: {shape.get('shape_pt_lat')}")
                print(f"  Longitude: {shape.get('shape_pt_lon')}")
                print(f"  Distance: {shape.get('shape_dist_traveled', 'N/A')}")
                
        # Also check if there are multiple shape_ids for the route
        unique_shapes = set()
        if shapes_data.get('data'):
            for shape in shapes_data['data']:
                unique_shapes.add(shape.get('shape_id'))
        
        print(f"\nUnique shape_ids for route 1A: {len(unique_shapes)}")
        if unique_shapes:
            print(f"Shape IDs: {list(unique_shapes)[:5]}...")  # Show first 5

if __name__ == "__main__":
    asyncio.run(analyze_route_shapes())