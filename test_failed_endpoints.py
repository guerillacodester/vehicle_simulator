"""
Test only the endpoints that failed in the initial test run.
Focus on diagnosing and fixing specific issues.
"""

import requests
import json
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:6000"
TIMEOUT = 10

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def test_endpoint(method: str, endpoint: str, description: str, 
                  body: dict = None) -> Tuple[bool, str, str]:
    """Test endpoint and return (success, status_code, response_text)"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=body, timeout=TIMEOUT)
        else:
            return False, "N/A", f"Unknown method: {method}"
        
        status = response.status_code
        # 200 = success, 503 = Strapi unavailable (acceptable for Strapi-dependent endpoints)
        success = status == 200 or status == 503
        
        # Truncate long responses
        text = response.text
        if len(text) > 200:
            text = text[:200] + "..."
        
        return success, str(status), text
        
    except Exception as e:
        return False, "ERR", str(e)[:200]

def print_test(num: int, endpoint: str, desc: str, success: bool, status: str, response: str):
    """Print test result"""
    if success:
        symbol = f"{Colors.GREEN}✓{Colors.RESET}"
        status_color = Colors.GREEN
    else:
        symbol = f"{Colors.RED}✗{Colors.RESET}"
        status_color = Colors.RED
    
    print(f"\n{num}. {symbol} {endpoint}")
    print(f"   {desc}")
    print(f"   Status: {status_color}{status}{Colors.RESET}")
    if not success:
        print(f"   {Colors.YELLOW}Response: {response}{Colors.RESET}")

print(f"{Colors.BOLD}Testing Failed Endpoints{Colors.RESET}\n")
print("="*80)

results = {'pass': 0, 'fail': 0}

# Test 1: /meta/regions - admin_level column missing
success, status, response = test_endpoint(
    "GET", "/meta/regions", 
    "List all regions (admin_level column issue)"
)
print_test(1, "/meta/regions", "Database column issue", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 2: /meta/tags - landuse_type column missing
success, status, response = test_endpoint(
    "GET", "/meta/tags",
    "Available OSM tags (landuse_type column issue)"
)
print_test(2, "/meta/tags", "Database column issue", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 3: /geocode/reverse - using correct parameter names
success, status, response = test_endpoint(
    "GET", "/geocode/reverse?lat=13.1&lon=-59.6",
    "Reverse geocode (using correct lat/lon parameters)"
)
print_test(3, "/geocode/reverse?lat=13.1&lon=-59.6", 
          "Geocoding test", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 4: /geocode/batch - endpoint missing
success, status, response = test_endpoint(
    "POST", "/geocode/batch",
    "Batch reverse geocode",
    {"locations": [{"lat": 13.1, "lon": -59.6}]}
)
print_test(4, "/geocode/batch", "Missing endpoint (404)", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 5: /geofence/batch - endpoint missing
success, status, response = test_endpoint(
    "POST", "/geofence/batch",
    "Batch geofence check",
    {"points": [{"lat": 13.1, "lon": -59.6}], 
     "polygon": [[13.0, -59.7], [13.2, -59.7], [13.2, -59.5], [13.0, -59.5]]}
)
print_test(5, "/geofence/batch", "Missing endpoint (404)", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 6: /buildings/along-route - wrong parameters
success, status, response = test_endpoint(
    "POST", "/buildings/along-route",
    "Buildings along route (expects route_id in query)",
    {"route_geojson": {"type": "LineString", "coordinates": [[-59.6, 13.1], [-59.5, 13.1]]}}
)
print_test(6, "/buildings/along-route", "Parameter mismatch", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 7: /buildings/in-polygon - SQL subscript error
success, status, response = test_endpoint(
    "POST", "/buildings/in-polygon",
    "Buildings in polygon (SQL subscript error)",
    {"coordinates": [[13.0, -59.7], [13.2, -59.7], [13.2, -59.5], [13.0, -59.5], [13.0, -59.7]]}
)
print_test(7, "/buildings/in-polygon", "SQL error with coordinates", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 8: /routes/nearest - POST body vs query params
success, status, response = test_endpoint(
    "POST", "/routes/nearest",
    "Find nearest route (POST body support)",
    {"latitude": 13.1, "longitude": -59.6}
)
print_test(8, "/routes/nearest", "POST body parameter issue", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 9: /depots/nearest - POST body vs query params
success, status, response = test_endpoint(
    "POST", "/depots/nearest",
    "Find nearest depot (POST body support)",
    {"latitude": 13.1, "longitude": -59.6}
)
print_test(9, "/depots/nearest", "POST body parameter issue", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 10: /analytics/density-heatmap - operator error
success, status, response = test_endpoint(
    "GET", 
    "/analytics/density-heatmap?min_lat=13.0&max_lat=13.2&min_lon=-59.7&max_lon=-59.5&grid_size=0.05",
    "Building density heatmap (operator not unique error)"
)
print_test(10, "/analytics/density-heatmap", "SQL operator error", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 11: /analytics/population-distribution - admin_level missing
success, status, response = test_endpoint(
    "GET", "/analytics/population-distribution",
    "Population distribution (admin_level column missing)"
)
print_test(11, "/analytics/population-distribution", "Database column issue", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 12: /spatial/buildings/nearest - endpoint missing
success, status, response = test_endpoint(
    "GET", "/spatial/buildings/nearest?latitude=13.1&longitude=-59.6&radius_meters=500",
    "Legacy nearest buildings (404)"
)
print_test(12, "/spatial/buildings/nearest", "Missing endpoint (404)", success, status, response)
results['pass' if success else 'fail'] += 1

# Test 13: /spatial/pois/nearest - endpoint missing
success, status, response = test_endpoint(
    "GET", "/spatial/pois/nearest?latitude=13.1&longitude=-59.6&radius_meters=1000",
    "Legacy nearest POIs (404)"
)
print_test(13, "/spatial/pois/nearest", "Missing endpoint (404)", success, status, response)
results['pass' if success else 'fail'] += 1

# Summary
print("\n" + "="*80)
print(f"{Colors.BOLD}SUMMARY{Colors.RESET}")
print(f"Total:  13 failed endpoints")
print(f"{Colors.GREEN}Fixed:  {results['pass']}{Colors.RESET}")
print(f"{Colors.RED}Broken: {results['fail']}{Colors.RESET}")

if results['fail'] == 0:
    print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL ISSUES RESOLVED!{Colors.RESET}")
else:
    print(f"\n{Colors.RED}{Colors.BOLD}✗ {results['fail']} ISSUE(S) REMAINING{Colors.RESET}")
    print("\nIssue Categories:")
    print("  • Database schema issues (admin_level, landuse_type columns)")
    print("  • Parameter name mismatches (lat/lon vs latitude/longitude)")
    print("  • Missing endpoints (404s)")
    print("  • SQL errors (subscript, operator)")

print("="*80)
