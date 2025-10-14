"""
Comprehensive analysis of Route 1A shape points - checking for completeness
"""
import asyncio
import httpx
import json

async def analyze_complete_route_1a():
    async with httpx.AsyncClient() as client:
        print("=== ROUTE 1A COMPLETE ANALYSIS ===\n")
        
        # Get all route shapes for 1A (there might be multiple shape_ids)
        route_shapes_response = await client.get('http://localhost:1337/api/route-shapes?filters[route_id][$eq]=1A')
        route_shapes_data = route_shapes_response.json()
        
        print(f"Found {len(route_shapes_data.get('data', []))} shape records for Route 1A:")
        
        all_shape_ids = []
        for shape_record in route_shapes_data.get('data', []):
            shape_id = shape_record['shape_id']
            is_default = shape_record.get('is_default', False)
            variant = shape_record.get('variant_code', 'None')
            print(f"  - Shape ID: {shape_id[:20]}... (Default: {is_default}, Variant: {variant})")
            all_shape_ids.append(shape_id)
        
        print(f"\n=== ANALYZING ALL SHAPE POINTS ===")
        
        total_points = 0
        min_lat, max_lat = 999, -999
        min_lon, max_lon = 999, -999
        
        for i, shape_id in enumerate(all_shape_ids):
            print(f"\nShape {i+1}: {shape_id[:20]}...")
            
            # Get all points for this shape_id
            shapes_response = await client.get(
                f'http://localhost:1337/api/shapes?filters[shape_id][$eq]={shape_id}&sort=shape_pt_sequence&pagination[pageSize]=1000'
            )
            shapes_data = shapes_response.json()
            
            points = shapes_data.get('data', [])
            if points:
                print(f"  Points: {len(points)}")
                print(f"  Sequence range: {points[0].get('shape_pt_sequence')} to {points[-1].get('shape_pt_sequence')}")
                
                # Check geographic bounds
                shape_lats = [p['shape_pt_lat'] for p in points if p.get('shape_pt_lat')]
                shape_lons = [p['shape_pt_lon'] for p in points if p.get('shape_pt_lon')]
                
                if shape_lats and shape_lons:
                    shape_min_lat, shape_max_lat = min(shape_lats), max(shape_lats)
                    shape_min_lon, shape_max_lon = min(shape_lons), max(shape_lons)
                    
                    print(f"  Lat range: {shape_min_lat:.6f} to {shape_max_lat:.6f}")
                    print(f"  Lon range: {shape_min_lon:.6f} to {shape_max_lon:.6f}")
                    
                    # Update overall bounds
                    min_lat = min(min_lat, shape_min_lat)
                    max_lat = max(max_lat, shape_max_lat)
                    min_lon = min(min_lon, shape_min_lon)
                    max_lon = max(max_lon, shape_max_lon)
                    
                    # Check if this reaches Speightstown area (northern Barbados ~13.35+ latitude)
                    if shape_max_lat > 13.35:
                        print(f"  ✅ This shape reaches northern area (Speightstown region)")
                    else:
                        print(f"  ❌ This shape does NOT reach Speightstown (max lat: {shape_max_lat:.6f})")
                
                total_points += len(points)
                
                # Show first and last few points
                print(f"  First point: ({points[0].get('shape_pt_lat'):.6f}, {points[0].get('shape_pt_lon'):.6f})")
                print(f"  Last point:  ({points[-1].get('shape_pt_lat'):.6f}, {points[-1].get('shape_pt_lon'):.6f})")
            else:
                print(f"  ❌ NO POINTS FOUND!")
        
        print(f"\n=== SUMMARY ===")
        print(f"Total shapes: {len(all_shape_ids)}")
        print(f"Total points: {total_points}")
        print(f"Overall lat range: {min_lat:.6f} to {max_lat:.6f}")
        print(f"Overall lon range: {min_lon:.6f} to {max_lon:.6f}")
        
        # Speightstown is approximately at 13.35 latitude
        if max_lat > 13.35:
            print(f"✅ Route data DOES reach Speightstown area (max lat: {max_lat:.6f})")
        else:
            print(f"❌ Route data does NOT reach Speightstown! (max lat: {max_lat:.6f})")
            print(f"   Speightstown should be around 13.35+ latitude")

if __name__ == "__main__":
    asyncio.run(analyze_complete_route_1a())