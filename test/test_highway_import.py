#!/usr/bin/env python3
"""
Integration tests for Highway GeoJSON import
Tests database insertion, PostGIS geometries, junction tables, and spatial indexes
"""

import requests
import psycopg2
import time

# Configuration
BASE_URL = "http://localhost:1337"
COUNTRY_ID = "bbzlsqe7n5fz6b8g25m4mtvj"  # Barbados document ID
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

def test_highways_table_exists():
    """Test 3: Verify highways table exists"""
    print("\n[Test 3] Checking if highways table exists...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'highways'
            );
        """)
        exists = cursor.fetchone()[0]
        if exists:
            print("✅ highways table exists")
        else:
            print("❌ highways table does not exist")
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False

def clear_existing_highways():
    """Clear existing highway records before import"""
    print("\n[Setup] Clearing existing highway records...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Delete from junction table first (foreign key constraint)
        cursor.execute("DELETE FROM highways_country_lnk;")
        deleted_links = cursor.rowcount
        
        # Delete from highways table
        cursor.execute("DELETE FROM highways;")
        deleted_highways = cursor.rowcount
        
        conn.commit()
        print(f"✅ Cleared {deleted_highways} highways and {deleted_links} country links")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to clear highways: {e}")
        return False

def test_highway_import():
    """Test 4: Execute highway import via API"""
    print("\n[Test 4] Executing highway import...")
    try:
        url = f"{BASE_URL}/api/geojson-import/import-highway"
        payload = {"countryId": COUNTRY_ID}
        
        print(f"Calling: POST {url}")
        print(f"Payload: {payload}")
        
        response = requests.post(url, json=payload, timeout=600)  # 10 minute timeout for large file
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Import successful!")
            print(f"   Total features: {data.get('result', {}).get('totalFeatures', 'N/A')}")
            print(f"   Total batches: {data.get('result', {}).get('totalBatches', 'N/A')}")
            print(f"   Elapsed time: {data.get('result', {}).get('elapsedSeconds', 'N/A')}s")
            print(f"   Features/sec: {data.get('result', {}).get('featuresPerSecond', 'N/A')}")
            return True
        else:
            print(f"❌ Import failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Import request failed: {e}")
        return False

def test_highway_records_count():
    """Test 5: Verify highway records were inserted"""
    print("\n[Test 5] Checking highway record count...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = cursor.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM highways;")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"✅ Found {count} highway records")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No highway records found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Record count check failed: {e}")
        return False

def test_highway_geom_column():
    """Test 6: Verify geom column exists and has SRID 4326"""
    print("\n[Test 6] Checking geom column and SRID...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'highways' AND column_name = 'geom';
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
            SELECT Find_SRID('public', 'highways', 'geom');
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

def test_highway_geometries_not_null():
    """Test 7: Verify all highway records have geometries"""
    print("\n[Test 7] Checking for NULL geometries...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM highways WHERE geom IS NULL;")
        null_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM highways;")
        total_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print(f"✅ All {total_count} highways have geometries")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ Found {null_count} highways with NULL geometries out of {total_count}")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ NULL geometry check failed: {e}")
        return False

def test_highway_geometry_type():
    """Test 8: Verify all geometries are LineString type"""
    print("\n[Test 8] Checking geometry types...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ST_GeometryType(geom) as geom_type, COUNT(*) 
            FROM highways 
            WHERE geom IS NOT NULL 
            GROUP BY geom_type;
        """)
        results = cursor.fetchall()
        
        print(f"   Geometry types found:")
        all_linestring = True
        for geom_type, count in results:
            print(f"   - {geom_type}: {count}")
            if geom_type != 'ST_LineString':
                all_linestring = False
        
        if all_linestring and len(results) > 0:
            print("✅ All geometries are LineString")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Non-LineString geometries found or no geometries")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Geometry type check failed: {e}")
        return False

