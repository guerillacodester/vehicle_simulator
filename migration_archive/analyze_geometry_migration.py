#!/usr/bin/env python3
"""
Complete Route Geometry Migration - PostGIS to GTFS Format
===========================================================
Converts PostGIS geometry data to GTFS-format coordinate points.

CONVERSION:
- Remote: PostGIS binary geometry (single record per shape)
- Strapi: GTFS points (multiple lat/lon records per shape)

MISSING CONTENT TYPES NEEDED:
- route-shapes (links routes to shapes)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json
import struct

def convert_postgis_to_coordinates(geom_binary):
    """Convert PostGIS binary geometry to lat/lon coordinate list"""
    try:
        # PostGIS geometry is in WKB (Well-Known Binary) format
        # This is a simplified parser for LINESTRING geometries
        
        if not geom_binary:
            return []
        
        # Convert to hex string for easier parsing
        hex_data = geom_binary.hex() if isinstance(geom_binary, bytes) else geom_binary
        
        # Basic WKB parsing (simplified)
        # This is a placeholder - you'd need proper WKB parsing library
        # For now, return empty coordinates and log the issue
        
        print(f"⚠️  PostGIS geometry conversion needed (WKB: {len(hex_data)} chars)")
        return []
        
    except Exception as e:
        print(f"❌ Error converting geometry: {e}")
        return []

def analyze_geometry_conversion():
    """Analyze what we need to convert PostGIS to GTFS"""
    print("🔍 ANALYZING GEOMETRY CONVERSION REQUIREMENTS")
    print("=" * 60)
    
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get geometry as text format for analysis
        print("📊 Analyzing PostGIS geometry format...")
        cursor.execute("""
            SELECT 
                shape_id,
                ST_AsText(geom) as geom_text,
                ST_NumPoints(geom) as point_count,
                ST_SRID(geom) as srid
            FROM shapes 
            LIMIT 3
        """)
        
        geometry_analysis = cursor.fetchall()
        
        print(f"\nFound {len(geometry_analysis)} geometry samples:")
        total_points = 0
        
        for geom in geometry_analysis:
            print(f"\nShape ID: {geom['shape_id']}")
            print(f"  Points: {geom['point_count']}")
            print(f"  SRID: {geom['srid']}")
            print(f"  Preview: {geom['geom_text'][:100]}...")
            total_points += geom['point_count']
        
        print(f"\n📈 Conversion Requirements:")
        print(f"  - {len(geometry_analysis)} shapes to convert")
        print(f"  - ~{total_points} coordinate points total")
        print(f"  - Format: PostGIS LINESTRING → GTFS points")
        
        # Analyze route-shapes relationships
        print(f"\n🔗 Route-Shape Relationships:")
        cursor.execute("""
            SELECT 
                r.short_name,
                rs.variant_code,
                rs.is_default,
                COUNT(*) as shape_count
            FROM routes r
            JOIN route_shapes rs ON r.route_id = rs.route_id
            GROUP BY r.route_id, r.short_name, rs.variant_code, rs.is_default
            ORDER BY r.short_name, rs.is_default DESC
        """)
        
        relationships = cursor.fetchall()
        for rel in relationships:
            default_text = " (DEFAULT)" if rel['is_default'] else ""
            variant_text = f" variant:{rel['variant_code']}" if rel['variant_code'] else ""
            print(f"  Route {rel['short_name']}{variant_text}: {rel['shape_count']} shapes{default_text}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        tunnel.stop()

def check_postgis_functions():
    """Check if we can extract coordinates from PostGIS"""
    print(f"\n🧪 TESTING POSTGIS COORDINATE EXTRACTION")
    print("=" * 60)
    
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test coordinate extraction
        print("🔍 Extracting coordinate points from PostGIS...")
        cursor.execute("""
            SELECT 
                s.shape_id,
                (ST_DumpPoints(s.geom)).path[1] as point_sequence,
                ST_Y((ST_DumpPoints(s.geom)).geom) as latitude,
                ST_X((ST_DumpPoints(s.geom)).geom) as longitude
            FROM shapes s
            WHERE s.shape_id = (SELECT shape_id FROM shapes LIMIT 1)
            ORDER BY (ST_DumpPoints(s.geom)).path[1]
            LIMIT 10
        """)
        
        coordinate_points = cursor.fetchall()
        
        if coordinate_points:
            print(f"✅ Successfully extracted {len(coordinate_points)} coordinate points!")
            print(f"\nSample coordinates for shape {coordinate_points[0]['shape_id']}:")
            
            for i, point in enumerate(coordinate_points[:5]):
                print(f"  Point {point['point_sequence']}: ({point['latitude']:.6f}, {point['longitude']:.6f})")
            
            if len(coordinate_points) > 5:
                print(f"  ... and {len(coordinate_points) - 5} more points")
            
            return True
        else:
            print("❌ No coordinate points extracted")
            return False
        
        conn.close()
        
    except Exception as e:
        print(f"❌ PostGIS extraction failed: {e}")
        return False
        
    finally:
        tunnel.stop()

def estimate_migration_scope():
    """Estimate the full scope of geometry migration"""
    print(f"\n📊 ESTIMATING FULL MIGRATION SCOPE")
    print("=" * 60)
    
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total point count across all shapes
        cursor.execute("""
            SELECT 
                COUNT(*) as total_shapes,
                SUM(ST_NumPoints(geom)) as total_coordinate_points
            FROM shapes
        """)
        
        totals = cursor.fetchone()
        
        # Get route-shapes count
        cursor.execute("SELECT COUNT(*) as total_route_shapes FROM route_shapes")
        route_shapes_count = cursor.fetchone()['total_route_shapes']
        
        print(f"Migration Requirements:")
        print(f"  📍 Shapes: {totals['total_shapes']} → Convert to {totals['total_coordinate_points']} GTFS points")
        print(f"  🔗 Route-Shapes: {route_shapes_count} relationship records")
        print(f"  📝 Total Strapi records to create: {totals['total_coordinate_points'] + route_shapes_count}")
        
        print(f"\n⚠️  CRITICAL ISSUES TO RESOLVE:")
        print(f"  1. 🏗️  Create 'route-shapes' content type in Strapi")
        print(f"  2. 🔄 Convert PostGIS → GTFS coordinate format")
        print(f"  3. 🗺️  Migrate {totals['total_coordinate_points']} coordinate points")
        print(f"  4. 🔗 Migrate {route_shapes_count} route-shape relationships")
        
        conn.close()
        return totals['total_coordinate_points'], route_shapes_count
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0, 0
        
    finally:
        tunnel.stop()

if __name__ == "__main__":
    print("🗺️  ROUTE GEOMETRY MIGRATION ANALYSIS")
    print("=" * 80)
    
    # Step 1: Analyze conversion requirements
    if analyze_geometry_conversion():
        
        # Step 2: Test PostGIS coordinate extraction
        if check_postgis_functions():
            
            # Step 3: Estimate full migration scope
            points, relationships = estimate_migration_scope()
            
            print(f"\n🎯 NEXT STEPS REQUIRED:")
            print(f"=" * 80)
            print(f"1. 🏗️  Create 'route-shapes' content type in Strapi admin")
            print(f"2. 🔄 Create PostGIS → GTFS migration script")
            print(f"3. 🚀 Run geometry migrations:")
            print(f"   - Shapes: {points} coordinate points")
            print(f"   - Route-Shapes: {relationships} relationships")
            
        else:
            print(f"\n❌ Cannot extract coordinates from PostGIS")
            
    else:
        print(f"\n❌ Geometry analysis failed")