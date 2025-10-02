#!/usr/bin/env python3
"""
Analyze Route Shapes and Shapes Data - The Missing Geometry Tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json

def analyze_shapes_tables():
    """Analyze the shapes and route_shapes tables"""
    print("🗺️  ANALYZING ROUTE GEOMETRY TABLES")
    print("=" * 60)
    
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Analyze SHAPES table
        print("\n--- SHAPES TABLE ---")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'shapes' 
            ORDER BY ordinal_position
        """)
        shapes_columns = cursor.fetchall()
        
        print(f"Columns ({len(shapes_columns)}):")
        for col in shapes_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  - {col['column_name']}: {col['data_type']} {nullable}")
        
        # Get sample shapes data
        cursor.execute("SELECT * FROM shapes LIMIT 3")
        shapes_samples = cursor.fetchall()
        
        print(f"\nSample records ({len(shapes_samples)}):")
        for i, shape in enumerate(shapes_samples, 1):
            print(f"\nShape {i}:")
            for key, value in shape.items():
                display_value = str(value)
                if len(display_value) > 100:
                    display_value = display_value[:97] + "..."
                print(f"  {key}: {display_value}")
        
        # Analyze ROUTE_SHAPES table
        print(f"\n--- ROUTE_SHAPES TABLE ---")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'route_shapes' 
            ORDER BY ordinal_position
        """)
        route_shapes_columns = cursor.fetchall()
        
        print(f"Columns ({len(route_shapes_columns)}):")
        for col in route_shapes_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  - {col['column_name']}: {col['data_type']} {nullable}")
        
        # Get sample route_shapes data
        cursor.execute("SELECT * FROM route_shapes LIMIT 5")
        route_shapes_samples = cursor.fetchall()
        
        print(f"\nSample records ({len(route_shapes_samples)}):")
        for i, rs in enumerate(route_shapes_samples, 1):
            print(f"\nRoute-Shape {i}:")
            for key, value in rs.items():
                print(f"  {key}: {value}")
        
        # Get relationship analysis
        print(f"\n--- RELATIONSHIP ANALYSIS ---")
        cursor.execute("""
            SELECT 
                r.short_name,
                r.long_name,
                COUNT(rs.shape_id) as shape_count
            FROM routes r
            LEFT JOIN route_shapes rs ON r.route_id = rs.route_id
            GROUP BY r.route_id, r.short_name, r.long_name
            ORDER BY r.short_name
        """)
        route_shape_counts = cursor.fetchall()
        
        print("Routes and their shape counts:")
        for rsc in route_shape_counts:
            print(f"  Route {rsc['short_name']} ({rsc['long_name']}): {rsc['shape_count']} shapes")
        
        conn.close()
        return shapes_columns, shapes_samples, route_shapes_columns, route_shapes_samples
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None
        
    finally:
        tunnel.stop()

def check_strapi_geometry_endpoints():
    """Check what geometry-related endpoints exist in Strapi"""
    print(f"\n🔍 CHECKING STRAPI GEOMETRY ENDPOINTS")
    print("=" * 60)
    
    endpoints_to_check = [
        'shapes',
        'route-shapes', 
        'geometries',
        'coordinates',
        'paths'
    ]
    
    existing_endpoints = []
    
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(f'http://localhost:1337/api/{endpoint}')
            if response.status_code == 200:
                data = response.json()
                count = len(data['data'])
                print(f"✅ /{endpoint} - {count} records")
                existing_endpoints.append(endpoint)
            else:
                print(f"❌ /{endpoint} - Not found ({response.status_code})")
        except Exception as e:
            print(f"❌ /{endpoint} - Error: {e}")
    
    return existing_endpoints

if __name__ == "__main__":
    shapes_cols, shapes_data, rs_cols, rs_data = analyze_shapes_tables()
    existing_endpoints = check_strapi_geometry_endpoints()
    
    print(f"\n🎯 SUMMARY")
    print("=" * 60)
    if shapes_cols and rs_cols:
        print(f"✅ Found geometry data in remote database:")
        print(f"   - shapes: {len(shapes_cols)} columns")
        print(f"   - route_shapes: {len(rs_cols)} columns")
        
        if existing_endpoints:
            print(f"✅ Found Strapi endpoints: {existing_endpoints}")
            print("🚀 Ready to create geometry migration!")
        else:
            print("⚠️  No Strapi geometry endpoints found")
            print("💡 Need to create Strapi content types for geometry data")
    else:
        print("❌ Could not analyze geometry tables")