def test_highway_sample_geometry():
    """Test 9: Verify sample geometry has valid coordinates"""
    print("\n[Test 9] Checking sample geometry coordinates...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT highway_id, name, ST_AsText(geom), ST_NumPoints(geom)
            FROM highways 
            WHERE geom IS NOT NULL 
            LIMIT 1;
        """)
        result = cursor.fetchone()
        
        if result:
            highway_id, name, wkt, num_points = result
            print(f"✅ Sample highway: {highway_id} ({name})")
            print(f"   WKT (first 100 chars): {wkt[:100]}...")
            print(f"   Number of points: {num_points}")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No highway geometries found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Sample geometry check failed: {e}")
        return False

def test_highway_spatial_query():
    """Test 10: Test spatial query (point within buffer of highway)"""
    print("\n[Test 10] Testing spatial query...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Bridgetown, Barbados coordinates: -59.6165, 13.0969
        cursor.execute("""
            SELECT COUNT(*) 
            FROM highways 
            WHERE ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(-59.6165, 13.0969), 4326)::geography,
                10000
            );
        """)
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"✅ Found {count} highways within 10km of Bridgetown")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No highways found near Bridgetown (expected some)")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Spatial query failed: {e}")
        return False

def test_junction_table_exists():
    """Test 11: Verify highways_country_lnk junction table exists"""
    print("\n[Test 11] Checking junction table...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'highways_country_lnk'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✅ highways_country_lnk table exists")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ highways_country_lnk table does not exist")
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
        cursor.execute("SELECT COUNT(*) FROM highways_country_lnk;")
        link_count = cursor.fetchone()[0]
        
        # Count highways
        cursor.execute("SELECT COUNT(*) FROM highways;")
        highway_count = cursor.fetchone()[0]
        
        if link_count == highway_count and link_count > 0:
            print(f"✅ Junction table has {link_count} links (matches {highway_count} highways)")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ Junction table has {link_count} links, but {highway_count} highways")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Junction table link check failed: {e}")
        return False

def test_highway_required_fields():
    """Test 13: Verify required fields are populated"""
    print("\n[Test 13] Checking required fields...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check for NULL in required fields
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(highway_id) as has_highway_id,
                COUNT(name) as has_name,
                COUNT(highway_type) as has_highway_type
            FROM highways;
        """)
        result = cursor.fetchone()
        total, has_highway_id, has_name, has_highway_type = result
        
        print(f"   Total records: {total}")
        print(f"   With highway_id: {has_highway_id}")
        print(f"   With name: {has_name}")
        print(f"   With highway_type: {has_highway_type}")
        
        if has_highway_id == total and has_name == total and has_highway_type == total:
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
            WHERE tablename = 'highways' 
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

def test_highway_types():
    """Test 15: Verify highway types are properly categorized"""
    print("\n[Test 15] Checking highway type distribution...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT highway_type, COUNT(*) 
            FROM highways 
            GROUP BY highway_type 
            ORDER BY COUNT(*) DESC 
            LIMIT 10;
        """)
        results = cursor.fetchall()
        
        print("   Top highway types:")
        for highway_type, count in results:
            print(f"   - {highway_type}: {count}")
        
        if len(results) > 0:
            print("✅ Highway types are categorized")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No highway types found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Highway type check failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests in sequence"""
    print("=" * 80)
    print("HIGHWAY IMPORT INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("PostGIS Extension", test_postgis_extension),
        ("Highways Table Exists", test_highways_table_exists),
        ("Clear Existing Data", clear_existing_highways),
        ("Highway Import", test_highway_import),
        ("Record Count", test_highway_records_count),
        ("Geom Column & SRID", test_highway_geom_column),
        ("No NULL Geometries", test_highway_geometries_not_null),
        ("Geometry Types", test_highway_geometry_type),
        ("Sample Geometry", test_highway_sample_geometry),
        ("Spatial Query", test_highway_spatial_query),
        ("Junction Table Exists", test_junction_table_exists),
        ("Junction Table Links", test_junction_table_links),
        ("Required Fields", test_highway_required_fields),
        ("Spatial Index", test_spatial_index),
        ("Highway Types", test_highway_types),
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
