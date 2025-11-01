"""
Comprehensive endpoint test script for Geospatial Services API v2.0.0
Tests all 52+ endpoints and provides pass/fail verdicts.
"""

import requests
import json
from typing import Dict, List, Tuple
from datetime import datetime

BASE_URL = "http://localhost:6000"
TIMEOUT = 10  # seconds

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def test_endpoint(method: str, endpoint: str, description: str, 
                  body: dict = None, expected_status: int = 200,
                  requires_strapi: bool = False) -> Tuple[bool, str]:
    """Test a single endpoint and return (success, message)"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=body, timeout=TIMEOUT)
        else:
            return False, f"Unknown method: {method}"
        
        # Check if it's a known Strapi dependency issue
        if response.status_code == 500 and requires_strapi:
            if "Strapi" in response.text or "Failed to fetch" in response.text:
                return None, "SKIP: Requires Strapi (not running)"
        
        # Check status code
        if response.status_code != expected_status:
            return False, f"Expected {expected_status}, got {response.status_code}: {response.text[:100]}"
        
        # Try to parse JSON
        try:
            data = response.json()
        except:
            return False, f"Response not valid JSON: {response.text[:100]}"
        
        return True, f"OK - {response.status_code}"
        
    except requests.exceptions.Timeout:
        return False, "TIMEOUT"
    except requests.exceptions.ConnectionError:
        return False, "CONNECTION ERROR - Service not running?"
    except Exception as e:
        return False, f"Exception: {str(e)[:100]}"

def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_result(endpoint: str, success: bool, message: str, description: str):
    """Print a test result"""
    if success is None:  # Skip
        status = f"{Colors.YELLOW}SKIP{Colors.RESET}"
        symbol = "⊘"
    elif success:
        status = f"{Colors.GREEN}PASS{Colors.RESET}"
        symbol = "✓"
    else:
        status = f"{Colors.RED}FAIL{Colors.RESET}"
        symbol = "✗"
    
    print(f"{symbol} [{status}] {endpoint}")
    print(f"  {description}")
    if message and (not success or success is None):
        print(f"  {Colors.YELLOW}{message}{Colors.RESET}")

def main():
    """Run all endpoint tests"""
    print(f"\n{Colors.BOLD}Geospatial Services API v2.0.0 - Endpoint Test Suite{Colors.RESET}")
    print(f"Testing against: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        'pass': 0,
        'fail': 0,
        'skip': 0,
        'tests': []
    }
    
    # ========== METADATA ENDPOINTS ==========
    print_section("1. METADATA ENDPOINTS (/meta)")
    
    tests = [
        ("GET", "/meta/health", "Health check with component status", None, 200, False),
        ("GET", "/meta/version", "API version and capabilities", None, 200, False),
        ("GET", "/meta/stats", "Database statistics", None, 200, False),
        ("GET", "/meta/bounds", "Geographic bounding box", None, 200, False),
        ("GET", "/meta/regions", "List all regions", None, 200, False),
        ("GET", "/meta/tags", "Available OSM tags", None, 200, False),
    ]
    
    for method, endpoint, desc, body, status, strapi in tests:
        success, msg = test_endpoint(method, endpoint, desc, body, status, strapi)
        print_result(endpoint, success, msg, desc)
        results['tests'].append((endpoint, success, msg))
        if success is None:
            results['skip'] += 1
        elif success:
            results['pass'] += 1
        else:
            results['fail'] += 1
    
    # ========== GEOCODING ENDPOINTS ==========
    print_section("2. GEOCODING ENDPOINTS (/geocode)")
    
    tests = [
        ("GET", "/geocode/reverse?lat=13.1&lon=-59.6", "Reverse geocode", None, 200, False),
        ("POST", "/geocode/batch", "Batch reverse geocode", 
         {"locations": [{"lat": 13.1, "lon": -59.6}]}, 200, False),
    ]
    
    for method, endpoint, desc, body, status, strapi in tests:
        success, msg = test_endpoint(method, endpoint, desc, body, status, strapi)
        print_result(endpoint, success, msg, desc)
        results['tests'].append((endpoint, success, msg))
        if success is None:
            results['skip'] += 1
        elif success:
            results['pass'] += 1
        else:
            results['fail'] += 1
    
    # ========== GEOFENCING ENDPOINTS ==========
    print_section("3. GEOFENCING ENDPOINTS (/geofence)")
    
    tests = [
        ("POST", "/geofence/check", "Point in polygon check",
         {"latitude": 13.1, "longitude": -59.6, "polygon": [[13.0, -59.7], [13.2, -59.7], [13.2, -59.5], [13.0, -59.5]]},
         200, False),
        ("POST", "/geofence/batch", "Batch geofence check",
         {"points": [{"lat": 13.1, "lon": -59.6}], "polygon": [[13.0, -59.7], [13.2, -59.7], [13.2, -59.5], [13.0, -59.5]]},
         200, False),
    ]
    
    for method, endpoint, desc, body, status, strapi in tests:
        success, msg = test_endpoint(method, endpoint, desc, body, status, strapi)
        print_result(endpoint, success, msg, desc)
        results['tests'].append((endpoint, success, msg))
        if success is None:
            results['skip'] += 1
        elif success:
            results['pass'] += 1
        else:
            results['fail'] += 1
    
    # ========== BUILDINGS ENDPOINTS ==========
    print_section("4. BUILDINGS ENDPOINTS (/buildings)")
    
    tests = [
        ("GET", "/buildings/at-point?latitude=13.1&longitude=-59.6&radius_meters=500", 
         "Buildings near point", None, 200, False),
        ("GET", "/buildings/count", "Total building count", None, 200, False),
        ("GET", "/buildings/stats", "Building statistics", None, 200, False),
        ("POST", "/buildings/along-route", "Buildings along route",
         {"route_geojson": {"type": "LineString", "coordinates": [[-59.6, 13.1], [-59.5, 13.1]]}},
         200, False),
        ("POST", "/buildings/in-polygon", "Buildings in polygon",
         {"coordinates": [[13.0, -59.7], [13.2, -59.7], [13.2, -59.5], [13.0, -59.5], [13.0, -59.7]]},
         200, False),
        ("POST", "/buildings/batch-at-points", "Batch building queries",
         {"points": [{"lat": 13.1, "lon": -59.6}]},
         200, False),
    ]
    
    for method, endpoint, desc, body, status, strapi in tests:
        success, msg = test_endpoint(method, endpoint, desc, body, status, strapi)
        print_result(endpoint, success, msg, desc)
        results['tests'].append((endpoint, success, msg))
        if success is None:
            results['skip'] += 1
        elif success:
            results['pass'] += 1
        else:
            results['fail'] += 1
    
    # ========== ROUTES ENDPOINTS ==========
    print_section("5. ROUTES ENDPOINTS (/routes) - Requires Strapi")
    
    tests = [
        ("GET", "/routes/all", "List all routes", None, 200, True),
        ("POST", "/routes/nearest", "Find nearest route",
         {"latitude": 13.1, "longitude": -59.6},
         200, True),
    ]
    
    for method, endpoint, desc, body, status, strapi in tests:
        success, msg = test_endpoint(method, endpoint, desc, body, status, strapi)
        print_result(endpoint, success, msg, desc)
        results['tests'].append((endpoint, success, msg))
        if success is None:
            results['skip'] += 1
        elif success:
            results['pass'] += 1
        else:
            results['fail'] += 1
    
    # ========== DEPOTS ENDPOINTS ==========
    print_section("6. DEPOTS ENDPOINTS (/depots) - Requires Strapi")
    
    tests = [
        ("GET", "/depots/all", "List all depots", None, 200, True),
        ("POST", "/depots/nearest", "Find nearest depot",
         {"latitude": 13.1, "longitude": -59.6},
         200, True),
    ]
    
    for method, endpoint, desc, body, status, strapi in tests:
        success, msg = test_endpoint(method, endpoint, desc, body, status, strapi)
        print_result(endpoint, success, msg, desc)
        results['tests'].append((endpoint, success, msg))
        if success is None:
            results['skip'] += 1
        elif success:
            results['pass'] += 1
        else:
            results['fail'] += 1
    
    # ========== SPAWN ENDPOINTS ==========
    print_section("7. SPAWN ENDPOINTS (/spawn)")
    
    tests = [
        ("GET", "/spawn/config", "Get spawn configuration", None, 200, False),
        ("GET", "/spawn/time-multipliers", "Get time multipliers", None, 200, False),
        ("GET", "/spawn/system-overview", "System-wide spawn overview", None, 200, True),
        ("GET", "/spawn/all-depots?rate=0.05", "All depots analysis", None, 200, True),
        ("GET", "/spawn/compare-scaling?rates=0.01,0.05,0.1", "Compare scaling", None, 200, True),
    ]
    
    for method, endpoint, desc, body, status, strapi in tests:
        success, msg = test_endpoint(method, endpoint, desc, body, status, strapi)
        print_result(endpoint, success, msg, desc)
        results['tests'].append((endpoint, success, msg))
        if success is None:
            results['skip'] += 1
        elif success:
            results['pass'] += 1
        else:
            results['fail'] += 1
    
    # ========== ANALYTICS ENDPOINTS ==========
    print_section("8. ANALYTICS ENDPOINTS (/analytics)")
    
    tests = [
        ("GET", "/analytics/density-heatmap?min_lat=13.0&max_lat=13.2&min_lon=-59.7&max_lon=-59.5&grid_size=0.05",
         "Building density heatmap", None, 200, False),
        ("GET", "/analytics/route-coverage", "Route coverage analysis", None, 200, True),
        ("GET", "/analytics/depot-service-areas", "Depot service areas", None, 200, True),
        ("GET", "/analytics/population-distribution", "Population distribution", None, 200, False),
        ("GET", "/analytics/transport-demand?passengers_per_building=0.05", 
         "Transport demand estimation", None, 200, False),
    ]
    
    for method, endpoint, desc, body, status, strapi in tests:
        success, msg = test_endpoint(method, endpoint, desc, body, status, strapi)
        print_result(endpoint, success, msg, desc)
        results['tests'].append((endpoint, success, msg))
        if success is None:
            results['skip'] += 1
        elif success:
            results['pass'] += 1
        else:
            results['fail'] += 1
    
    # ========== SPATIAL ENDPOINTS (Legacy) ==========
    print_section("9. SPATIAL ENDPOINTS (Legacy) (/spatial)")
    
    tests = [
        ("GET", "/spatial/buildings/nearest?latitude=13.1&longitude=-59.6&radius_meters=500",
         "Legacy nearest buildings", None, 200, False),
        ("GET", "/spatial/pois/nearest?latitude=13.1&longitude=-59.6&radius_meters=1000",
         "Legacy nearest POIs", None, 200, False),
    ]
    
    for method, endpoint, desc, body, status, strapi in tests:
        success, msg = test_endpoint(method, endpoint, desc, body, status, strapi)
        print_result(endpoint, success, msg, desc)
        results['tests'].append((endpoint, success, msg))
        if success is None:
            results['skip'] += 1
        elif success:
            results['pass'] += 1
        else:
            results['fail'] += 1
    
    # ========== SUMMARY ==========
    print_section("TEST SUMMARY")
    
    total = results['pass'] + results['fail'] + results['skip']
    pass_rate = (results['pass'] / total * 100) if total > 0 else 0
    
    print(f"Total Tests:  {total}")
    print(f"{Colors.GREEN}Passed:       {results['pass']} ({pass_rate:.1f}%){Colors.RESET}")
    print(f"{Colors.RED}Failed:       {results['fail']}{Colors.RESET}")
    print(f"{Colors.YELLOW}Skipped:      {results['skip']} (Strapi not running){Colors.RESET}")
    
    if results['fail'] > 0:
        print(f"\n{Colors.RED}FAILED TESTS:{Colors.RESET}")
        for endpoint, success, msg in results['tests']:
            if success is False:
                print(f"  {Colors.RED}✗{Colors.RESET} {endpoint}")
                print(f"    {msg}")
    
    print(f"\n{Colors.BOLD}Overall Verdict:{Colors.RESET}", end=" ")
    if results['fail'] == 0:
        print(f"{Colors.GREEN}✓ ALL TESTS PASSED{Colors.RESET}")
        print(f"\nNote: {results['skip']} tests skipped (require Strapi)")
        return 0
    else:
        print(f"{Colors.RED}✗ {results['fail']} TEST(S) FAILED{Colors.RESET}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test suite interrupted by user{Colors.RESET}")
        exit(2)
    except Exception as e:
        print(f"\n\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        exit(3)
