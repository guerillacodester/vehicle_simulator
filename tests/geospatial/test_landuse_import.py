#!/usr/bin/env python3
"""
Integration tests for Landuse GeoJSON import
Tests database insertion, PostGIS POLYGON/MULTIPOLYGON geometries, junction tables, and spatial indexes
"""

import requests
import psycopg2
import time

# Configuration
BASE_URL = "http://localhost:1337"
COUNTRY_ID = "y5qsd8a1it9bfxmlpg6gvt4c"  # Barbados document ID
DB_CONFIG = {
    'host': 'localhost',
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}

def test_database_connection():
    """Test 1: Verify database connection"""
    print("\n[Test 1] Testing database connection...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        print(f"✅ Database connected: {db_version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_postgis_extension():
    """Test 2: Verify PostGIS extension is installed"""
    print("\n[Test 2] Checking PostGIS extension...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT PostGIS_version();")
        postgis_version = cursor.fetchone()[0]
        print(f"✅ PostGIS installed: {postgis_version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ PostGIS check failed: {e}")
        return False

def test_landuse_zones_table_exists():
    """Test 3: Verify landuse_zones table exists"""
    print("\n[Test 3] Checking if landuse_zones table exists...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'landuse_zones'
            );
        """)
        exists = cursor.fetchone()[0]
        if exists:
            print("✅ landuse_zones table exists")
        else:
            print("❌ landuse_zones table does not exist")
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False

def clear_existing_zones():
    """Clear existing landuse zone records before import"""
    print("\n[Setup] Clearing existing landuse zone records...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Delete from junction table first (foreign key constraint)
        cursor.execute("DELETE FROM landuse_zones_country_lnk;")
        deleted_links = cursor.rowcount
        
        # Delete from landuse_zones table
        cursor.execute("DELETE FROM landuse_zones;")
        deleted_zones = cursor.rowcount
        
        conn.commit()
        print(f"✅ Cleared {deleted_zones} zones and {deleted_links} country links")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to clear zones: {e}")
        return False

def test_landuse_import():
    """Test 4: Verify landuse data exists (import done via UI)"""
    print("\n[Test 4] Verifying landuse import data exists...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM landuse_zones;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        if count > 0:
            print(f"✅ Found {count} landuse zones in database")
            return True
        else:
            print(f"❌ No landuse zones found in database")
            return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def test_zone_records_count():
    """Test 5: Verify landuse zone records were inserted"""
    print("\n[Test 5] Checking landuse zone record count...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM landuse_zones;")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"✅ Found {count} landuse zone records")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No landuse zone records found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Record count check failed: {e}")
        return False

def test_zone_geom_column():
    """Test 6: Verify geom column exists and has SRID 4326"""
    print("\n[Test 6] Checking geom column and SRID...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'landuse_zones' AND column_name = 'geom';
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"✅ geom column exists (type: {result[1]})")
        else:
            print("❌ geom column not found")
            cursor.close()
            conn.close()
            return False
        
        # Check SRID
        cursor.execute("""
            SELECT Find_SRID('public', 'landuse_zones', 'geom');
        """)
        srid = cursor.fetchone()[0]
        
        if srid == 4326:
            print(f"✅ SRID is 4326")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ SRID is {srid}, expected 4326")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Geom column check failed: {e}")
        return False

def test_zone_geometries_not_null():
    """Test 7: Verify all zone records have geometries"""
    print("\n[Test 7] Checking for NULL geometries...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM landuse_zones WHERE geom IS NULL;")
        null_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM landuse_zones;")
        total_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print(f"✅ All {total_count} zones have geometries")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ Found {null_count} zones with NULL geometries out of {total_count}")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ NULL geometry check failed: {e}")
        return False

def test_zone_geometry_type():
    """Test 8: Verify all geometries are Polygon or MultiPolygon"""
    print("\n[Test 8] Checking geometry types...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ST_GeometryType(geom) as geom_type, COUNT(*) 
            FROM landuse_zones 
            WHERE geom IS NOT NULL 
            GROUP BY geom_type;
        """)
        results = cursor.fetchall()
        
        print(f"   Geometry types found:")
        valid_types = True
        for geom_type, count in results:
            print(f"   - {geom_type}: {count}")
            if geom_type not in ['ST_Polygon', 'ST_MultiPolygon']:
                valid_types = False
        
        if valid_types and len(results) > 0:
            print("✅ All geometries are Polygon or MultiPolygon")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Invalid geometry types found or no geometries")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Geometry type check failed: {e}")
        return False

