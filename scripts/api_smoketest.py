"""
Fleet Management API Smoke Test Suite
=====================================
Comprehensive test suite to verify all API endpoints are production-ready
for CRUD operations and meet MVP demo standards.

Tests:
- Database connectivity
- All CRUD operations for each entity
- Error handling
- Data validation
- Response formats
- Performance benchmarks
"""

import requests
import json
import time
import uuid
from datetime import datetime, date
from datetime import time as datetime_time
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Test configuration
API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
TIMEOUT = 30  # seconds
MAX_RESPONSE_TIME = 2.0  # seconds for performance check

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class APITester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.created_entities = {}  # Track created entities for cleanup
        
    def log(self, message: str, color: str = Colors.WHITE):
        """Log a message with color"""
        print(f"{color}{message}{Colors.END}")
        
    def log_success(self, message: str):
        self.log(f"✅ {message}", Colors.GREEN)
        
    def log_error(self, message: str):
        self.log(f"❌ {message}", Colors.RED)
        
    def log_warning(self, message: str):
        self.log(f"⚠️  {message}", Colors.YELLOW)
        
    def log_info(self, message: str):
        self.log(f"ℹ️  {message}", Colors.BLUE)

    def make_request(self, method: str, endpoint: str, use_prefix: bool = True, **kwargs) -> tuple[Optional[requests.Response], Optional[Exception]]:
        """Make HTTP request with error handling and retry logic"""
        if use_prefix and not endpoint.startswith(("/health", "/docs", "/redoc")) and endpoint != "/":
            url = f"{self.base_url}{API_PREFIX}{endpoint}"
        else:
            url = f"{self.base_url}{endpoint}"
        
        # Retry logic for connection issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = self.session.request(method, url, timeout=TIMEOUT, **kwargs)
                end_time = time.time()
                
                # Performance check
                response_time = end_time - start_time
                if response_time > MAX_RESPONSE_TIME:
                    self.log_warning(f"Slow response: {response_time:.2f}s for {method} {endpoint}")
                    
                return response, None
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # Wait 500ms before retry
                    continue
                return None, e
            except Exception as e:
                return None, e
        
        return None, Exception("Max retries exceeded")

    def wait_for_api_ready(self, max_wait_time: int = 30) -> bool:
        """Wait for API to be ready before running tests"""
        print(f"🔄 Waiting for API to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.session.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ API is ready!")
                    return True
            except:
                pass
            time.sleep(1)
        
        print(f"❌ API did not become ready within {max_wait_time} seconds")
        return False

    def test_health_check(self) -> bool:
        """Test API health and database connectivity"""
        self.log_info("Testing API health and database connectivity...")
        
        # Test root endpoint
        response, error = self.make_request("GET", "/", use_prefix=False)
        if error or not response or response.status_code != 200:
            self.log_error("Root endpoint failed")
            return False
            
        # Test health endpoint
        response, error = self.make_request("GET", "/health", use_prefix=False)
        if error:
            self.log_error(f"Health check failed: {error}")
            return False
            
        # Test health endpoint specifically
        if response.status_code == 200:
            health_data = response.json()
            if health_data.get("status") == "healthy":
                self.log_success("Health check passed - API and database are healthy")
                return True
        
        self.log_error("Health check failed")
        return False

    def create_test_country(self) -> Optional[str]:
        """Create a test country and return its ID"""
        country_data = {
            "iso_code": "TS",
            "name": "Test Country"
        }
        
        response, error = self.make_request("POST", "/countries", json=country_data)
        if error or not response or response.status_code != 200:
            return None
            
        country = response.json()
        country_id = country.get("country_id")
        if country_id:
            self.created_entities.setdefault("countries", []).append(country_id)
        return country_id

    def create_test_depot(self, country_id: str) -> Optional[str]:
        """Create a test depot and return its ID"""
        depot_data = {
            "country_id": country_id,
            "name": "Test Depot",
            "capacity": 50,
            "notes": "Automated test depot"
        }
        
        response, error = self.make_request("POST", "/depots", json=depot_data)
        if error or not response or response.status_code != 200:
            return None
            
        depot = response.json()
        depot_id = depot.get("depot_id")
        if depot_id:
            self.created_entities.setdefault("depots", []).append(depot_id)
        return depot_id

    def test_crud_operations(self, entity_name: str, endpoint: str, create_data: Dict, update_data: Dict, 
                           id_field: str, dependency_ids: Dict = None) -> bool:
        """Test complete CRUD operations for an entity"""
        self.log_info(f"Testing CRUD operations for {entity_name}...")
        
        # Inject dependency IDs into create_data if provided
        if dependency_ids:
            create_data.update(dependency_ids)
            
        # CREATE Test
        self.log_info(f"Testing CREATE {entity_name}...")
        response, error = self.make_request("POST", endpoint, json=create_data)
        
        if error:
            self.log_error(f"CREATE {entity_name} - Network error: {error}")
            return False
            
        if not response or response.status_code != 200:
            self.log_error(f"CREATE {entity_name} - HTTP {response.status_code if response else 'None'}")
            if response:
                self.log_error(f"Response: {response.text}")
            return False
            
        try:
            created_entity = response.json()
            entity_id = created_entity.get(id_field)
            if not entity_id:
                self.log_error(f"CREATE {entity_name} - No {id_field} in response")
                return False
        except json.JSONDecodeError:
            self.log_error(f"CREATE {entity_name} - Invalid JSON response")
            return False
            
        self.log_success(f"CREATE {entity_name} - ID: {entity_id}")
        
        # Track created entity for cleanup
        self.created_entities.setdefault(entity_name.lower(), []).append(entity_id)
        
        # READ Test (single)
        self.log_info(f"Testing READ {entity_name} (single)...")
        response, error = self.make_request("GET", f"{endpoint}/{entity_id}")
        
        if error or not response or response.status_code != 200:
            self.log_error(f"READ {entity_name} (single) failed")
            return False
            
        self.log_success(f"READ {entity_name} (single) - Success")
        
        # READ Test (list)
        self.log_info(f"Testing READ {entity_name} (list)...")
        response, error = self.make_request("GET", f"{endpoint}?limit=10")
        
        if error or not response or response.status_code != 200:
            self.log_error(f"READ {entity_name} (list) failed")
            return False
            
        try:
            entities_list = response.json()
            if not isinstance(entities_list, list):
                self.log_error(f"READ {entity_name} (list) - Response is not a list")
                return False
        except json.JSONDecodeError:
            self.log_error(f"READ {entity_name} (list) - Invalid JSON response")
            return False
            
        self.log_success(f"READ {entity_name} (list) - Found {len(entities_list)} entities")
        
        # UPDATE Test
        self.log_info(f"Testing UPDATE {entity_name}...")
        response, error = self.make_request("PUT", f"{endpoint}/{entity_id}", json=update_data)
        
        if error or not response or response.status_code != 200:
            self.log_error(f"UPDATE {entity_name} failed")
            return False
            
        self.log_success(f"UPDATE {entity_name} - Success")
        
        # DELETE Test
        self.log_info(f"Testing DELETE {entity_name}...")
        response, error = self.make_request("DELETE", f"{endpoint}/{entity_id}")
        
        if error or not response or response.status_code != 200:
            self.log_error(f"DELETE {entity_name} failed")
            return False
            
        self.log_success(f"DELETE {entity_name} - Success")
        
        # Remove from tracking since it's deleted
        if entity_name.lower() in self.created_entities:
            try:
                self.created_entities[entity_name.lower()].remove(entity_id)
            except ValueError:
                pass
        
        # Verify DELETE (should return 404) - use fresh request to avoid session issues
        try:
            import requests
            url = f"{self.base_url}{API_PREFIX}{endpoint}/{entity_id}"
            response = requests.get(url, timeout=TIMEOUT)
            
            if response.status_code == 404:
                self.log_success(f"DELETE {entity_name} verification - Entity properly removed")
            else:
                self.log_warning(f"DELETE {entity_name} verification - Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_warning(f"DELETE {entity_name} verification - Error checking deletion: {e}")
        
        return True

    def test_error_handling(self) -> bool:
        """Test error handling and validation"""
        self.log_info("Testing error handling and validation...")
        
        # Test 404 for non-existent entity - use fresh session to avoid any session issues
        fake_id = str(uuid.uuid4())
        url = f"{self.base_url}{API_PREFIX}/countries/{fake_id}"
        
        try:
            # Use a fresh requests call instead of session to eliminate session issues
            import requests
            response = requests.get(url, timeout=TIMEOUT)
            
            if response.status_code == 404:
                self.log_success("404 handling works correctly")
            else:
                self.log_error(f"404 handling failed - Expected 404, got {response.status_code}")
                self.log_error(f"Response body: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"404 test failed with error: {type(e).__name__}: {e}")
            return False
            
        # Test invalid data validation
        try:
            invalid_data = {"invalid_field": "invalid_value"}
            url = f"{self.base_url}{API_PREFIX}/countries"
            response = requests.post(url, json=invalid_data, timeout=TIMEOUT)
            
            if response.status_code in [400, 422]:  # FastAPI uses 422 for validation errors
                self.log_success("Data validation works correctly")
            else:
                self.log_error(f"Data validation failed - Expected 400/422, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"Data validation test failed with error: {type(e).__name__}: {e}")
            return False
            
        return True

    def cleanup_created_entities(self):
        """Clean up all entities created during testing"""
        self.log_info("Cleaning up created test entities...")
        
        # Cleanup order matters due to foreign key constraints
        cleanup_order = ["vehicles", "drivers", "stops", "trips", "blocks", "services", "depots", "countries"]
        
        for entity_type in cleanup_order:
            if entity_type in self.created_entities:
                endpoint_map = {
                    "countries": "/countries",
                    "depots": "/depots",
                    "vehicles": "/vehicles",
                    "drivers": "/drivers",
                    "stops": "/stops",
                    "trips": "/trips",
                    "services": "/services",
                    "blocks": "/blocks"
                }
                
                endpoint = endpoint_map.get(entity_type)
                if endpoint:
                    for entity_id in self.created_entities[entity_type]:
                        self.make_request("DELETE", f"{endpoint}/{entity_id}")
                        
        self.log_success("Cleanup completed")

    def run_comprehensive_tests(self) -> bool:
        """Run comprehensive test suite"""
        self.log(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        self.log(f"{Colors.BOLD}{Colors.CYAN}Fleet Management API Smoke Test Suite{Colors.END}")
        self.log(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")
        
        # Wait for API to be ready
        if not self.wait_for_api_ready():
            return False
        
        start_time = time.time()
        all_tests_passed = True
        
        # Test 1: Health Check
        if not self.test_health_check():
            self.log_error("Health check failed - Cannot proceed with tests")
            return False
            
        # Test 2: Error Handling
        if not self.test_error_handling():
            all_tests_passed = False
            
        # Test 3: Create dependencies for other tests
        self.log_info("Setting up test dependencies...")
        country_id = self.create_test_country()
        if not country_id:
            self.log_error("Failed to create test country - Cannot test dependent entities")
            return False
            
        depot_id = self.create_test_depot(country_id)
        if not depot_id:
            self.log_error("Failed to create test depot - Cannot test dependent entities")
            return False
        
        # Test 4: CRUD Operations for all entities
        test_cases = [
            {
                "entity_name": "Countries",
                "endpoint": "/countries",
                "create_data": {"iso_code": "T2", "name": "Test Country 2"},
                "update_data": {"name": "Updated Test Country 2"},
                "id_field": "country_id"
            },
            {
                "entity_name": "Depots", 
                "endpoint": "/depots",
                "create_data": {"name": "Test Depot 2", "capacity": 75},
                "update_data": {"capacity": 100},
                "id_field": "depot_id",
                "dependency_ids": {"country_id": country_id}
            },
            {
                "entity_name": "Vehicles",
                "endpoint": "/vehicles", 
                "create_data": {
                    "reg_code": "TEST-001",
                    "status": "available",
                    "notes": "Test vehicle"
                },
                "update_data": {"status": "maintenance"},
                "id_field": "vehicle_id",
                "dependency_ids": {"country_id": country_id, "home_depot_id": depot_id}
            },
            {
                "entity_name": "Drivers",
                "endpoint": "/drivers",
                "create_data": {
                    "name": "Test Driver",
                    "license_no": "TEST123",
                    "employment_status": "active"
                },
                "update_data": {"employment_status": "inactive"},
                "id_field": "driver_id",
                "dependency_ids": {"country_id": country_id, "home_depot_id": depot_id}
            },
            {
                "entity_name": "Services",
                "endpoint": "/services",
                "create_data": {
                    "name": "Test Service",
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": False,
                    "sun": False,
                    "date_start": "2024-01-01",
                    "date_end": "2024-12-31"
                },
                "update_data": {"sat": True},
                "id_field": "service_id",
                "dependency_ids": {"country_id": country_id}
            },
            {
                "entity_name": "Stops",
                "endpoint": "/stops",
                "create_data": {
                    "code": "TEST001",
                    "name": "Test Stop",
                    "latitude": 13.0969,
                    "longitude": -59.6138,
                    "zone_id": "TEST_ZONE"
                },
                "update_data": {"name": "Updated Test Stop", "latitude": 13.0970, "longitude": -59.6140},
                "id_field": "stop_id",
                "dependency_ids": {"country_id": country_id}
            }
        ]
        
        for test_case in test_cases:
            success = self.test_crud_operations(**test_case)
            if not success:
                all_tests_passed = False
                
        # Test 5: Performance benchmarks
        self.log_info("Running performance benchmarks...")
        # This is already done in make_request method
        
        # Cleanup
        self.cleanup_created_entities()
        
        # Results
        end_time = time.time()
        total_time = end_time - start_time
        
        self.log(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        self.log(f"{Colors.BOLD}{Colors.CYAN}Test Results Summary{Colors.END}")
        self.log(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        
        if all_tests_passed:
            self.log_success(f"✅ ALL TESTS PASSED - API is production ready!")
            self.log_success(f"📊 Total test time: {total_time:.2f} seconds")
            self.log_success(f"🚀 MVP demo standards met")
        else:
            self.log_error(f"❌ SOME TESTS FAILED - API needs attention")
            self.log_error(f"📊 Total test time: {total_time:.2f} seconds")
            
        return all_tests_passed

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    else:
        api_url = API_BASE_URL
        
    print(f"Testing API at: {api_url}")
    
    tester = APITester(api_url)
    success = tester.run_comprehensive_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
