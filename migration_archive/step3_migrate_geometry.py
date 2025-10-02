#!/usr/bin/env python3
"""
Step 3: PostGIS to GTFS Geometry Migration
==========================================
Migrates route geometry data from PostGIS database to Strapi GTFS format.
"""
import psycopg2
import requests
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel

class GeometryMigrator:
    def __init__(self):
        self.tunnel = None
        self.db_connection = None
        
    def setup_ssh_tunnel(self):
        """Setup SSH tunnel to remote database"""
        print("🔐 SETTING UP SSH TUNNEL")
        print("=" * 60)
        
        try:
            self.tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
            self.tunnel.start()
            print(f"✅ SSH tunnel established on local port 6543")
            return True
            
        except Exception as e:
            print(f"❌ SSH tunnel failed: {e}")
            return False
    
    def connect_to_database(self):
        """Connect to PostgreSQL database through SSH tunnel"""
        print("🔌 CONNECTING TO REMOTE DATABASE")
        print("=" * 60)
        
        try:
            self.db_connection = psycopg2.connect(
                host='127.0.0.1',
                port=6543, 
                database='arknettransit',
                user='david',
                password='Ga25w123!'
            )
            
            # Test connection with PostGIS
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT PostGIS_Version();")
            version = cursor.fetchone()[0]
            print(f"✅ Connected to PostgreSQL with PostGIS {version}")
            cursor.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def analyze_geometry_data(self):
        """Analyze the geometry data to be migrated"""
        print("🔍 ANALYZING GEOMETRY DATA")
        print("=" * 60)
        
        cursor = self.db_connection.cursor()
        
        # Count shapes
        cursor.execute("SELECT COUNT(*) FROM shapes")
        shape_count = cursor.fetchone()[0]
        
        # Count route_shapes (relationships)
        cursor.execute("SELECT COUNT(*) FROM route_shapes")
        route_shape_count = cursor.fetchone()[0]
        
        # Get coordinate point count (CORRECTED: column is 'geom' not 'shape_geom')
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT (ST_DumpPoints(geom)).geom 
                FROM shapes 
                WHERE geom IS NOT NULL
            ) AS points
        """)
        total_points = cursor.fetchone()[0]
        
        # Sample data (CORRECTED: column is 'geom' not 'shape_geom')
        cursor.execute("""
            SELECT shape_id, ST_NumPoints(geom) as point_count
            FROM shapes 
            WHERE geom IS NOT NULL 
            ORDER BY shape_id 
            LIMIT 3
        """)
        sample_shapes = cursor.fetchall()
        
        cursor.execute("""
            SELECT route_id, shape_id, variant_code, is_default
            FROM route_shapes 
            ORDER BY route_id, variant_code 
            LIMIT 5
        """)
        sample_relations = cursor.fetchall()
        
        print(f"Data Summary:")
        print(f"  📍 Shapes: {shape_count}")
        print(f"  🔗 Route-Shape Relations: {route_shape_count}")
        print(f"  📊 Total Coordinate Points: {total_points}")
        print()
        print(f"Sample Shapes:")
        for shape_id, points in sample_shapes:
            print(f"  {shape_id}: {points} points")
        print()
        print(f"Sample Route-Shape Relations:")
        for route_id, shape_id, variant, default in sample_relations:
            print(f"  Route {route_id} → Shape {shape_id} (variant: {variant}, default: {default})")
        
        cursor.close()
        return {
            'shapes': shape_count,
            'route_shapes': route_shape_count,
            'total_points': total_points
        }
    
    def extract_shapes_data(self):
        """Extract shapes data with PostGIS to GTFS conversion"""
        print(f"\n📦 EXTRACTING SHAPES DATA (PostGIS → GTFS)")
        print("=" * 60)
        
        cursor = self.db_connection.cursor()
        
        # Extract all shapes with coordinate points (CORRECTED: column is 'geom' not 'shape_geom')
        cursor.execute("""
            SELECT 
                s.shape_id,
                (ST_DumpPoints(s.geom)).path[1] as shape_pt_sequence,
                ST_Y((ST_DumpPoints(s.geom)).geom) as shape_pt_lat,
                ST_X((ST_DumpPoints(s.geom)).geom) as shape_pt_lon
            FROM shapes s
            WHERE s.geom IS NOT NULL
            ORDER BY s.shape_id, shape_pt_sequence
        """)
        
        shapes_data = cursor.fetchall()
        
        print(f"✅ Extracted {len(shapes_data)} coordinate points")
        
        # Group by shape_id for preview
        shapes_grouped = {}
        for shape_id, seq, lat, lon in shapes_data:
            if shape_id not in shapes_grouped:
                shapes_grouped[shape_id] = []
            shapes_grouped[shape_id].append({
                'shape_pt_sequence': seq,
                'shape_pt_lat': float(lat),
                'shape_pt_lon': float(lon)
            })
        
        print(f"📊 Organized into {len(shapes_grouped)} shapes")
        for shape_id, points in list(shapes_grouped.items())[:3]:
            print(f"  {shape_id}: {len(points)} points")
        
        cursor.close()
        return shapes_grouped
    
    def extract_route_shapes_data(self):
        """Extract route-shapes relationship data"""
        print(f"\n🔗 EXTRACTING ROUTE-SHAPES RELATIONSHIPS")
        print("=" * 60)
        
        cursor = self.db_connection.cursor()
        
        cursor.execute("""
            SELECT 
                route_id,
                shape_id,
                variant_code,
                is_default
            FROM route_shapes
            ORDER BY route_id, variant_code
        """)
        
        route_shapes_data = cursor.fetchall()
        
        print(f"✅ Extracted {len(route_shapes_data)} route-shape relationships")
        
        # Preview data (no route_shape_id in source table)
        for i, (route_id, shape_id, variant, default) in enumerate(route_shapes_data[:5]):
            print(f"  Route {route_id} → Shape {shape_id} (variant: {variant}, default: {default})")
        
        if len(route_shapes_data) > 5:
            print(f"  ... and {len(route_shapes_data) - 5} more")
        
        cursor.close()
        return route_shapes_data
    
    def check_strapi_endpoints(self):
        """Check if Strapi endpoints are ready"""
        print(f"\n🔍 CHECKING STRAPI ENDPOINTS")
        print("=" * 60)
        
        endpoints = {
            'shapes': 'http://localhost:1337/api/shapes',
            'route-shapes': 'http://localhost:1337/api/route-shapes'
        }
        
        for name, url in endpoints.items():
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    count = len(response.json()['data'])
                    print(f"✅ {name}: Available ({count} existing records)")
                else:
                    print(f"❌ {name}: Not available (Status: {response.status_code})")
                    return False
            except Exception as e:
                print(f"❌ {name}: Error - {e}")
                return False
        
        return True
    
    def migrate_shapes_to_strapi(self, shapes_data):
        """Migrate shapes data to Strapi"""
        print(f"\n🚀 MIGRATING SHAPES TO STRAPI")
        print("=" * 60)
        
        success_count = 0
        error_count = 0
        
        for shape_id, points in shapes_data.items():
            print(f"Migrating shape {shape_id} ({len(points)} points)...")
            
            for point in points:
                try:
                    payload = {
                        "data": {
                            "shape_id": shape_id,
                            "shape_pt_sequence": point['shape_pt_sequence'],
                            "shape_pt_lat": point['shape_pt_lat'],
                            "shape_pt_lon": point['shape_pt_lon']
                        }
                    }
                    
                    response = requests.post(
                        'http://localhost:1337/api/shapes',
                        headers={'Content-Type': 'application/json'},
                        json=payload
                    )
                    
                    if response.status_code in [200, 201]:
                        success_count += 1
                    else:
                        print(f"  ❌ Failed to create point {point['shape_pt_sequence']}: {response.status_code}")
                        try:
                            error_detail = response.json()
                            print(f"      Error: {error_detail}")
                        except:
                            print(f"      Response: {response.text[:200]}...")
                        error_count += 1
                        
                except Exception as e:
                    print(f"  ❌ Error creating point {point['shape_pt_sequence']}: {e}")
                    error_count += 1
                
                # Small delay between individual point creations
                time.sleep(0.05)
            
            # Brief pause between shapes to avoid overwhelming Strapi
            time.sleep(0.2)
        
        print(f"\n📊 Shapes Migration Results:")
        print(f"  ✅ Success: {success_count} points")
        print(f"  ❌ Errors: {error_count} points")
        
        return success_count, error_count
    
    def migrate_route_shapes_to_strapi(self, route_shapes_data):
        """Migrate route-shapes relationships to Strapi"""
        print(f"\n🔗 MIGRATING ROUTE-SHAPES TO STRAPI")
        print("=" * 60)
        
        success_count = 0
        error_count = 0
        
        for route_id, shape_id, variant_code, is_default in route_shapes_data:
            try:
                # Generate route_shape_id from route_id and shape_id combination
                route_shape_id = f"{route_id}_{shape_id}"
                
                payload = {
                    "data": {
                        "route_shape_id": route_shape_id,
                        "route_id": route_id,
                        "shape_id": shape_id,
                        "variant_code": variant_code,
                        "is_default": is_default
                    }
                }
                
                response = requests.post(
                    'http://localhost:1337/api/route-shapes',
                    headers={'Content-Type': 'application/json'},
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ Migrated route-shape {route_shape_id}: Route {route_id} → Shape {shape_id}")
                    success_count += 1
                else:
                    print(f"❌ Failed to migrate route-shape {route_shape_id}: {response.status_code}")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ Error migrating route-shape {route_shape_id}: {e}")
                error_count += 1
        
        print(f"\n📊 Route-Shapes Migration Results:")
        print(f"  ✅ Success: {success_count} relationships")
        print(f"  ❌ Errors: {error_count} relationships")
        
        return success_count, error_count
    
    def verify_migration(self):
        """Verify the migration results"""
        print(f"\n✅ VERIFYING MIGRATION RESULTS")
        print("=" * 60)
        
        try:
            # Check shapes
            response = requests.get('http://localhost:1337/api/shapes')
            if response.status_code == 200:
                shapes_count = len(response.json()['data'])
                print(f"📍 Shapes in Strapi: {shapes_count}")
            
            # Check route-shapes
            response = requests.get('http://localhost:1337/api/route-shapes')
            if response.status_code == 200:
                route_shapes_count = len(response.json()['data'])
                print(f"🔗 Route-shapes in Strapi: {route_shapes_count}")
            
            # Sample verification
            response = requests.get('http://localhost:1337/api/shapes?pagination[limit]=3')
            if response.status_code == 200:
                sample_shapes = response.json()['data']
                print(f"\nSample migrated shapes:")
                for shape in sample_shapes:
                    attrs = shape['attributes']
                    print(f"  Shape {attrs['shape_id']}: Point {attrs['shape_pt_sequence']} ({attrs['shape_pt_lat']}, {attrs['shape_pt_lon']})")
            
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up connections"""
        if self.db_connection:
            self.db_connection.close()
        if self.tunnel:
            self.tunnel.stop()

