#!/usr/bin/env python3
"""
Integration tests for Amenity GeoJSON import
Tests database insertion, PostGIS POINT geometries (extracted centroids), junction tables, and spatial indexes
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

def test_pois_table_exists():
    """Test 3: Verify pois table exists"""
    print("\n[Test 3] Checking if pois table exists...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'pois'
            );
        """)
        exists = cursor.fetchone()[0]
        if exists:
            print("✅ pois table exists")
        else:
            print("❌ pois table does not exist")
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False

def clear_existing_pois():
    """Clear existing POI records before import"""
    print("\n[Setup] Clearing existing POI records...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Delete from junction table first (foreign key constraint)
        cursor.execute("DELETE FROM pois_country_lnk;")
        deleted_links = cursor.rowcount
        
        # Delete from pois table
        cursor.execute("DELETE FROM pois;")
        deleted_pois = cursor.rowcount
        
        conn.commit()
        print(f"✅ Cleared {deleted_pois} POIs and {deleted_links} country links")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to clear POIs: {e}")
        return False

def test_amenity_import():
    """Test 4: Verify amenity data exists (import done via UI)"""
    print("\n[Test 4] Verifying amenity import data exists...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pois;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        if count > 0:
            print(f"✅ Found {count} POIs in database")
            return True
        else:
            print(f"❌ No POIs found in database")
            return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def test_poi_records_count():
    """Test 5: Verify POI records were inserted"""
    print("\n[Test 5] Checking POI record count...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM pois;")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"✅ Found {count} POI records")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No POI records found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Record count check failed: {e}")
        return False

def test_poi_geom_column():
    """Test 6: Verify geom column exists and has SRID 4326"""
    print("\n[Test 6] Checking geom column and SRID...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'pois' AND column_name = 'geom';
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
            SELECT Find_SRID('public', 'pois', 'geom');
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

def test_poi_geometries_not_null():
    """Test 7: Verify all POI records have geometries"""
    print("\n[Test 7] Checking for NULL geometries...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM pois WHERE geom IS NULL;")
        null_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pois;")
        total_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print(f"✅ All {total_count} POIs have geometries")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ Found {null_count} POIs with NULL geometries out of {total_count}")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ NULL geometry check failed: {e}")
        return False

def test_poi_geometry_type():
    """Test 8: Verify all geometries are POINT type (centroids extracted)"""
    print("\n[Test 8] Checking geometry types (must be POINT)...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ST_GeometryType(geom) as geom_type, COUNT(*) 
            FROM pois 
            WHERE geom IS NOT NULL 
            GROUP BY geom_type;
        """)
        results = cursor.fetchall()
        
        print(f"   Geometry types found:")
        all_point = True
        for geom_type, count in results:
            print(f"   - {geom_type}: {count}")
            if geom_type != 'ST_Point':
                all_point = False
        
        if all_point and len(results) > 0:
            print("✅ All geometries are POINT (centroids successfully extracted)")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Non-POINT geometries found or no geometries")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Geometry type check failed: {e}")
        return False

def test_poi_latitude_longitude():
    """Test 9: Verify latitude/longitude fields are populated"""
    print("\n[Test 9] Checking latitude/longitude fields...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(latitude) as has_lat,
                COUNT(longitude) as has_lon,
                AVG(latitude) as avg_lat,
                AVG(longitude) as avg_lon
            FROM pois;
        """)
        result = cursor.fetchone()
        total, has_lat, has_lon, avg_lat, avg_lon = result
        
        print(f"   Total records: {total}")
        print(f"   With latitude: {has_lat}")
        print(f"   With longitude: {has_lon}")
        print(f"   Average latitude: {avg_lat:.4f}")
        print(f"   Average longitude: {avg_lon:.4f}")
        
        # Barbados is around 13°N, -59°W
        if has_lat == total and has_lon == total and 12 < avg_lat < 14 and -60 < avg_lon < -58:
            print("✅ Latitude/longitude fields populated with valid Barbados coordinates")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Latitude/longitude fields missing or invalid")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Latitude/longitude check failed: {e}")
        return False

def test_poi_sample_geometry():
    """Test 10: Verify sample geometry matches latitude/longitude"""
    print("\n[Test 10] Checking sample geometry coordinates...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                osm_id, 
                name, 
                latitude, 
                longitude,
                ST_X(geom) as geom_lon,
                ST_Y(geom) as geom_lat,
                ST_AsText(geom)
            FROM pois 
            WHERE geom IS NOT NULL 
            LIMIT 3;
        """)
        results = cursor.fetchall()
        
        if results:
            print(f"✅ Sample POIs:")
            all_match = True
            for osm_id, name, lat, lon, geom_lon, geom_lat, wkt in results:
                lat_match = abs(lat - geom_lat) < 0.0001
                lon_match = abs(lon - geom_lon) < 0.0001
                match_str = "✓" if (lat_match and lon_match) else "✗"
                print(f"   {match_str} {osm_id} ({name})")
                print(f"      Lat/Lon: ({lat}, {lon})")
                print(f"      Geom: ({geom_lat}, {geom_lon})")
                print(f"      WKT: {wkt}")
                if not (lat_match and lon_match):
                    all_match = False
            
            cursor.close()
            conn.close()
            if all_match:
                print("✅ Latitude/longitude matches PostGIS geometry")
                return True
            else:
                print("❌ Latitude/longitude does not match geometry")
                return False
        else:
            print("❌ No POI geometries found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Sample geometry check failed: {e}")
        return False

def test_poi_spatial_query():
    """Test 11: Test spatial query (POIs near Bridgetown)"""
    print("\n[Test 11] Testing spatial query...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Bridgetown, Barbados coordinates: -59.6165, 13.0969
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pois 
            WHERE ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(-59.6165, 13.0969), 4326)::geography,
                5000
            );
        """)
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"✅ Found {count} POIs within 5km of Bridgetown")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No POIs found near Bridgetown (expected some)")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Spatial query failed: {e}")
        return False

