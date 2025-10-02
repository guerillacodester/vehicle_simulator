#!/usr/bin/env python3
"""
LIMITED GEOMETRY MIGRATION TEST
==============================
Test migration with just 1 shape to validate the approach.
"""
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json

def test_single_shape_migration():
    """Test migration of just one shape to validate approach"""
    print("🧪 LIMITED GEOMETRY MIGRATION TEST")
    print("=" * 60)
    
    # Setup SSH tunnel
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=6543, 
            database='arknettransit',
            user='david',
            password='Ga25w123!'
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("📦 EXTRACTING ONE SHAPE FOR TESTING")
        print("-" * 40)
        
        # Get the smallest shape for testing
        cursor.execute("""
            SELECT 
                s.shape_id,
                ST_NumPoints(s.geom) as point_count
            FROM shapes s
            WHERE s.geom IS NOT NULL
            ORDER BY ST_NumPoints(s.geom) ASC
            LIMIT 1
        """)
        
        smallest_shape = cursor.fetchone()
        test_shape_id = smallest_shape['shape_id']
        point_count = smallest_shape['point_count']
        
        print(f"Selected shape: {test_shape_id} ({point_count} points)")
        
        # Extract coordinate points for this shape
        cursor.execute("""
            SELECT 
                s.shape_id,
                (ST_DumpPoints(s.geom)).path[1] as shape_pt_sequence,
                ST_Y((ST_DumpPoints(s.geom)).geom) as shape_pt_lat,
                ST_X((ST_DumpPoints(s.geom)).geom) as shape_pt_lon
            FROM shapes s
            WHERE s.shape_id = %s AND s.geom IS NOT NULL
            ORDER BY shape_pt_sequence
        """, (test_shape_id,))
        
        points = cursor.fetchall()
        print(f"Extracted {len(points)} coordinate points")
        
        # Show first few points
        print(f"\nSample points:")
        for i, point in enumerate(points[:3]):
            print(f"  Point {point['shape_pt_sequence']}: ({point['shape_pt_lat']}, {point['shape_pt_lon']})")
        
        print(f"\n🚀 MIGRATING TO STRAPI")
        print("-" * 40)
        
        success_count = 0
        error_count = 0
        
        for point in points:
            try:
                payload = {
                    "data": {
                        "shape_id": str(point['shape_id']),
                        "shape_pt_sequence": point['shape_pt_sequence'],
                        "shape_pt_lat": float(point['shape_pt_lat']),
                        "shape_pt_lon": float(point['shape_pt_lon'])
                    }
                }
                
                response = requests.post(
                    'http://localhost:1337/api/shapes',
                    headers={'Content-Type': 'application/json'},
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ Point {point['shape_pt_sequence']}: SUCCESS")
                    success_count += 1
                else:
                    print(f"❌ Point {point['shape_pt_sequence']}: FAILED ({response.status_code})")
                    try:
                        error_detail = response.json()
                        print(f"   Error: {error_detail}")
                    except:
                        print(f"   Response: {response.text[:100]}...")
                    error_count += 1
                
                # Small delay between requests
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Point {point['shape_pt_sequence']}: ERROR - {e}")
                error_count += 1
        
        print(f"\n📊 TEST RESULTS")
        print("-" * 40)
        print(f"✅ Success: {success_count}/{len(points)} points")
        print(f"❌ Errors: {error_count}/{len(points)} points")
        
        if error_count == 0:
            print("🎉 PERFECT! Ready for full migration")
        else:
            print("⚠️  Issues found - need to investigate")
        
        # Check what's in Strapi now
        response = requests.get('http://localhost:1337/api/shapes')
        if response.status_code == 200:
            total_shapes = len(response.json()['data'])
            print(f"📊 Total shapes in Strapi: {total_shapes}")
        
        cursor.close()
        conn.close()
        
    finally:
        tunnel.stop()

if __name__ == "__main__":
    test_single_shape_migration()