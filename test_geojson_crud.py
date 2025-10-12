#!/usr/bin/env python3
"""
Test CRUD operations for all GeoJSON entities (POI, Landuse, Region, Highway)
Verifies proper separation of concerns and shape creation/deletion

Usage:
    python test_geojson_crud.py <email> <password>
    
Example:
    python test_geojson_crud.py admin@example.com MyPassword123
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
STRAPI_URL = "http://localhost:1337"
API_URL = f"{STRAPI_URL}/api"
ADMIN_URL = f"{STRAPI_URL}/admin"
# Full Access API Token
API_TOKEN = "b127418caf99e995d561f1c787005e328c8b9168e7fcc313460e43e032259a2b26d209b260b1dd8c0ca5dced2f20db90823984a50e2ec7429070552acad2b81f94bcad87ddf09e3314ded62538163e55e7f11a8909de45f67dd95890311211f5c1af76b86452a9e4f585ea9e4d3832e434c6cb46b97823c103801323a0214442"

# GeoJSON file paths
GEOJSON_DIR = "E:/projects/github/vehicle_simulator/commuter_service/geojson_data"
POI_FILE = f"{GEOJSON_DIR}/barbados_amenities.json"
LANDUSE_FILE = f"{GEOJSON_DIR}/barbados_landuse.json"
HIGHWAY_FILE = f"{GEOJSON_DIR}/barbados_highway.json"
REGIONS_FILE = f"{GEOJSON_DIR}/barbados_names.json"

# Test GeoJSON samples
POI_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-59.6152, 13.1939]
            },
            "properties": {
                "name": "Test Restaurant",
                "amenity": "restaurant"
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-59.6200, 13.1950]
            },
            "properties": {
                "name": "Test Bank",
                "amenity": "bank"
            }
        }
    ]
}

LANDUSE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-59.6152, 13.1939],
                    [-59.6150, 13.1939],
                    [-59.6150, 13.1937],
                    [-59.6152, 13.1937],
                    [-59.6152, 13.1939]
                ]]
            },
            "properties": {
                "name": "Test Residential Zone",
                "landuse": "residential"
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-59.6160, 13.1940],
                    [-59.6158, 13.1940],
                    [-59.6158, 13.1938],
                    [-59.6160, 13.1938],
                    [-59.6160, 13.1940]
                ]]
            },
            "properties": {
                "name": "Test Commercial Zone",
                "landuse": "commercial"
            }
        }
    ]
}

REGION_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-59.6200, 13.2000],
                    [-59.6100, 13.2000],
                    [-59.6100, 13.1900],
                    [-59.6200, 13.1900],
                    [-59.6200, 13.2000]
                ]]
            },
            "properties": {
                "name": "Test District",
                "admin_level": 8
            }
        }
    ]
}

HIGHWAY_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-59.6152, 13.1939],
                    [-59.6160, 13.1945],
                    [-59.6170, 13.1950]
                ]
            },
            "properties": {
                "name": "Test Highway",
                "highway": "primary"
            }
        }
    ]
}


class GeoJSONTester:
    def __init__(self):
        self.session = requests.Session()
        self.country_id = None
        self.jwt_token = None
        
    def login(self):
        """Login to Strapi admin"""
        email = "guerillacodester@gmail.com"
        password = "Ga25w123"
        
        print(f"\n[LOGIN] Authenticating as {email}...")
        
        # Strapi admin login endpoint
        response = self.session.post(
            f"{ADMIN_URL}/login",
            json={
                "email": email,
                "password": password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.jwt_token = data["data"]["token"]
            self.session.headers.update({"Authorization": f"Bearer {self.jwt_token}"})
            print(f"✅ Logged in successfully")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def find_country(self, country_code="BB"):
        """Find country by code"""
        print(f"\n[COUNTRY] Finding country with code '{country_code}'...")
        response = self.session.get(
            f"{API_URL}/countries",
            params={
                "filters[code][$eq]": country_code,
                "populate": "*"
            },
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["data"]:
                self.country_id = data["data"][0]["documentId"]
                print(f"✅ Found country: {data['data'][0]['name']} (ID: {self.country_id})")
                return True
            else:
                print(f"❌ Country not found")
                return False
        else:
            print(f"❌ Failed to fetch country: {response.status_code} - {response.text[:200]}")
            return False
    
    def upload_geojson_file_from_path(self, file_path: str) -> str:
        """Upload GeoJSON file from disk to Strapi"""
        filename = file_path.split('/')[-1]
        print(f"\n[UPLOAD] Uploading {filename} from {file_path}...")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Upload to Strapi
        files = {
            'files': (filename, file_content, 'application/json')
        }
        
        response = self.session.post(f"{API_URL}/upload", files=files)
        
        if response.status_code == 201:
            data = response.json()
            file_id = data[0]["id"]
            print(f"✅ Uploaded {filename} (ID: {file_id})")
            return file_id
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return None
    
    def upload_geojson_file(self, geojson_data: Dict[str, Any], filename: str) -> str:
        """Upload GeoJSON file to Strapi"""
        print(f"\n[UPLOAD] Uploading {filename}...")
        
        # Create file content
        file_content = json.dumps(geojson_data, indent=2)
        
        # Upload to Strapi
        files = {
            'files': (filename, file_content, 'application/json')
        }
        
        response = self.session.post(f"{API_URL}/upload", files=files)
        
        if response.status_code == 201:
            data = response.json()
            file_id = data[0]["id"]
            print(f"✅ Uploaded {filename} (ID: {file_id})")
            return file_id
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return None
    
    def update_country_geojson(self, field_name: str, file_id: str):
        """Update country with GeoJSON file"""
        print(f"\n[UPDATE] Setting {field_name} to file ID {file_id}...")
        
        response = self.session.put(
            f"{API_URL}/countries/{self.country_id}",
            json={
                "data": {
                    field_name: file_id
                }
            },
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if response.status_code == 200:
            print(f"✅ Country updated with {field_name}")
            return True
        else:
            print(f"❌ Update failed: {response.status_code} - {response.text[:200]}")
            return False
            return False
    
    def count_entities(self, entity_type: str) -> int:
        """Count entities of a specific type for the country"""
        print(f"\n[COUNT] Counting {entity_type}...")
        
        response = self.session.get(
            f"{API_URL}/{entity_type}",
            params={
                "filters[country][documentId][$eq]": self.country_id,
                "pagination[pageSize]": 1
            },
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data["meta"]["pagination"]["total"]
            print(f"✅ Found {count} {entity_type}")
            return count
        else:
            print(f"❌ Count failed: {response.status_code}")
            return -1
    
    def count_shapes(self, shape_type: str) -> int:
        """Count shape records"""
        print(f"\n[COUNT] Counting {shape_type}...")
        
        response = self.session.get(
            f"{API_URL}/{shape_type}",
            params={"pagination[pageSize]": 1},
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data["meta"]["pagination"]["total"]
            print(f"✅ Found {count} {shape_type}")
            return count
        else:
            print(f"❌ Count failed: {response.status_code}")
            return -1
    
    def remove_geojson_file(self, field_name: str):
        """Remove GeoJSON file from country (set to null)"""
        print(f"\n[REMOVE] Removing {field_name}...")
        
        response = self.session.put(
            f"{API_URL}/countries/{self.country_id}",
            json={
                "data": {
                    field_name: None
                }
            },
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if response.status_code == 200:
            print(f"✅ Removed {field_name}")
            return True
        else:
            print(f"❌ Remove failed: {response.status_code} - {response.text[:200]}")
            return False
    
    def test_poi_crud(self):
        """Test POI CRUD operations"""
        print("\n" + "="*60)
        print("TESTING POI CRUD")
        print("="*60)
        
        # Upload POI file
        file_id = self.upload_geojson_file_from_path(POI_FILE)
        if not file_id:
            return False
        
        # Update country with POI file
        if not self.update_country_geojson("pois_geojson_file", file_id):
            return False
        
        print("[WAIT] Waiting 10 seconds for lifecycle hook to process...")
        time.sleep(10)  # Wait for processing
        
        # Verify POIs created
        poi_count = self.count_entities("pois")
        poi_shape_count = self.count_shapes("poi-shapes")
        
        if poi_count == 0:
            print(f"❌ Expected POIs to be created, got {poi_count}")
            return False
        
        print(f"✅ POIs created: {poi_count} entities, {poi_shape_count} shapes")
        
        # Remove POI file
        if not self.remove_geojson_file("pois_geojson_file"):
            return False
        
        time.sleep(3)  # Wait for deletion
        
        # Verify POIs deleted
        poi_count = self.count_entities("pois")
        poi_shape_count = self.count_shapes("poi-shapes")
        
        if poi_count != 0:
            print(f"❌ Expected 0 POIs after deletion, got {poi_count}")
            return False
        
        if poi_shape_count != 0:
            print(f"❌ Expected 0 POI shapes after deletion, got {poi_shape_count}")
            return False
        
        print("\n✅ POI CRUD TEST PASSED")
        return True
    
    def test_landuse_crud(self):
        """Test Landuse CRUD operations"""
        print("\n" + "="*60)
        print("TESTING LANDUSE CRUD")
        print("="*60)
        
        # Upload Landuse file
        file_id = self.upload_geojson_file_from_path(LANDUSE_FILE)
        if not file_id:
            return False
        
        # Update country with Landuse file
        if not self.update_country_geojson("landuse_geojson_file", file_id):
            return False
        
        print("[WAIT] Waiting 10 seconds for lifecycle hook to process...")
        time.sleep(10)  # Wait for processing
        
        # Verify Landuse zones created
        landuse_count = self.count_entities("landuse-zones")
        landuse_shape_count = self.count_shapes("landuse-shapes")
        
        if landuse_count == 0:
            print(f"❌ Expected Landuse zones to be created, got {landuse_count}")
            return False
        
        print(f"✅ Landuse zones created: {landuse_count} entities, {landuse_shape_count} shapes")
        
        # Remove Landuse file
        if not self.remove_geojson_file("landuse_geojson_file"):
            return False
        
        print("[WAIT] Waiting 10 seconds for deletion to process...")
        time.sleep(10)  # Wait for deletion
        
        # Verify Landuse deleted
        landuse_count = self.count_entities("landuse-zones")
        landuse_shape_count = self.count_shapes("landuse-shapes")
        
        if landuse_count != 0:
            print(f"❌ Expected 0 Landuse zones after deletion, got {landuse_count}")
            return False
        
        if landuse_shape_count != 0:
            print(f"❌ Expected 0 Landuse shapes after deletion, got {landuse_shape_count}")
            return False
        
        print("\n✅ LANDUSE CRUD TEST PASSED")
        return True
    
    def test_region_crud(self):
        """Test Region CRUD operations"""
        print("\n" + "="*60)
        print("TESTING REGION CRUD")
        print("="*60)
        
        # Upload Region file
        file_id = self.upload_geojson_file_from_path(REGIONS_FILE)
        if not file_id:
            return False
        
        # Update country with Region file
        if not self.update_country_geojson("regions_geojson_file", file_id):
            return False
        
        print("[WAIT] Waiting 10 seconds for lifecycle hook to process...")
        time.sleep(10)  # Wait for processing
        
        # Verify Regions created
        region_count = self.count_entities("regions")
        region_shape_count = self.count_shapes("region-shapes")
        
        if region_count == 0:
            print(f"❌ Expected Regions to be created, got {region_count}")
            return False
        
        print(f"✅ Regions created: {region_count} entities, {region_shape_count} shapes")
        
        # Remove Region file
        if not self.remove_geojson_file("regions_geojson_file"):
            return False
        
        print("[WAIT] Waiting 10 seconds for deletion to process...")
        time.sleep(10)  # Wait for deletion
        
        # Verify Regions deleted
        region_count = self.count_entities("regions")
        region_shape_count = self.count_shapes("region-shapes")
        
        if region_count != 0:
            print(f"❌ Expected 0 Regions after deletion, got {region_count}")
            return False
        
        if region_shape_count != 0:
            print(f"❌ Expected 0 Region shapes after deletion, got {region_shape_count}")
            return False
        
        print("\n✅ REGION CRUD TEST PASSED")
        return True
    
    def test_highway_crud(self):
        """Test Highway CRUD operations"""
        print("\n" + "="*60)
        print("TESTING HIGHWAY CRUD")
        print("="*60)
        
        # Upload Highway file
        file_id = self.upload_geojson_file_from_path(HIGHWAY_FILE)
        if not file_id:
            return False
        
        # Update country with Highway file
        if not self.update_country_geojson("highways_geojson_file", file_id):
            return False
        
        print("[WAIT] Waiting 10 seconds for lifecycle hook to process...")
        time.sleep(10)  # Wait for processing
        
        # Verify Highways created
        highway_count = self.count_entities("highways")
        highway_shape_count = self.count_shapes("highway-shapes")
        
        if highway_count == 0:
            print(f"❌ Expected Highways to be created, got {highway_count}")
            return False
        
        print(f"✅ Highways created: {highway_count} entities, {highway_shape_count} shapes")
        
        # Remove Highway file
        if not self.remove_geojson_file("highways_geojson_file"):
            return False
        
        print("[WAIT] Waiting 10 seconds for deletion to process...")
        time.sleep(10)  # Wait for deletion
        
        # Verify Highways deleted
        highway_count = self.count_entities("highways")
        highway_shape_count = self.count_shapes("highway-shapes")
        
        if highway_count != 0:
            print(f"❌ Expected 0 Highways after deletion, got {highway_count}")
            return False
        
        if highway_shape_count != 0:
            print(f"❌ Expected 0 Highway shapes after deletion, got {highway_shape_count}")
            return False
        
        print("\n✅ HIGHWAY CRUD TEST PASSED")
        return True
    
    def test_independence(self):
        """Test that entities are independent (uploading one doesn't affect others)"""
        print("\n" + "="*60)
        print("TESTING ENTITY INDEPENDENCE")
        print("="*60)
        
        # Upload POI file
        poi_file_id = self.upload_geojson_file(POI_GEOJSON, "test_pois_independence.json")
        if not poi_file_id:
            return False
        
        # Update country with ONLY POI file
        if not self.update_country_geojson("pois_geojson_file", poi_file_id):
            return False
        
        time.sleep(3)  # Wait for processing
        
        # Verify only POIs created, not other entities
        poi_count = self.count_entities("pois")
        landuse_count = self.count_entities("landuse-zones")
        region_count = self.count_entities("regions")
        highway_count = self.count_entities("highways")
        
        if poi_count != 2:
            print(f"❌ Expected 2 POIs, got {poi_count}")
            return False
        
        if landuse_count != 0:
            print(f"❌ Expected 0 Landuse zones (POI upload shouldn't create them), got {landuse_count}")
            return False
        
        if region_count != 0:
            print(f"❌ Expected 0 Regions (POI upload shouldn't create them), got {region_count}")
            return False
        
        if highway_count != 0:
            print(f"❌ Expected 0 Highways (POI upload shouldn't create them), got {highway_count}")
            return False
        
        # Cleanup
        self.remove_geojson_file("pois_geojson_file")
        time.sleep(2)
        
        print("\n✅ INDEPENDENCE TEST PASSED")
        return True
    
    def run_all_tests(self):
        """Run all CRUD tests"""
        print("\n" + "="*60)
        print("GEOJSON CRUD TEST SUITE")
        print("="*60)
        
        # We have API token, no need to login
        print("\n[AUTH] Using API token for authentication...")
        
        # Find country
        if not self.find_country():
            print("\n❌ TESTS FAILED - Could not find country")
            return False
        
        # Run tests
        tests = [
            ("POI (Amenities) CRUD", self.test_poi_crud),
            ("Landuse CRUD", self.test_landuse_crud),
            ("Highway CRUD", self.test_highway_crud)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"\n❌ {test_name} FAILED WITH EXCEPTION: {e}")
                import traceback
                traceback.print_exc()
                results.append((test_name, False))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        all_passed = all(result for _, result in results)
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n❌ SOME TESTS FAILED")
        
        return all_passed


if __name__ == "__main__":
    tester = GeoJSONTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
