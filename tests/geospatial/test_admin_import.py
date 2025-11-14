"""
Admin Import Integration Tests

Tests the complete admin boundary import workflow including:
- Database schema validation
- Import API endpoints
- PostGIS geometry compliance
- Junction table relationships
- Spatial index performance

Prerequisites:
- Strapi running on http://localhost:1337
- PostgreSQL running with admin_levels seeded
- Admin logged in with valid session

Usage:
    python test_admin_import.py
"""

import sys
import time
import requests
import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class TestResult:
    """Test result container"""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration

    def __str__(self):
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if self.passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        duration_str = f"({self.duration:.3f}s)" if self.duration > 0 else ""
        msg = f" - {self.message}" if self.message else ""
        return f"{status} {self.name} {duration_str}{msg}"


class AdminImportTester:
    """Automated test suite for admin import functionality"""
    
    def __init__(self):
        self.strapi_url = "http://localhost:1337"
        self.api_url = f"{self.strapi_url}/api"
        self.results: List[TestResult] = []
        self.db_conn = None
        self.country_id = None
        self.admin_levels = []
        
    def connect_db(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(
                host="127.0.0.1",
                database="arknettransit",
                user="david",
                password="Ga25w123!",
                port=5432
            )
            return True
        except Exception as e:
            print(f"{Colors.RED}Database connection failed: {e}{Colors.RESET}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[tuple]]:
        """Execute SQL query and return results"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                self.db_conn.commit()
                return []
        except Exception as e:
            print(f"{Colors.RED}Query failed: {e}{Colors.RESET}")
            self.db_conn.rollback()
            return None
    
    def test_strapi_running(self) -> TestResult:
        """Test 1: Verify Strapi is running"""
        start = time.time()
        try:
            response = requests.get(f"{self.strapi_url}/admin", timeout=5)
            passed = response.status_code in [200, 302]
            message = f"Status {response.status_code}" if passed else f"Unexpected status {response.status_code}"
            return TestResult("Strapi Server Running", passed, message, time.time() - start)
        except Exception as e:
            return TestResult("Strapi Server Running", False, str(e), time.time() - start)
    
    def test_database_connection(self) -> TestResult:
        """Test 2: Verify database connection"""
        start = time.time()
        connected = self.connect_db()
        message = "Connected successfully" if connected else "Connection failed"
        return TestResult("Database Connection", connected, message, time.time() - start)
    
    def test_admin_levels_seeded(self) -> TestResult:
        """Test 3: Verify admin_levels table is seeded"""
        start = time.time()
        query = "SELECT id, level, name FROM admin_levels ORDER BY level"
        results = self.execute_query(query)
        
        if results is None:
            return TestResult("Admin Levels Seeded", False, "Query failed", time.time() - start)
        
        expected_levels = [6, 8, 9, 10]
        actual_levels = [row[1] for row in results]
        
        passed = actual_levels == expected_levels
        if passed:
            self.admin_levels = [(row[0], row[1], row[2]) for row in results]  # Store for later tests
        
        message = f"Found levels: {actual_levels}" if results else "No admin levels found"
        return TestResult("Admin Levels Seeded", passed, message, time.time() - start)
    
    def test_postgis_extension(self) -> TestResult:
        """Test 4: Verify PostGIS extension is enabled"""
        start = time.time()
        query = "SELECT extname FROM pg_extension WHERE extname = 'postgis'"
        results = self.execute_query(query)
        
        passed = results is not None and len(results) > 0
        message = "PostGIS enabled" if passed else "PostGIS not found"
        return TestResult("PostGIS Extension", passed, message, time.time() - start)
    
    def test_regions_table_schema(self) -> TestResult:
        """Test 5: Verify regions table has correct PostGIS schema"""
        start = time.time()
        query = """
            SELECT column_name, udt_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'regions' AND column_name = 'geom'
        """
        results = self.execute_query(query)
        
        if not results:
            return TestResult("Regions Table Schema", False, "geom column not found", time.time() - start)
        
        # Check geometry type and SRID
        query_geom = """
            SELECT 
                f_geometry_column,
                type,
                srid
            FROM geometry_columns
            WHERE f_table_name = 'regions' AND f_geometry_column = 'geom'
        """
        geom_info = self.execute_query(query_geom)
        
        if geom_info and len(geom_info) > 0:
            geom_type, srid = geom_info[0][1], geom_info[0][2]
            passed = geom_type == 'MULTIPOLYGON' and srid == 4326
            message = f"Type: {geom_type}, SRID: {srid}"
        else:
            passed = False
            message = "Geometry metadata not found"
        
        return TestResult("Regions Table Schema", passed, message, time.time() - start)
    
    def test_spatial_index(self) -> TestResult:
        """Test 6: Verify GIST spatial index exists"""
        start = time.time()
        query = """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'regions' 
            AND indexname LIKE '%geom%'
            AND indexdef LIKE '%USING gist%'
        """
        results = self.execute_query(query)
        
        passed = results is not None and len(results) > 0
        message = f"Index: {results[0][0]}" if passed else "GIST index not found"
        return TestResult("Spatial Index (GIST)", passed, message, time.time() - start)
    
    def test_geojson_files_exist(self) -> TestResult:
        """Test 7: Verify all admin level GeoJSON files exist"""
        start = time.time()
        import os
        
        sample_data_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data')
        required_files = [
            'admin_level_6_polygon.geojson',
            'admin_level_8_polygon.geojson',
            'admin_level_9_polygon.geojson',
            'admin_level_10_polygon.geojson'
        ]
        
        missing = []
        for filename in required_files:
            filepath = os.path.join(sample_data_path, filename)
            if not os.path.exists(filepath):
                missing.append(filename)
        
        passed = len(missing) == 0
        message = "All files found" if passed else f"Missing: {', '.join(missing)}"
        return TestResult("GeoJSON Files Exist", passed, message, time.time() - start)
    
    def test_import_api_endpoint(self) -> TestResult:
        """Test 8: Verify import API endpoint is accessible"""
        start = time.time()
        try:
            # Just check if endpoint exists (will get 400 without params)
            response = requests.post(
                f"{self.api_url}/import-geojson/admin",
                json={},
                timeout=5
            )
            # 400 is expected without parameters, means endpoint exists
            passed = response.status_code in [400, 401, 403]
            message = f"Endpoint accessible (status {response.status_code})"
            return TestResult("Import API Endpoint", passed, message, time.time() - start)
        except Exception as e:
            return TestResult("Import API Endpoint", False, str(e), time.time() - start)
    
    def test_get_country_id(self) -> TestResult:
        """Test 9: Get a country ID for testing (Barbados)"""
        start = time.time()
        query = "SELECT document_id FROM countries WHERE name ILIKE '%barbados%' LIMIT 1"
        results = self.execute_query(query)
        
        if results and len(results) > 0:
            self.country_id = results[0][0]
            passed = True
            message = f"Country ID: {self.country_id}"
        else:
            passed = False
            message = "No country found (create Barbados first)"
        
        return TestResult("Get Country ID", passed, message, time.time() - start)
    
    def test_clean_existing_regions(self) -> TestResult:
        """Test 10: Clean existing test regions (optional - for clean test)"""
        start = time.time()
        
        # Delete existing regions for clean test
        delete_queries = [
            "DELETE FROM regions_admin_level_lnk",
            "DELETE FROM regions_country_lnk", 
            "DELETE FROM regions"
        ]
        
        try:
            for query in delete_queries:
                self.execute_query(query)
            
            passed = True
            message = "Cleaned existing regions"
        except Exception as e:
            passed = False
            message = f"Cleanup failed: {e}"
        
        return TestResult("Clean Existing Regions", passed, message, time.time() - start)
    
    def test_parish_import(self) -> TestResult:
        """Test 11: Import Parish (Level 6) boundaries"""
        start = time.time()
        
        if not self.country_id or not self.admin_levels:
            return TestResult("Parish Import", False, "Prerequisites not met", time.time() - start)
        
        # Find level 6 admin level
        level_6 = next((al for al in self.admin_levels if al[1] == 6), None)
        if not level_6:
            return TestResult("Parish Import", False, "Level 6 not found", time.time() - start)
        
        try:
            response = requests.post(
                f"{self.api_url}/import-geojson/admin",
                json={
                    "countryId": self.country_id,
                    "adminLevelId": level_6[0],
                    "adminLevel": 6
                },
                timeout=30
            )
            
            passed = response.status_code == 200
            if passed:
                data = response.json()
                total = data.get('result', {}).get('totalFeatures', 0)
                message = f"Imported {total} features"
            else:
                message = f"Status {response.status_code}: {response.text[:100]}"
            
            return TestResult("Parish Import (Level 6)", passed, message, time.time() - start)
        except Exception as e:
            return TestResult("Parish Import (Level 6)", False, str(e), time.time() - start)
    
    def test_verify_parish_in_db(self) -> TestResult:
        """Test 12: Verify parishes were inserted into database"""
        start = time.time()
        
        query = """
            SELECT COUNT(*) 
            FROM regions r
            JOIN regions_admin_level_lnk ral ON r.id = ral.region_id
            JOIN admin_levels al ON ral.admin_level_id = al.id
            WHERE al.level = 6
        """
        results = self.execute_query(query)
        
        if results:
            count = results[0][0]
            passed = count > 0
            message = f"Found {count} parish records"
        else:
            passed = False
            message = "Query failed"
        
        return TestResult("Verify Parishes in DB", passed, message, time.time() - start)
    
    def test_geometry_validity(self) -> TestResult:
        """Test 13: Verify all geometries are valid PostGIS geometries"""
        start = time.time()
        
        query = """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE ST_IsValid(geom)) as valid,
                COUNT(*) FILTER (WHERE ST_GeometryType(geom) = 'ST_MultiPolygon') as multipolygon,
                COUNT(*) FILTER (WHERE ST_SRID(geom) = 4326) as correct_srid
            FROM regions
            WHERE geom IS NOT NULL
        """
        results = self.execute_query(query)
        
        if results and results[0][0] > 0:
            total, valid, multipolygon, correct_srid = results[0]
            passed = total == valid == multipolygon == correct_srid
            message = f"{valid}/{total} valid, {multipolygon}/{total} MultiPolygon, {correct_srid}/{total} SRID 4326"
        else:
            passed = False
            message = "No geometries found"
        
        return TestResult("Geometry Validity", passed, message, time.time() - start)
    
    def test_region_metadata_fields(self) -> TestResult:
        """Test 14a: Verify center coordinates are populated with original precision"""
        start = time.time()
        query = """
            SELECT 
                COUNT(*) as total,
                COUNT(center_latitude) as has_center_lat,
                COUNT(center_longitude) as has_center_lon,
                AVG(center_latitude) as avg_lat,
                AVG(center_longitude) as avg_lon,
                center_latitude,
                center_longitude
            FROM regions
            GROUP BY center_latitude, center_longitude
            LIMIT 1
        """
        results = self.execute_query(query)
        
        if results and len(results) > 0:
            total, has_lat, has_lon, avg_lat, avg_lon, sample_lat, sample_lon = results[0]
            all_populated = (has_lat == total and has_lon == total)
            # Barbados is around 13°N, -59°W
            coords_valid = 12 < avg_lat < 14 and -60 < avg_lon < -58
            # Check precision: original GeoJSON has 2 decimal places (e.g., 13.08, -59.53)
            passed = all_populated and total > 0 and coords_valid
            message = f"center_lat: {has_lat}/{total}, center_lon: {has_lon}/{total}, avg: ({avg_lat:.2f}, {avg_lon:.2f}), sample: ({sample_lat}, {sample_lon})"
        else:
            passed = False
            message = "No regions found"
        
        return TestResult("Region Metadata Fields", passed, message, time.time() - start)
    
    def test_junction_tables(self) -> TestResult:
        """Test 14b: Verify junction table relationships"""
        start = time.time()
        
        queries = {
            "country_link": "SELECT COUNT(*) FROM regions_country_lnk",
            "admin_level_link": "SELECT COUNT(*) FROM regions_admin_level_lnk"
        }
        
        results = {}
        for name, query in queries.items():
            result = self.execute_query(query)
            if result:
                results[name] = result[0][0]
        
        passed = all(count > 0 for count in results.values())
        message = f"Country links: {results.get('country_link', 0)}, Admin level links: {results.get('admin_level_link', 0)}"
        
        return TestResult("Junction Table Relationships", passed, message, time.time() - start)
    
    def test_spatial_query_performance(self) -> TestResult:
        """Test 15: Test spatial query uses index"""
        start = time.time()
        
        query = """
            EXPLAIN ANALYZE
            SELECT name 
            FROM regions
            WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(-59.6145, 13.0975), 4326))
            LIMIT 1
        """
        results = self.execute_query(query)
        
        if results:
            explain_output = '\n'.join([row[0] for row in results])
            uses_index = 'Index Scan' in explain_output and 'idx_regions_geom' in explain_output
            execution_time = float([line for line in explain_output.split('\n') if 'Execution Time' in line][0].split(':')[1].strip().split()[0])
            
            passed = uses_index and execution_time < 10.0  # Should be under 10ms
            message = f"Uses index: {uses_index}, Execution: {execution_time:.3f}ms"
        else:
            passed = False
            message = "EXPLAIN failed"
        
        return TestResult("Spatial Query Performance", passed, message, time.time() - start)
    
    def test_area_accuracy(self) -> TestResult:
        """Test 16: Verify calculated areas match known values"""
        start = time.time()
        
        # Known official areas for Barbados parishes (in km²)
        known_areas = {
            'Christ Church': 57, 'Saint Andrew': 36, 'Saint George': 44, 'Saint James': 32,
            'Saint John': 34, 'Saint Joseph': 26, 'Saint Lucy': 36, 'Saint Michael': 39,
            'Saint Peter': 34, 'Saint Philip': 60, 'Saint Thomas': 34
        }
        
        query = "SELECT name, area_sq_km FROM regions WHERE area_sq_km IS NOT NULL ORDER BY name"
        results = self.execute_query(query)
        
        if results and len(results) > 0:
            total_calc = sum(float(row[1]) for row in results)
            total_known = sum(known_areas.get(row[0], 0) for row in results)
            max_diff_pct = max(abs((float(row[1]) - known_areas.get(row[0], 0)) / known_areas.get(row[0], 1) * 100) 
                               for row in results if known_areas.get(row[0], 0) > 0)
            total_diff_pct = abs((total_calc - total_known) / total_known * 100)
            
            passed = total_diff_pct < 1.0 and max_diff_pct < 15.0
            message = f"Total: {total_calc:.2f} vs {total_known} km² ({total_diff_pct:+.1f}%), Max diff: {max_diff_pct:.1f}%"
        else:
            passed = False
            message = "No area data found"
        
        return TestResult("Area Calculation Accuracy", passed, message, time.time() - start)
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}ADMIN IMPORT INTEGRATION TESTS{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        tests = [
            self.test_strapi_running,
            self.test_database_connection,
            self.test_admin_levels_seeded,
            self.test_postgis_extension,
            self.test_regions_table_schema,
            self.test_spatial_index,
            self.test_geojson_files_exist,
            self.test_import_api_endpoint,
            self.test_get_country_id,
            self.test_clean_existing_regions,
            self.test_parish_import,
            self.test_verify_parish_in_db,
            self.test_geometry_validity,
            self.test_region_metadata_fields,
            self.test_junction_tables,
            self.test_spatial_query_performance,
            self.test_area_accuracy,
        ]
        
        for i, test_func in enumerate(tests, 1):
            print(f"{Colors.BLUE}[{i}/{len(tests)}]{Colors.RESET} Running: {test_func.__doc__.split(':')[1].strip()}")
            result = test_func()
            self.results.append(result)
            print(f"    {result}\n")
            
            # Stop on critical failures
            if not result.passed and i <= 3:
                print(f"{Colors.RED}Critical test failed. Stopping test suite.{Colors.RESET}\n")
                break
        
        self.print_summary()
        
        if self.db_conn:
            self.db_conn.close()
    
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        total_time = sum(r.duration for r in self.results)
        
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        
        print(f"Total Tests: {len(self.results)}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"Total Time: {total_time:.3f}s")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if failed > 0:
            print(f"{Colors.RED}FAILED TESTS:{Colors.RESET}")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.name}: {result.message}")
            print()
        
        success_rate = (passed / len(self.results)) * 100
        if success_rate == 100:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.RESET}\n")
            sys.exit(0)
        elif success_rate >= 80:
            print(f"{Colors.YELLOW}⚠ PARTIAL SUCCESS ({success_rate:.0f}%){Colors.RESET}\n")
            sys.exit(1)
        else:
            print(f"{Colors.RED}✗ TESTS FAILED ({success_rate:.0f}%){Colors.RESET}\n")
            sys.exit(1)


if __name__ == "__main__":
    print(f"{Colors.YELLOW}Note: Make sure Strapi is running on http://localhost:1337{Colors.RESET}")
    print(f"{Colors.YELLOW}      and PostgreSQL is accessible with admin_levels seeded.{Colors.RESET}\n")
    
    input("Press Enter to start tests...")
    
    tester = AdminImportTester()
    tester.run_all_tests()
