#!/usr/bin/env python3
"""
Step 1 Validation: API Client Foundation Test (CORRECTED)
========================================================

Tests the StrapiApiClient foundation before proceeding with spawner integration.
Uses correct httpx methods from actual implementation.

SUCCESS CRITERIA (Must achieve 100% - 4/4 tests passing):
✅ 1. API connection to Strapi server  
✅ 2. Country list retrieval with data
✅ 3. Barbados country lookup success
✅ 4. Valid Barbados country ID confirmation

This test must show 100% success before proceeding to Step 2.
"""

import asyncio
import sys
import os

# Add the commuter service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from strapi_api_client import StrapiApiClient

async def validate_api_client_foundation():
    """
    Validate API client foundation - Step 1 of Poisson Spawner Integration
    """
    print("="*70)
    print("STEP 1 VALIDATION: API Client Foundation")
    print("="*70)
    print("Target: Validate basic Strapi API connectivity and data access")
    print("Required Success Rate: 4/4 tests (100%)")
    print()
    
    success_count = 0
    total_tests = 4
    
    # Initialize API client
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        # Connect to API
        print("Initializing API client connection...")
        connection_success = await client.connect()
        
        if not connection_success:
            print("❌ CRITICAL: Cannot establish API connection")
            print("\nStep 1 Status: FAILED - 0/4 tests passed")
            return success_count, total_tests
        
        # Test 1: Basic API Connection
        print("\nTest 1: Basic API Connection")
        print("-" * 30)
        try:
            response = await client.session.get(f"{client.base_url}/api/countries")
            if response.status_code == 200:
                print("✅ API connection successful")
                success_count += 1
            else:
                print(f"❌ API connection failed - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ API connection failed: {e}")
        
        # Test 2: Country List Retrieval
        print("\nTest 2: Country List Retrieval")
        print("-" * 30)
        try:
            response = await client.session.get(
                f"{client.base_url}/api/countries",
                params={"pagination[pageSize]": 100}
            )
            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    countries = data["data"]
                    print(f"✅ Countries retrieved: {len(countries)} countries found")
                    success_count += 1
                    
                    # Show sample countries
                    print("   Sample countries:")
                    for country in countries[:3]:
                        name = country.get('name', 'Unknown')
                        cid = country.get('id', 'Unknown')
                        print(f"   - {name} (ID: {cid})")
                else:
                    print("❌ Countries retrieval failed - no data field or empty")
            else:
                print(f"❌ Countries retrieval failed - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Countries retrieval failed: {e}")
        
        # Test 3: Barbados Lookup
        print("\nTest 3: Barbados Country Lookup")
        print("-" * 30)
        try:
            response = await client.session.get(
                f"{client.base_url}/api/countries",
                params={
                    "filters[name][$eqi]": "barbados",  # Case-insensitive exact match
                    "pagination[pageSize]": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                barbados_list = data.get("data", [])
                
                if barbados_list and len(barbados_list) > 0:
                    barbados = barbados_list[0]
                    country_id = barbados.get("id")
                    country_name = barbados.get("name")
                    print(f"✅ Barbados found: {country_name} (ID: {country_id})")
                    success_count += 1
                    
                    # Test 4: Validate Country ID
                    print("\nTest 4: Barbados Country ID Validation")
                    print("-" * 30)
                    if isinstance(country_id, int) and country_id > 0:
                        print(f"✅ Valid country ID confirmed: {country_id}")
                        success_count += 1
                    else:
                        print(f"❌ Invalid country ID: {country_id} (type: {type(country_id)})")
                else:
                    print("❌ Barbados not found in countries")
            else:
                print(f"❌ Barbados lookup failed - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Barbados lookup failed: {e}")
            
    finally:
        await client.close()
    
    # Results Summary
    print("\n" + "="*70)
    print("STEP 1 VALIDATION RESULTS")
    print("="*70)
    print(f"Tests Passed: {success_count}/{total_tests}")
    print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("✅ STEP 1: PASSED - API Client Foundation is solid")
        print("✅ READY to proceed to Step 2: Geographic Data Pagination")
    else:
        print("❌ STEP 1: FAILED - API Client Foundation needs fixes")
        print("❌ DO NOT proceed to Step 2 until this shows 100% success")
    
    print("="*70)
    
    return success_count, total_tests

def main():
    """Main execution function"""
    try:
        success, total = asyncio.run(validate_api_client_foundation())
        
        # Exit with appropriate code
        if success == total:
            print(f"\n🎯 SUCCESS: Step 1 validation complete ({success}/{total})")
            sys.exit(0)
        else:
            print(f"\n💥 FAILURE: Step 1 validation failed ({success}/{total})")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()