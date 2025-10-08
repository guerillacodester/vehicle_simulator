#!/usr/bin/env python3
"""
Step 2 Validation: Geographic Data Pagination Test
===================================================

Tests our ability to retrieve the full geographic dataset (11,870+ features) 
using proper pagination parameters before integrating with Poisson spawner.

SUCCESS CRITERIA (Must achieve 100% - 4/4 tests passing):
✅ 1. POIs retrieval with high pagination (target: 1,419+ POIs)
✅ 2. Places retrieval with high pagination (target: 8,283+ Places)  
✅ 3. Landuse retrieval with high pagination (target: 2,168+ Landuse)
✅ 4. Total geographic features validation (target: 11,870+ total)

This test must show 100% success before proceeding to Step 3.
"""

import asyncio
import sys
import os

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def validate_geographic_pagination():
    """
    Validate geographic data pagination - Step 2 of Poisson Spawner Integration
    """
    print("="*70)
    print("STEP 2 VALIDATION: Geographic Data Pagination")
    print("="*70)
    print("Target: Validate retrieval of full geographic dataset (11,870+ features)")
    print("Required Success Rate: 4/4 tests (100%)")
    print()
    
    success_count = 0
    total_tests = 4
    
    # Expected minimums based on discovery
    expected_pois = 1419
    expected_places = 8283  
    expected_landuse = 2168
    expected_total = 11870
    
    # Initialize API client
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        # Connect to API
        print("Initializing API client connection...")
        connection_success = await client.connect()
        
        if not connection_success:
            print("❌ CRITICAL: Cannot establish API connection")
            print("\nStep 2 Status: FAILED - 0/4 tests passed")
            return success_count, total_tests
        
        # Test 1: POIs Retrieval with High Pagination
        print("\nTest 1: POIs Retrieval (Points of Interest)")
        print("-" * 45)
        try:
            response = await client.session.get(
                f"{client.base_url}/api/pois",
                params={
                    "pagination[pageSize]": 50000,  # High pagination limit
                    "pagination[page]": 1
                }
            )
            if response.status_code == 200:
                data = response.json()
                pois = data.get("data", [])
                poi_count = len(pois)
                print(f"✅ POIs retrieved: {poi_count} features")
                
                if poi_count >= expected_pois:
                    print(f"✅ POIs count meets expectation (>= {expected_pois})")
                    success_count += 1
                else:
                    print(f"❌ POIs count below expectation ({poi_count} < {expected_pois})")
            else:
                print(f"❌ POIs retrieval failed - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ POIs retrieval failed: {e}")
        
        # Test 2: Places Retrieval with High Pagination
        print("\nTest 2: Places Retrieval")
        print("-" * 25)
        try:
            response = await client.session.get(
                f"{client.base_url}/api/places",
                params={
                    "pagination[pageSize]": 50000,  # High pagination limit
                    "pagination[page]": 1
                }
            )
            if response.status_code == 200:
                data = response.json()
                places = data.get("data", [])
                places_count = len(places)
                print(f"✅ Places retrieved: {places_count} features")
                
                if places_count >= expected_places:
                    print(f"✅ Places count meets expectation (>= {expected_places})")
                    success_count += 1
                else:
                    print(f"❌ Places count below expectation ({places_count} < {expected_places})")
            else:
                print(f"❌ Places retrieval failed - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Places retrieval failed: {e}")
        
        # Test 3: Landuse Retrieval with High Pagination
        print("\nTest 3: Landuse Retrieval")
        print("-" * 26)
        try:
            response = await client.session.get(
                f"{client.base_url}/api/landuses",
                params={
                    "pagination[pageSize]": 50000,  # High pagination limit
                    "pagination[page]": 1
                }
            )
            if response.status_code == 200:
                data = response.json()
                landuses = data.get("data", [])
                landuse_count = len(landuses)
                print(f"✅ Landuse retrieved: {landuse_count} features")
                
                if landuse_count >= expected_landuse:
                    print(f"✅ Landuse count meets expectation (>= {expected_landuse})")
                    success_count += 1
                else:
                    print(f"❌ Landuse count below expectation ({landuse_count} < {expected_landuse})")
            else:
                print(f"❌ Landuse retrieval failed - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Landuse retrieval failed: {e}")
        
        # Test 4: Total Geographic Features Validation
        print("\nTest 4: Total Geographic Features Count")
        print("-" * 38)
        try:
            # Re-fetch all counts for total calculation
            pois_response = await client.session.get(
                f"{client.base_url}/api/pois",
                params={"pagination[pageSize]": 50000}
            )
            places_response = await client.session.get(
                f"{client.base_url}/api/places",
                params={"pagination[pageSize]": 50000}
            )
            landuse_response = await client.session.get(
                f"{client.base_url}/api/landuses",
                params={"pagination[pageSize]": 50000}
            )
            
            total_features = 0
            if pois_response.status_code == 200:
                total_features += len(pois_response.json().get("data", []))
            if places_response.status_code == 200:
                total_features += len(places_response.json().get("data", []))
            if landuse_response.status_code == 200:
                total_features += len(landuse_response.json().get("data", []))
            
            print(f"✅ Total geographic features: {total_features}")
            
            if total_features >= expected_total:
                print(f"✅ Total features meet expectation (>= {expected_total})")
                success_count += 1
            else:
                print(f"❌ Total features below expectation ({total_features} < {expected_total})")
                
        except Exception as e:
            print(f"❌ Total features calculation failed: {e}")
            
    finally:
        await client.close()
    
    # Results Summary
    print("\n" + "="*70)
    print("STEP 2 VALIDATION RESULTS")
    print("="*70)
    print(f"Tests Passed: {success_count}/{total_tests}")
    print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("✅ STEP 2: PASSED - Geographic Data Pagination is working")
        print("✅ READY to proceed to Step 3: Poisson Mathematical Foundation")
    else:
        print("❌ STEP 2: FAILED - Geographic Data Pagination needs fixes")
        print("❌ DO NOT proceed to Step 3 until this shows 100% success")
    
    print("="*70)
    
    return success_count, total_tests

def main():
    """Main execution function"""
    try:
        success, total = asyncio.run(validate_geographic_pagination())
        
        # Exit with appropriate code
        if success == total:
            print(f"\n🎯 SUCCESS: Step 2 validation complete ({success}/{total})")
            sys.exit(0)
        else:
            print(f"\n💥 FAILURE: Step 2 validation failed ({success}/{total})")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()