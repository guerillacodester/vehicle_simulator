"""
Count all points in Route 1A across all shape segments
"""
import asyncio
import httpx

async def count_all_route_1a_points():
    async with httpx.AsyncClient() as client:
        print("=== COUNTING ALL ROUTE 1A POINTS ===\n")
        
        # Get all route shapes for 1A
        route_shapes_response = await client.get('http://localhost:1337/api/route-shapes?filters[route_id][$eq]=1A')
        route_shapes_data = route_shapes_response.json()
        
        total_points = 0
        shape_details = []
        
        print(f"Found {len(route_shapes_data.get('data', []))} shape segments for Route 1A:\n")
        
        for i, shape_record in enumerate(route_shapes_data.get('data', [])):
            shape_id = shape_record['shape_id']
            is_default = shape_record.get('is_default', False)
            
            # Get all points for this shape_id
            shapes_response = await client.get(
                f'http://localhost:1337/api/shapes?filters[shape_id][$eq]={shape_id}&pagination[pageSize]=1000'
            )
            shapes_data = shapes_response.json()
            
            points = shapes_data.get('data', [])
            point_count = len(points)
            total_points += point_count
            
            print(f"Shape {i+1}: {shape_id}")
            print(f"  Points: {point_count}")
            print(f"  Default: {is_default}")
            
            if points:
                # Get sequence range
                sequences = [p.get('shape_pt_sequence', 0) for p in points]
                min_seq, max_seq = min(sequences), max(sequences)
                print(f"  Sequence: {min_seq} to {max_seq}")
                
                # Get coordinate bounds
                lats = [p['shape_pt_lat'] for p in points]
                lons = [p['shape_pt_lon'] for p in points]
                print(f"  Lat range: {min(lats):.6f} to {max(lats):.6f}")
                print(f"  Lon range: {min(lons):.6f} to {max(lons):.6f}")
            
            print()
            
            shape_details.append({
                'shape_id': shape_id,
                'points': point_count,
                'is_default': is_default
            })
        
        print("=" * 50)
        print(f"📊 TOTAL POINTS IN ROUTE 1A: {total_points}")
        print("=" * 50)
        
        # Summary by type
        default_points = sum(s['points'] for s in shape_details if s['is_default'])
        non_default_points = sum(s['points'] for s in shape_details if not s['is_default'])
        
        print(f"\nBreakdown:")
        print(f"  Default shapes: {default_points} points")
        print(f"  Non-default shapes: {non_default_points} points")
        print(f"  Total shapes: {len(shape_details)}")
        
        if total_points == 0:
            print("\n❌ NO POINTS FOUND! This indicates a data problem.")
        else:
            print(f"\n✅ Found {total_points} total coordinate points for Route 1A")

if __name__ == "__main__":
    asyncio.run(count_all_route_1a_points())