def test_zone_sample_geometry():
    """Test 9: Verify sample geometry has valid coordinates"""
    print("\n[Test 9] Checking sample geometry coordinates...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                osm_id, 
                name, 
                ST_GeometryType(geom) as geom_type,
                ST_AsText(geom) as wkt,
                ST_Area(geom::geography) as area_sqm,
                ST_NPoints(geom) as num_points
            FROM landuse_zones 
            WHERE geom IS NOT NULL 
            LIMIT 3;
        """)
        results = cursor.fetchall()
        
        if results:
            print(f"✅ Sample zones:")
            for osm_id, name, geom_type, wkt, area_sqm, num_points in results:
                print(f"   - {osm_id} ({name})")
                print(f"     Type: {geom_type}")
                print(f"     WKT (first 80 chars): {wkt[:80]}...")
                print(f"     Area: {area_sqm:.2f} sqm")
                print(f"     Points: {num_points}")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No zone geometries found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Sample geometry check failed: {e}")
        return False

def test_zone_spatial_query():
    """Test 10: Test spatial query (zones containing Bridgetown)"""
    print("\n[Test 10] Testing spatial query...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Bridgetown, Barbados coordinates: -59.6165, 13.0969
        cursor.execute("""
            SELECT COUNT(*) 
            FROM landuse_zones 
            WHERE ST_Contains(
                geom,
                ST_SetSRID(ST_MakePoint(-59.6165, 13.0969), 4326)
            );
        """)
        contains_count = cursor.fetchone()[0]
        
        # Also check zones within 5km
        cursor.execute("""
            SELECT COUNT(*) 
            FROM landuse_zones 
            WHERE ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(-59.6165, 13.0969), 4326)::geography,
                5000
            );
        """)
        nearby_count = cursor.fetchone()[0]
        
        print(f"   Zones containing Bridgetown point: {contains_count}")
        print(f"   Zones within 5km of Bridgetown: {nearby_count}")
        
        if nearby_count > 0:
            print(f"✅ Spatial queries work correctly")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No zones found near Bridgetown (expected some)")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Spatial query failed: {e}")
        return False

def test_junction_table_exists():
    """Test 11: Verify landuse_zones_country_lnk junction table exists"""
    print("\n[Test 11] Checking junction table...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'landuse_zones_country_lnk'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✅ landuse_zones_country_lnk table exists")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ landuse_zones_country_lnk table does not exist")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Junction table check failed: {e}")
        return False

def test_junction_table_links():
    """Test 12: Verify junction table has correct links"""
    print("\n[Test 12] Checking junction table links...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Count links
        cursor.execute("SELECT COUNT(*) FROM landuse_zones_country_lnk;")
        link_count = cursor.fetchone()[0]
        
        # Count zones
        cursor.execute("SELECT COUNT(*) FROM landuse_zones;")
        zone_count = cursor.fetchone()[0]
        
        if link_count == zone_count and link_count > 0:
            print(f"✅ Junction table has {link_count} links (matches {zone_count} zones)")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ Junction table has {link_count} links, but {zone_count} zones")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Junction table link check failed: {e}")
        return False

def test_region_links():
    """Test 12a: Verify landuse zones are linked to regions"""
    print("\n[Test 12a] Checking zone-region links...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Count region links
        cursor.execute("SELECT COUNT(*) FROM landuse_zones_region_lnk;")
        link_count = cursor.fetchone()[0]
        
        # Count zones
        cursor.execute("SELECT COUNT(*) FROM landuse_zones;")
        zone_count = cursor.fetchone()[0]
        
        if link_count > 0:
            print(f"✅ {link_count} zone-region links exist ({zone_count} zones)")
            if link_count > zone_count:
                crossing = link_count - zone_count
                print(f"   ℹ️  {crossing} zones cross parish boundaries")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ No zone-region links found (expected {zone_count})")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Region link check failed: {e}")
        return False

def test_zone_required_fields():
    """Test 13: Verify required fields are populated"""
    print("\n[Test 13] Checking required fields...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check for NULL in required fields
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(osm_id) as has_osm_id,
                COUNT(name) as has_name,
                COUNT(zone_type) as has_zone_type
            FROM landuse_zones;
        """)
        result = cursor.fetchone()
        total, has_osm_id, has_name, has_zone_type = result
        
        print(f"   Total records: {total}")
        print(f"   With osm_id: {has_osm_id}")
        print(f"   With name: {has_name}")
        print(f"   With zone_type: {has_zone_type}")
        
        if has_osm_id == total and has_name == total and has_zone_type == total:
            print("✅ All required fields are populated")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Some required fields are NULL")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Required fields check failed: {e}")
        return False

def test_spatial_index():
    """Test 14: Verify spatial index exists on geom column"""
    print("\n[Test 14] Checking spatial index...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'landuse_zones' 
            AND indexdef LIKE '%USING gist%';
        """)
        indexes = cursor.fetchall()
        
        if len(indexes) > 0:
            print(f"✅ Found {len(indexes)} GIST spatial index(es):")
            for idx in indexes:
                print(f"   - {idx[0]}")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No GIST spatial indexes found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Spatial index check failed: {e}")
        return False

def test_landuse_types():
    """Test 15: Verify landuse types are properly categorized"""
    print("\n[Test 15] Checking landuse type distribution...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT zone_type, COUNT(*) 
            FROM landuse_zones 
            GROUP BY zone_type 
            ORDER BY COUNT(*) DESC 
            LIMIT 10;
        """)
        results = cursor.fetchall()
        
        print("   Top landuse types:")
        for zone_type, count in results:
            print(f"   - {zone_type}: {count}")
        
        if len(results) > 0:
            print("✅ Landuse types are categorized")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No landuse types found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Landuse type check failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests in sequence"""
    print("=" * 80)
    print("LANDUSE IMPORT INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("PostGIS Extension", test_postgis_extension),
        ("Landuse Zones Table Exists", test_landuse_zones_table_exists),
        # ("Clear Existing Data", clear_existing_zones),  # Don't clear - data imported via UI
        ("Landuse Import", test_landuse_import),
        ("Record Count", test_zone_records_count),
        ("Geom Column & SRID", test_zone_geom_column),
        ("No NULL Geometries", test_zone_geometries_not_null),
        ("Geometry Types", test_zone_geometry_type),
        ("Sample Geometry", test_zone_sample_geometry),
        ("Spatial Query", test_zone_spatial_query),
        ("Junction Table Exists", test_junction_table_exists),
        ("Junction Table Links", test_junction_table_links),
        ("Region Links", test_region_links),
        ("Required Fields", test_zone_required_fields),
        ("Spatial Index", test_spatial_index),
        ("Landuse Types", test_landuse_types),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            failed += 1
        
        # Small delay between tests
        time.sleep(0.5)
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
