"""
Check for other routes that might go to Speightstown or investigate route naming
"""
import asyncio
import httpx

async def find_speightstown_routes():
    async with httpx.AsyncClient() as client:
        print("=== SEARCHING FOR SPEIGHTSTOWN ROUTES ===\n")
        
        # Get ALL routes to see if there are variants
        routes_response = await client.get('http://localhost:1337/api/routes?pagination[pageSize]=100')
        routes_data = routes_response.json()
        
        print(f"Found {len(routes_data.get('data', []))} total routes:")
        
        speightstown_candidates = []
        
        for route in routes_data.get('data', []):
            route_name = route.get('short_name', 'Unknown')
            route_desc = route.get('long_name', 'No description')
            is_active = route.get('is_active', False)
            
            print(f"  {route_name}: {route_desc} (Active: {is_active})")
            
            # Check if description mentions Speightstown
            if 'speight' in route_desc.lower() or 'speight' in route_name.lower():
                speightstown_candidates.append(route)
            
            # Check if it's a 1A variant
            if '1a' in route_name.lower() or route_name.startswith('1'):
                speightstown_candidates.append(route)
        
        print(f"\n=== POTENTIAL SPEIGHTSTOWN ROUTES ===")
        for route in speightstown_candidates:
            print(f"Route {route.get('short_name')}: {route.get('long_name')}")
            
            # Check this route's shapes
            shapes_response = await client.get(f'http://localhost:1337/api/route-shapes?filters[route_id][$eq]={route.get("short_name")}')
            shapes_data = shapes_response.json()
            
            if shapes_data.get('data'):
                for shape_record in shapes_data['data']:
                    shape_id = shape_record['shape_id']
                    
                    # Check geographic extent of this shape
                    coords_response = await client.get(f'http://localhost:1337/api/shapes?filters[shape_id][$eq]={shape_id}&pagination[pageSize]=1000')
                    coords_data = coords_response.json()
                    
                    if coords_data.get('data'):
                        points = coords_data['data']
                        lats = [p['shape_pt_lat'] for p in points]
                        max_lat = max(lats) if lats else 0
                        
                        print(f"  Shape {shape_id[:20]}... - Max lat: {max_lat:.6f}")
                        if max_lat > 13.35:
                            print(f"    ✅ THIS REACHES SPEIGHTSTOWN AREA!")
                        else:
                            print(f"    ❌ Does not reach Speightstown")
        
        # Also check if there are shapes not linked to any route
        print(f"\n=== CHECKING FOR UNLINKED SHAPES ===")
        all_shapes_response = await client.get('http://localhost:1337/api/shapes?pagination[pageSize]=10')
        all_shapes_data = all_shapes_response.json()
        
        if all_shapes_data.get('data'):
            unique_shape_ids = set()
            for shape in all_shapes_data['data']:
                unique_shape_ids.add(shape['shape_id'])
            
            print(f"Found {len(unique_shape_ids)} unique shape_ids in shapes table")
            
            # Check a few random ones for northern extent
            sample_shapes = list(unique_shape_ids)[:5]
            for shape_id in sample_shapes:
                coords_response = await client.get(f'http://localhost:1337/api/shapes?filters[shape_id][$eq]={shape_id}&pagination[pageSize]=1000')
                coords_data = coords_response.json()
                
                if coords_data.get('data'):
                    points = coords_data['data']
                    lats = [p['shape_pt_lat'] for p in points]
                    max_lat = max(lats) if lats else 0
                    
                    print(f"Shape {shape_id[:20]}... - {len(points)} points, Max lat: {max_lat:.6f}")

if __name__ == "__main__":
    asyncio.run(find_speightstown_routes())