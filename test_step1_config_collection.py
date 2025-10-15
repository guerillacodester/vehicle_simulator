"""
Test Step 1: Operational Configuration Collection
==================================================
Verifies that the operational-configurations collection exists in Strapi
and can be queried successfully.
"""

import asyncio
import aiohttp
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STRAPI_URL = "http://localhost:1337"


async def test_collection_exists():
    """Test that operational-configurations collection exists and is accessible."""
    
    print("\n" + "="*80)
    print("STEP 1 TEST: OPERATIONAL CONFIGURATION COLLECTION")
    print("="*80 + "\n")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Check if collection is accessible
        print("TEST 1: Collection Accessibility")
        print("-" * 40)
        
        try:
            async with session.get(
                f"{STRAPI_URL}/api/operational-configurations",
                params={"pagination[limit]": 1}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print("   ✅ Collection exists and is accessible")
                    print(f"   📊 Response structure: {list(data.keys())}")
                    
                    if 'data' in data:
                        configs = data['data']
                        print(f"   📊 Number of configurations: {len(configs)}")
                        
                        if len(configs) > 0:
                            # Show first config as example
                            first_config = configs[0]
                            print(f"\n   Example configuration:")
                            print(f"      Section: {first_config.get('section', 'N/A')}")
                            print(f"      Parameter: {first_config.get('parameter', 'N/A')}")
                            print(f"      Value: {first_config.get('value', 'N/A')}")
                            print(f"      Type: {first_config.get('value_type', 'N/A')}")
                        else:
                            print("   ⚠️  No configurations found - collection is empty")
                            print("   Run: python arknet_fleet_manager/seed_operational_config.py")
                    
                    test1_passed = True
                else:
                    print(f"   ❌ Failed to access collection (status: {response.status})")
                    error_text = await response.text()
                    print(f"   Error: {error_text[:200]}")
                    test1_passed = False
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            test1_passed = False
        
        # Test 2: Query specific section
        print("\nTEST 2: Query Specific Section")
        print("-" * 40)
        
        try:
            async with session.get(
                f"{STRAPI_URL}/api/operational-configurations",
                params={
                    "filters[section][$eq]": "conductor.proximity",
                    "pagination[limit]": 10
                }
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    configs = data.get('data', [])
                    print(f"   ✅ Section query successful")
                    print(f"   📊 Found {len(configs)} parameters in 'conductor.proximity'")
                    
                    for config in configs:
                        print(f"      - {config.get('parameter')}: {config.get('value')}")
                    
                    test2_passed = len(configs) > 0
                    if not test2_passed:
                        print("   ⚠️  No parameters found in section")
                else:
                    print(f"   ❌ Query failed (status: {response.status})")
                    test2_passed = False
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            test2_passed = False
        
        # Test 3: Query specific parameter
        print("\nTEST 3: Query Specific Parameter")
        print("-" * 40)
        
        try:
            async with session.get(
                f"{STRAPI_URL}/api/operational-configurations",
                params={
                    "filters[section][$eq]": "conductor.proximity",
                    "filters[parameter][$eq]": "pickup_radius_km"
                }
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    configs = data.get('data', [])
                    
                    if configs:
                        config = configs[0]
                        print(f"   ✅ Parameter found")
                        print(f"      Section: {config.get('section')}")
                        print(f"      Parameter: {config.get('parameter')}")
                        print(f"      Value: {config.get('value')}")
                        print(f"      Type: {config.get('value_type')}")
                        print(f"      Default: {config.get('default_value')}")
                        
                        if config.get('constraints'):
                            print(f"      Constraints: {config.get('constraints')}")
                        
                        test3_passed = True
                    else:
                        print(f"   ⚠️  Parameter not found")
                        test3_passed = False
                else:
                    print(f"   ❌ Query failed (status: {response.status})")
                    test3_passed = False
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            test3_passed = False
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"✅ Collection Accessibility: {'PASS' if test1_passed else 'FAIL'}")
        print(f"✅ Section Query: {'PASS' if test2_passed else 'FAIL'}")
        print(f"✅ Parameter Query: {'PASS' if test3_passed else 'FAIL'}")
        
        all_passed = test1_passed and test2_passed and test3_passed
        
        if all_passed:
            print("\n🎉 STEP 1 COMPLETE: Database schema is ready!")
            print("\nNext: Proceed to Step 2 - Create Configuration Service")
        else:
            print("\n⚠️  Some tests failed. Check:")
            print("   1. Strapi is running")
            print("   2. operational-configurations collection created")
            print("   3. Collection has been seeded with data")
        
        print("="*80 + "\n")
        
        return all_passed


if __name__ == "__main__":
    result = asyncio.run(test_collection_exists())
    
    if not result:
        sys.exit(1)