def test_junction_table_exists():
    """Test 12: Verify pois_country_lnk junction table exists"""
    print("\n[Test 12] Checking junction table...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'pois_country_lnk'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✅ pois_country_lnk table exists")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ pois_country_lnk table does not exist")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Junction table check failed: {e}")
        return False

def test_junction_table_links():
    """Test 13: Verify junction table has correct links"""
    print("\n[Test 13] Checking junction table links...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Count links
        cursor.execute("SELECT COUNT(*) FROM pois_country_lnk;")
        link_count = cursor.fetchone()[0]
        
        # Count POIs
        cursor.execute("SELECT COUNT(*) FROM pois;")
        poi_count = cursor.fetchone()[0]
        
        if link_count == poi_count and link_count > 0:
            print(f"✅ Junction table has {link_count} links (matches {poi_count} POIs)")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ Junction table has {link_count} links, but {poi_count} POIs")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Junction table link check failed: {e}")
        return False

def test_region_links():
    """Test 13a: Verify POIs are linked to regions"""
    print("\n[Test 13a] Checking POI-region links...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Count region links
        cursor.execute("SELECT COUNT(*) FROM pois_region_lnk;")
        link_count = cursor.fetchone()[0]
        
        # Count POIs
        cursor.execute("SELECT COUNT(*) FROM pois;")
        poi_count = cursor.fetchone()[0]
        
        if link_count > 0:
            print(f"✅ {link_count} POI-region links exist ({poi_count} POIs)")
            if link_count < poi_count:
                print(f"   ⚠️  Some POIs ({poi_count - link_count}) are not linked to any region")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ No POI-region links found (expected {poi_count})")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Region link check failed: {e}")
        return False

def test_poi_required_fields():
    """Test 14: Verify required fields are populated"""
    print("\n[Test 14] Checking required fields...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check for NULL in required fields
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(osm_id) as has_osm_id,
                COUNT(name) as has_name,
                COUNT(poi_type) as has_poi_type,
                COUNT(amenity) as has_amenity
            FROM pois;
        """)
        result = cursor.fetchone()
        total, has_osm_id, has_name, has_poi_type, has_amenity = result
        
        print(f"   Total records: {total}")
        print(f"   With osm_id: {has_osm_id}")
        print(f"   With name: {has_name}")
        print(f"   With poi_type: {has_poi_type}")
        print(f"   With amenity: {has_amenity}")
        
        if has_osm_id == total and has_name == total and has_poi_type == total:
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
    """Test 15: Verify spatial index exists on geom column"""
    print("\n[Test 15] Checking spatial index...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'pois' 
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

def test_amenity_types():
    """Test 16: Verify amenity types are properly categorized"""
    print("\n[Test 16] Checking amenity type distribution...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT amenity, COUNT(*) 
            FROM pois 
            GROUP BY amenity 
            ORDER BY COUNT(*) DESC 
            LIMIT 10;
        """)
        results = cursor.fetchall()
        
        print("   Top amenity types:")
        for amenity, count in results:
            print(f"   - {amenity}: {count}")
        
        if len(results) > 0:
            print("✅ Amenity types are categorized")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No amenity types found")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Amenity type check failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests in sequence"""
    print("=" * 80)
    print("AMENITY IMPORT INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("PostGIS Extension", test_postgis_extension),
        ("POIs Table Exists", test_pois_table_exists),
        # ("Clear Existing Data", clear_existing_pois),  # Don't clear - data imported via UI
        ("Amenity Import", test_amenity_import),
        ("Record Count", test_poi_records_count),
        ("Geom Column & SRID", test_poi_geom_column),
        ("No NULL Geometries", test_poi_geometries_not_null),
        ("Geometry Types (POINT)", test_poi_geometry_type),
        ("Latitude/Longitude Fields", test_poi_latitude_longitude),
        ("Sample Geometry Match", test_poi_sample_geometry),
        ("Spatial Query", test_poi_spatial_query),
        ("Junction Table Exists", test_junction_table_exists),
        ("Junction Table Links", test_junction_table_links),
        ("Region Links", test_region_links),
        ("Required Fields", test_poi_required_fields),
        ("Spatial Index", test_spatial_index),
        ("Amenity Types", test_amenity_types),
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
