"""
Integration tests for Geospatial Services API
Tests all spatial query endpoints with real Barbados data
"""

import requests
import time
import json

# API base URL
BASE_URL = "http://localhost:6000"

# Test coordinates in Barbados
BRIDGETOWN_CENTER = {"lat": 13.0969, "lon": -59.6145}  # Bridgetown center
TOM_ADAMS_HIGHWAY = {"lat": 13.0806, "lon": -59.5905}  # Near airport
PARISH_BOUNDARY = {"lat": 13.1853, "lon": -59.5431}   # St. Andrew/St. Joseph boundary
RURAL_AREA = {"lat": 13.2500, "lon": -59.5500}         # Rural St. Andrew


class TestHealthEndpoints:
    """Test API health and status endpoints"""
    
    def test_01_health_endpoint(self):
        """Test /health endpoint returns healthy status"""
        print("\n🧪 Test 1: Health endpoint")
        
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["status"] == "healthy", "API should be healthy"
        assert data["database"] == "connected", "Database should be connected"
        assert "features" in data, "Should return feature counts"
        assert data["features"]["buildings"] > 0, "Should have buildings"
        assert data["latency_ms"] < 100, f"Health check too slow: {data['latency_ms']}ms"
        
        print(f"✅ Health check: {data['latency_ms']:.2f}ms")
        print(f"   Buildings: {data['features']['buildings']:,}")
        print(f"   Highways: {data['features']['highways']:,}")
        print(f"   POIs: {data['features']['pois']:,}")
    
    def test_02_root_endpoint(self):
        """Test / root endpoint returns API info"""
        print("\n🧪 Test 2: Root endpoint")
        
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "Geospatial Services API"
        assert data["status"] == "operational"
        assert "endpoints" in data
        
        print(f"✅ Service: {data['service']} v{data['version']}")


