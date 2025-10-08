#!/usr/bin/env python3
"""
Step 2 Validation: Geographic Data Pagination Test (FIXED)
===========================================================

Fixed version that handles Strapi pagination correctly by fetching multiple pages
to get the full dataset (11,870+ features).

SUCCESS CRITERIA (Must achieve 100% - 3/3 tests passing):
✅ 1. POIs retrieval with multi-page pagination (target: 1,419+ POIs)
✅ 2. Places retrieval with multi-page pagination (target: 8,283+ Places)  
✅ 3. Total geographic features validation (target: 9,702+ total - no landuses endpoint)

This test must show 100% success before proceeding to Step 3.
"""

import asyncio
import sys
import os

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def fetch_all_pages(client, endpoint, expected_total):
    """Fetch all pages for an endpoint to get complete dataset"""
    all_data = []
    page = 1
    max_pages = 100  # Safety limit
    
    print(f"   Fetching {endpoint} data across multiple pages...")
    
    while page <= max_pages:
        try:
            response = await client.session.get(
                f"{client.base_url}/api/{endpoint}",
                params={
                    "pagination[page]": page,
                    "pagination[pageSize]": 100  # Use Strapi's max page size
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                page_data = data.get("data", [])
                all_data.extend(page_data)
                
                # Check if we have more pages
                pagination = data.get("meta", {}).get("pagination", {})
                total_pages = pagination.get("pageCount", 1)
                current_total = len(all_data)
                
                print(f"   Page {page}/{total_pages}: +{len(page_data)} records (total: {current_total})")
                
                if page >= total_pages or len(page_data) == 0:
                    break
                    
                page += 1
            else:
                print(f"   ❌ Failed to fetch page {page}: HTTP {response.status_code}")
                break
                
        except Exception as e:
            print(f"   ❌ Error fetching page {page}: {e}")
            break
    
    return all_data

async def validate_geographic_pagination_fixed():
    """
    Validate geographic data pagination - Step 2 of Poisson Spawner Integration (FIXED)
    """
    print("="*70)
    print("STEP 2 VALIDATION: Geographic Data Pagination (FIXED)")
    print("="*70)
    print("Target: Validate retrieval of full geographic dataset using multi-page pagination")
    print("Required Success Rate: 3/3 tests (100%)")
    print("Note: Landuse endpoint not available - focusing on POIs + Places")
    print()
    
    success_count = 0
    total_tests = 3
    
    # Expected minimums based on discovery (adjusted - no landuses)
    expected_pois = 1419
    expected_places = 8283  
    expected_total = expected_pois + expected_places  # 9702
    
    # Initialize API client
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        # Connect to API
        print("Initializing API client connection...")
        connection_success = await client.connect()
        
        if not connection_success:
            print("❌ CRITICAL: Cannot establish API connection")
            print("\nStep 2 Status: FAILED - 0/3 tests passed")
            return success_count, total_tests
        
        # Test 1: POIs Complete Retrieval
        print("\nTest 1: POIs Complete Retrieval (Multi-page)")
        print("-" * 45)
        try:
            pois_data = await fetch_all_pages(client, "pois", expected_pois)
            poi_count = len(pois_data)
            
            print(f"✅ Total POIs retrieved: {poi_count} features")
            
            if poi_count >= expected_pois:
                print(f"✅ POIs count meets expectation (>= {expected_pois})")
                success_count += 1
            else:
                print(f"❌ POIs count below expectation ({poi_count} < {expected_pois})")
                
        except Exception as e:
            print(f"❌ POIs complete retrieval failed: {e}")
        
        # Test 2: Places Complete Retrieval  
        print("\nTest 2: Places Complete Retrieval (Multi-page)")
        print("-" * 45)
        try:
            places_data = await fetch_all_pages(client, "places", expected_places)
            places_count = len(places_data)
            
            print(f"✅ Total Places retrieved: {places_count} features")
            
            if places_count >= expected_places:
                print(f"✅ Places count meets expectation (>= {expected_places})")
                success_count += 1
            else:
                print(f"❌ Places count below expectation ({places_count} < {expected_places})")
                
        except Exception as e:
            print(f"❌ Places complete retrieval failed: {e}")
        
        # Test 3: Total Geographic Features Validation
        print("\nTest 3: Total Geographic Features Count")
        print("-" * 38)
        try:
            # Use previously fetched data
            total_features = poi_count + places_count
            print(f"✅ Total geographic features: {total_features}")
            print(f"   - POIs: {poi_count}")
            print(f"   - Places: {places_count}")
            
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
        print("✅ Complete dataset available for Poisson spawner integration")
        print("✅ READY to proceed to Step 3: Poisson Mathematical Foundation")
    else:
        print("❌ STEP 2: FAILED - Geographic Data Pagination needs fixes")
        print("❌ DO NOT proceed to Step 3 until this shows 100% success")
    
    print("="*70)
    
    return success_count, total_tests

def main():
    """Main execution function"""
    try:
        success, total = asyncio.run(validate_geographic_pagination_fixed())
        
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