def main():
    print("🚀 STEP 3: POSTGIS TO GTFS GEOMETRY MIGRATION")
    print("=" * 80)
    
    migrator = GeometryMigrator()
    
    try:
        # Setup connections
        if not migrator.setup_ssh_tunnel():
            return
        
        if not migrator.connect_to_database():
            return
        
        # Check Strapi readiness
        if not migrator.check_strapi_endpoints():
            print("❌ Strapi endpoints not ready. Complete Step 2 first!")
            return
        
        # Analyze data
        stats = migrator.analyze_geometry_data()
        
        print(f"\n⚠️  MIGRATION SCOPE:")
        print(f"   • {stats['shapes']} shapes to migrate")
        print(f"   • {stats['total_points']} coordinate points to create")
        print(f"   • {stats['route_shapes']} route-shape relationships to create")
        print(f"\n📝 This will create {stats['total_points'] + stats['route_shapes']} total records in Strapi")
        
        # Confirm before proceeding
        confirm = input(f"\nProceed with migration? (y/N): ").lower().strip()
        if confirm != 'y':
            print("Migration cancelled")
            return
        
        # Extract data
        shapes_data = migrator.extract_shapes_data()
        route_shapes_data = migrator.extract_route_shapes_data()
        
        # Migrate shapes first
        shapes_success, shapes_errors = migrator.migrate_shapes_to_strapi(shapes_data)
        
        # Then migrate route-shapes relationships
        rs_success, rs_errors = migrator.migrate_route_shapes_to_strapi(route_shapes_data)
        
        # Final verification
        migrator.verify_migration()
        
        # Summary
        print(f"\n🎉 GEOMETRY MIGRATION COMPLETE!")
        print("=" * 80)
        print(f"Total Success: {shapes_success + rs_success} records")
        print(f"Total Errors: {shapes_errors + rs_errors} records")
        
        if shapes_errors + rs_errors == 0:
            print("✅ 100% SUCCESS - All geometry data migrated!")
        else:
            print(f"⚠️  {shapes_errors + rs_errors} errors occurred - check logs above")
    
    finally:
        migrator.cleanup()

if __name__ == "__main__":
    main()