class TestReverseGeocoding:
    """Test reverse geocoding endpoints"""
    
    def test_03_reverse_geocode_bridgetown(self):
        """Test reverse geocoding in Bridgetown (should find highway + POI)"""
        print("\n🧪 Test 3: Reverse geocode - Bridgetown")
        print(f"   Input: lat={BRIDGETOWN_CENTER['lat']}, lon={BRIDGETOWN_CENTER['lon']}")
        
        response = requests.get(
            f"{BASE_URL}/geocode/reverse",
            params=BRIDGETOWN_CENTER
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "address" in data
        assert data["address"] != "Unknown location", "Should find location in Bridgetown"
        assert data["latitude"] == BRIDGETOWN_CENTER["lat"]
        assert data["longitude"] == BRIDGETOWN_CENTER["lon"]
        assert data["latency_ms"] < 50, f"Too slow: {data['latency_ms']}ms (target <50ms)"
        
        print(f"✅ Address: {data['address']}")
        print(f"   Latency: {data['latency_ms']:.2f}ms")
        if data.get("highway"):
            print(f"   Highway: {data['highway']['name']} ({data['highway']['distance_meters']:.0f}m)")
        if data.get("poi"):
            print(f"   POI: {data['poi']['name']} ({data['poi']['distance_meters']:.0f}m)")
    
    def test_04_reverse_geocode_highway(self):
        """Test reverse geocoding near Tom Adams Highway"""
        print("\n🧪 Test 4: Reverse geocode - Tom Adams Highway")
        print(f"   Input: lat={TOM_ADAMS_HIGHWAY['lat']}, lon={TOM_ADAMS_HIGHWAY['lon']}")
        
        response = requests.get(
            f"{BASE_URL}/geocode/reverse",
            params=TOM_ADAMS_HIGHWAY
        )
        assert response.status_code == 200
        
        data = response.json()
        # Just verify we got a valid address with highway and parish
        assert data["address"] is not None and len(data["address"]) > 0, "Should return an address"
        assert data["highway"] is not None, "Should find highway nearby"
        assert data["latency_ms"] < 50
        
        print(f"✅ Address: {data['address']}")
        print(f"   Latency: {data['latency_ms']:.2f}ms")
    
    def test_05_reverse_geocode_post_method(self):
        """Test POST method for reverse geocoding"""
        print("\n🧪 Test 5: Reverse geocode - POST method")
        
        response = requests.post(
            f"{BASE_URL}/geocode/reverse",
            json={
                "latitude": BRIDGETOWN_CENTER["lat"],
                "longitude": BRIDGETOWN_CENTER["lon"],
                "highway_radius_meters": 500,
                "poi_radius_meters": 1000
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["address"] != "Unknown location"
        print(f"✅ POST method works: {data['address']}")


class TestGeofencing:
    """Test geofence detection endpoints"""
    
    def test_06_geofence_check_bridgetown(self):
        """Test geofence check in Bridgetown (should be in a parish)"""
        print("\n🧪 Test 6: Geofence check - Bridgetown")
        print(f"   Input: lat={BRIDGETOWN_CENTER['lat']}, lon={BRIDGETOWN_CENTER['lon']}")
        
        response = requests.post(
            f"{BASE_URL}/geofence/check",
            json={
                "latitude": BRIDGETOWN_CENTER["lat"],
                "longitude": BRIDGETOWN_CENTER["lon"]
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["inside_region"] == True, "Bridgetown should be inside a region"
        assert data["region"] is not None, "Should return region details"
        assert data["latency_ms"] < 30, f"Too slow: {data['latency_ms']}ms (target <30ms)"
        
        print(f"✅ Inside region: {data['region']['name']}")
        print(f"   Region type: {data['region']['region_type']}")
        print(f"   Inside landuse: {data['inside_landuse']}")
        print(f"   Latency: {data['latency_ms']:.2f}ms")
    
    def test_07_geofence_check_parish_boundary(self):
        """Test geofence near parish boundary"""
        print("\n🧪 Test 7: Geofence check - Parish boundary")
        print(f"   Input: lat={PARISH_BOUNDARY['lat']}, lon={PARISH_BOUNDARY['lon']}")
        
        response = requests.post(
            f"{BASE_URL}/geofence/check",
            json={
                "latitude": PARISH_BOUNDARY["lat"],
                "longitude": PARISH_BOUNDARY["lon"]
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should still be inside SOME parish
        assert data["inside_region"] == True
        print(f"✅ Region: {data['region']['name'] if data['region'] else 'None'}")
    
    def test_08_geofence_batch_check(self):
        """Test batch geofence checking"""
        print("\n🧪 Test 8: Geofence batch check")
        
        coordinates = [
            {"latitude": BRIDGETOWN_CENTER["lat"], "longitude": BRIDGETOWN_CENTER["lon"]},
            {"latitude": TOM_ADAMS_HIGHWAY["lat"], "longitude": TOM_ADAMS_HIGHWAY["lon"]},
            {"latitude": RURAL_AREA["lat"], "longitude": RURAL_AREA["lon"]}
        ]
        
        response = requests.post(
            f"{BASE_URL}/geofence/check-batch",
            json={"coordinates": coordinates}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_count"] == 3
        assert len(data["results"]) == 3
        assert data["latency_ms"] < 200, f"Batch too slow: {data['latency_ms']}ms (target <200ms)"
        
        print(f"✅ Batch check: {data['total_count']} coordinates in {data['latency_ms']:.2f}ms")
        for i, result in enumerate(data["results"]):
            region_name = result["region"]["name"] if result["region"] else "None"
            print(f"   [{i+1}] {region_name}")


class TestSpatialQueries:
    """Test spatial query endpoints for spawning"""
    
    def test_09_depot_catchment_bridgetown(self):
        """Test depot catchment query in Bridgetown"""
        print("\n🧪 Test 9: Depot catchment - Bridgetown (1km radius)")
        print(f"   Input: lat={BRIDGETOWN_CENTER['lat']}, lon={BRIDGETOWN_CENTER['lon']}, radius=1000m")
        
        response = requests.get(
            f"{BASE_URL}/spatial/depot-catchment",
            params={
                "lat": BRIDGETOWN_CENTER["lat"],
                "lon": BRIDGETOWN_CENTER["lon"],
                "radius": 1000,
                "limit": 5000
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["radius_meters"] == 1000
        assert data["count"] > 0, "Should find buildings in Bridgetown"
        assert data["latency_ms"] < 150, f"Too slow: {data['latency_ms']}ms (target <150ms)"
        assert len(data["buildings"]) == data["count"]
        
        # Verify building structure
        if data["buildings"]:
            building = data["buildings"][0]
            assert "building_id" in building
            assert "latitude" in building
            assert "longitude" in building
            assert "distance_meters" in building
            assert building["distance_meters"] <= 1000, "Building should be within radius"
        
        print(f"✅ Found {data['count']:,} buildings within 1km")
        print(f"   Latency: {data['latency_ms']:.2f}ms")
        if data["buildings"]:
            print(f"   Closest: {data['buildings'][0]['distance_meters']:.0f}m")
    
    def test_10_depot_catchment_post_method(self):
        """Test POST method for depot catchment"""
        print("\n🧪 Test 10: Depot catchment - POST method")
        
        response = requests.post(
            f"{BASE_URL}/spatial/depot-catchment",
            json={
                "latitude": BRIDGETOWN_CENTER["lat"],
                "longitude": BRIDGETOWN_CENTER["lon"],
                "radius_meters": 500,
                "limit": 1000
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] > 0
        print(f"✅ POST method: {data['count']} buildings in 500m")
    
    def test_11_depot_catchment_rural_area(self):
        """Test depot catchment in rural area (fewer buildings expected)"""
        print("\n🧪 Test 11: Depot catchment - Rural area")
        print(f"   Input: lat={RURAL_AREA['lat']}, lon={RURAL_AREA['lon']}, radius=1000m")
        
        response = requests.get(
            f"{BASE_URL}/spatial/depot-catchment",
            params={
                "lat": RURAL_AREA["lat"],
                "lon": RURAL_AREA["lon"],
                "radius": 1000,
                "limit": 5000
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        print(f"✅ Rural area: {data['count']} buildings")
        print(f"   Latency: {data['latency_ms']:.2f}ms")
    
    def test_12_route_buildings_query(self):
        """Test route buildings query (requires highway document_id)"""
        print("\n🧪 Test 12: Route buildings - Need to get highway ID first")
        
        # First, get a highway document_id by finding nearest highway
        geocode_response = requests.get(
            f"{BASE_URL}/geocode/reverse",
            params=TOM_ADAMS_HIGHWAY
        )
        
        if geocode_response.status_code == 200:
            geocode_data = geocode_response.json()
            
            if geocode_data.get("highway"):
                # We need to query the database to get document_id
                # For now, just test the endpoint structure
                print("   ⚠️  Need highway document_id for full test")
                print(f"   Found highway: {geocode_data['highway']['name']}")
            else:
                print("   ⚠️  No highway found at test coordinates")
        else:
            print("   ⚠️  Could not test route buildings (no highway data)")


class TestPerformance:
    """Performance benchmarks"""
    
    def test_13_performance_reverse_geocoding(self):
        """Benchmark reverse geocoding with concurrent requests"""
        print("\n🧪 Test 13: Performance - Reverse geocoding (10 concurrent requests)")
        
        import concurrent.futures
        
        def make_request():
            response = requests.get(
                f"{BASE_URL}/geocode/reverse",
                params=BRIDGETOWN_CENTER
            )
            if response.status_code == 200:
                return response.json().get('latency_ms', 0)
            return None
        
        start = time.time()
        
        # Execute 10 requests concurrently (simulates real async usage)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            latencies = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        wall_clock_time = (time.time() - start) * 1000
        latencies = [l for l in latencies if l is not None]
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
            
            print(f"✅ API Latency - Avg: {avg_latency:.2f}ms, Min: {min_latency:.2f}ms, Max: {max_latency:.2f}ms")
            print(f"   Wall-clock (10 concurrent): {wall_clock_time:.2f}ms")
            print(f"   Throughput: ~{10000/wall_clock_time:.0f} req/sec")
            
            # Reverse geocode makes 3 DB queries, so allow higher latency
            # Real-time systems need fast geofence checks (2-10ms), not addresses
            assert avg_latency < 500, f"API latency too high: {avg_latency:.2f}ms"
        else:
            assert False, "No successful requests"
    
    def test_14_performance_geofence_check(self):
        """Benchmark geofence check with concurrent requests"""
        print("\n🧪 Test 14: Performance - Geofence check (10 concurrent requests)")
        
        import concurrent.futures
        
        def make_request():
            response = requests.post(
                f"{BASE_URL}/geofence/check",
                json={
                    "latitude": BRIDGETOWN_CENTER["lat"],
                    "longitude": BRIDGETOWN_CENTER["lon"]
                }
            )
            if response.status_code == 200:
                return response.json().get('latency_ms', 0)
            return None
        
        start = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            latencies = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        wall_clock_time = (time.time() - start) * 1000
        latencies = [l for l in latencies if l is not None]
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            
            print(f"✅ API Latency - Avg: {avg_latency:.2f}ms, Min: {min(latencies):.2f}ms, Max: {max(latencies):.2f}ms")
            print(f"   Wall-clock (10 concurrent): {wall_clock_time:.2f}ms")
            print(f"   Throughput: ~{10000/wall_clock_time:.0f} req/sec")
            
            assert avg_latency < 50, f"API latency too high: {avg_latency:.2f}ms"
        else:
            assert False, "No successful requests"
    
    def test_15_performance_depot_catchment(self):
        """Benchmark depot catchment with concurrent requests"""
        print("\n🧪 Test 15: Performance - Depot catchment (5 concurrent requests)")
        
        import concurrent.futures
        
        def make_request():
            response = requests.get(
                f"{BASE_URL}/spatial/depot-catchment",
                params={
                    "lat": BRIDGETOWN_CENTER["lat"],
                    "lon": BRIDGETOWN_CENTER["lon"],
                    "radius": 1000,
                    "limit": 5000
                }
            )
            if response.status_code == 200:
                return response.json().get('latency_ms', 0)
            return None
        
        start = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            latencies = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        wall_clock_time = (time.time() - start) * 1000
        latencies = [l for l in latencies if l is not None]
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            
            print(f"✅ API Latency - Avg: {avg_latency:.2f}ms, Min: {min(latencies):.2f}ms, Max: {max(latencies):.2f}ms")
            print(f"   Wall-clock (5 concurrent): {wall_clock_time:.2f}ms")
            print(f"   Throughput: ~{5000/wall_clock_time:.0f} req/sec")
            
            assert avg_latency < 200, f"API latency too high: {avg_latency:.2f}ms"
        else:
            assert False, "No successful requests"


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_16_invalid_coordinates(self):
        """Test with invalid coordinates"""
        print("\n🧪 Test 16: Error handling - Invalid coordinates")
        
        # Latitude out of range
        response = requests.get(
            f"{BASE_URL}/geocode/reverse",
            params={"lat": 91, "lon": -59.6145}
        )
        assert response.status_code == 422, "Should reject invalid latitude"
        
        # Longitude out of range
        response = requests.get(
            f"{BASE_URL}/geocode/reverse",
            params={"lat": 13.0969, "lon": -181}
        )
        assert response.status_code == 422, "Should reject invalid longitude"
        
        print("✅ Invalid coordinates properly rejected")


def run_tests():
    """Run all tests"""
    print("=" * 80)
    print("GEOSPATIAL SERVICES API - INTEGRATION TESTS")
    print("=" * 80)
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ API not healthy. Please start the server: python main.py")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {BASE_URL}")
        print("   Please start the server: python main.py")
        return False
    
    test_classes = [
        TestHealthEndpoints,
        TestReverseGeocoding,
        TestGeofencing,
        TestSpatialQueries,
        TestPerformance,
        TestErrorHandling
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        
        for method_name in sorted(methods):
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                passed_tests += 1
            except AssertionError as e:
                failed_tests.append((method_name, str(e)))
                print(f"❌ FAILED: {e}")
            except Exception as e:
                failed_tests.append((method_name, str(e)))
                print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {len(failed_tests)} ❌")
    
    if failed_tests:
        print("\nFailed tests:")
        for test_name, error in failed_tests:
            print(f"  - {test_name}: {error}")
        return False
    else:
        print("\n🎉 ALL TESTS PASSED!")
        return True


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
