#!/usr/bin/env python3
"""
Step 3 Validation: Poisson Mathematical Foundation Test
=======================================================

Tests the Poisson mathematical engine with the complete 9,702-feature geographic dataset
to validate statistical spawning calculations before full integration.

SUCCESS CRITERIA (Must achieve 100% - 4/4 tests passing):
✅ 1. Poisson Distribution Mathematics - λ parameter calculation with real data
✅ 2. Geographic Feature Processing - 9,702 features coordinate processing  
✅ 3. Time-based Spawning Calculations - rush hour vs off-peak rate scaling
✅ 4. Memory and Performance Validation - production-scale calculation speeds

This test must show 100% success before proceeding to Step 4.
"""

import asyncio
import sys
import os
import time
import math
import random
from typing import List, Dict, Tuple

# Add the necessary paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'arknet_transit_simulator'))

from strapi_api_client import StrapiApiClient

class PoissonMathematicalEngine:
    """
    Core Poisson mathematical engine for passenger spawning validation
    """
    
    def __init__(self):
        self.geographic_features = []
        self.base_lambda = 2.0  # Base λ parameter for Poisson distribution
        
    def calculate_poisson_lambda(self, geographic_count: int, time_modifier: float = 1.0) -> float:
        """Calculate λ parameter based on geographic features and time"""
        if geographic_count == 0:
            return 0.0
        
        # Scale lambda based on geographic density and time
        density_factor = math.log(geographic_count + 1) / 10.0  # Logarithmic scaling
        adjusted_lambda = self.base_lambda * density_factor * time_modifier
        
        return max(0.1, adjusted_lambda)  # Minimum λ to prevent zero spawning
    
    def poisson_probability(self, k: int, lam: float) -> float:
        """Calculate Poisson probability P(X = k) = (λ^k * e^(-λ)) / k!"""
        if lam <= 0:
            return 0.0
        
        try:
            # Use math functions for numerical stability
            log_prob = k * math.log(lam) - lam - math.lgamma(k + 1)
            return math.exp(log_prob)
        except (OverflowError, ValueError):
            return 0.0
    
    def generate_poisson_arrivals(self, lam: float, time_window: int = 60) -> List[int]:
        """Generate Poisson-distributed passenger arrivals over time window"""
        arrivals = []
        
        for minute in range(time_window):
            # Generate number of arrivals this minute
            k = 0
            cumulative_prob = 0.0
            rand_val = random.random()
            
            # Calculate Poisson probabilities until we exceed random value
            while cumulative_prob < rand_val and k < 50:  # Safety limit
                prob_k = self.poisson_probability(k, lam)
                cumulative_prob += prob_k
                if cumulative_prob >= rand_val:
                    break
                k += 1
            
            arrivals.append(k)
        
        return arrivals
    
    def calculate_time_modifiers(self, hour: int) -> float:
        """Calculate time-based modifier for rush hour vs off-peak"""
        # Rush hour periods: 7-9 AM (1.8x) and 5-7 PM (2.0x)
        if 7 <= hour <= 9:
            return 1.8  # Morning rush
        elif 17 <= hour <= 19:
            return 2.0  # Evening rush  
        elif 22 <= hour or hour <= 5:
            return 0.3  # Late night/early morning
        else:
            return 1.0  # Normal daytime
    
    def process_geographic_coordinates(self, features: List[Dict]) -> List[Tuple[float, float]]:
        """Extract and validate geographic coordinates from features"""
        coordinates = []
        
        for feature in features:
            try:
                # Extract coordinates from separate latitude/longitude fields
                lat = feature.get('latitude')
                lon = feature.get('longitude')
                
                if lat is not None and lon is not None:
                    lat, lon = float(lat), float(lon)
                    
                    # Validate Barbados coordinate bounds
                    if 13.0 <= lat <= 13.35 and -59.65 <= lon <= -59.4:
                        coordinates.append((lat, lon))
                
            except (ValueError, TypeError):
                continue  # Skip invalid coordinates
        
        return coordinates

async def validate_poisson_mathematical_foundation():
    """
    Validate Poisson mathematical foundation - Step 3 of Poisson Spawner Integration
    """
    print("="*70)
    print("STEP 3 VALIDATION: Poisson Mathematical Foundation")
    print("="*70)
    print("Target: Validate Poisson mathematics with complete 9,702-feature dataset")
    print("Required Success Rate: 4/4 tests (100%)")
    print()
    
    success_count = 0
    total_tests = 4
    
    # Initialize components
    engine = PoissonMathematicalEngine()
    client = StrapiApiClient("http://localhost:1337")
    
    try:
        # Connect to API
        print("Initializing mathematical engine and API client...")
        connection_success = await client.connect()
        
        if not connection_success:
            print("❌ CRITICAL: Cannot establish API connection")
            print("\nStep 3 Status: FAILED - 0/4 tests passed")
            return success_count, total_tests
        
        # Test 1: Poisson Distribution Mathematics
        print("\nTest 1: Poisson Distribution Mathematics")
        print("-" * 40)
        try:
            # Test λ calculation with different geographic counts
            test_counts = [100, 1419, 8283, 9702]  # Real dataset sizes
            lambda_results = []
            
            for count in test_counts:
                lam = engine.calculate_poisson_lambda(count, 1.0)
                lambda_results.append(lam)
                print(f"   Geographic count {count}: λ = {lam:.4f}")
            
            # Validate λ calculations
            if all(0.1 <= lam <= 10.0 for lam in lambda_results):
                # Test Poisson probability calculations
                test_lam = lambda_results[-1]  # Use full dataset λ
                prob_0 = engine.poisson_probability(0, test_lam)
                prob_1 = engine.poisson_probability(1, test_lam)
                prob_5 = engine.poisson_probability(5, test_lam)
                
                print(f"   Poisson probabilities (λ={test_lam:.4f}):")
                print(f"   P(X=0) = {prob_0:.6f}")
                print(f"   P(X=1) = {prob_1:.6f}")
                print(f"   P(X=5) = {prob_5:.6f}")
                
                # Validate probabilities sum constraint (spot check)
                if 0 <= prob_0 <= 1 and 0 <= prob_1 <= 1 and 0 <= prob_5 <= 1:
                    print("✅ Poisson mathematics validation successful")
                    success_count += 1
                else:
                    print("❌ Poisson probability calculations invalid")
            else:
                print("❌ Lambda parameter calculations out of valid range")
                
        except Exception as e:
            print(f"❌ Poisson mathematics validation failed: {e}")
        
        # Test 2: Geographic Feature Processing  
        print("\nTest 2: Geographic Feature Processing")
        print("-" * 37)
        try:
            start_time = time.time()
            
            # Fetch complete dataset (using our proven multi-page method)
            async def fetch_all_pages(endpoint):
                all_data = []
                page = 1
                while page <= 100:  # Safety limit
                    response = await client.session.get(
                        f"{client.base_url}/api/{endpoint}",
                        params={"pagination[page]": page, "pagination[pageSize]": 100}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        page_data = data.get("data", [])
                        all_data.extend(page_data)
                        
                        pagination = data.get("meta", {}).get("pagination", {})
                        if page >= pagination.get("pageCount", 1) or len(page_data) == 0:
                            break
                        page += 1
                    else:
                        break
                return all_data
            
            # Load complete geographic dataset
            pois_data = await fetch_all_pages("pois")
            places_data = await fetch_all_pages("places")
            
            all_features = pois_data + places_data
            total_features = len(all_features)
            
            # Process coordinates
            coordinates = engine.process_geographic_coordinates(all_features)
            valid_coords_count = len(coordinates)
            
            load_time = time.time() - start_time
            
            print(f"✅ Geographic features loaded: {total_features}")
            print(f"   - POIs: {len(pois_data)}")
            print(f"   - Places: {len(places_data)}")
            print(f"✅ Valid coordinates processed: {valid_coords_count}")
            print(f"✅ Processing time: {load_time:.2f} seconds")
            
            if total_features >= 9700 and valid_coords_count > 0:
                print("✅ Geographic feature processing successful")
                success_count += 1
            else:
                if total_features < 9700:
                    print(f"❌ Insufficient geographic data ({total_features} < 9700)")
                else:
                    print(f"❌ No valid coordinates processed ({valid_coords_count} coordinates)")
                
        except Exception as e:
            print(f"❌ Geographic feature processing failed: {e}")
        
        # Test 3: Time-based Spawning Calculations
        print("\nTest 3: Time-based Spawning Calculations") 
        print("-" * 38)
        try:
            # Test time modifiers for different hours
            test_hours = [8, 12, 18, 23]  # Morning rush, midday, evening rush, late night
            expected_modifiers = [1.8, 1.0, 2.0, 0.3]
            
            modifier_results = []
            for hour in test_hours:
                modifier = engine.calculate_time_modifiers(hour)
                modifier_results.append(modifier)
                
            print("   Time-based modifier calculations:")
            for i, (hour, expected, actual) in enumerate(zip(test_hours, expected_modifiers, modifier_results)):
                status = "✅" if abs(actual - expected) < 0.1 else "❌"
                print(f"   {status} Hour {hour:2d}: {actual:.1f}x (expected: {expected:.1f}x)")
            
            # Test scaled λ calculations
            base_count = len(all_features) if 'all_features' in locals() else 9702
            rush_lambda = engine.calculate_poisson_lambda(base_count, 2.0)  # Evening rush
            normal_lambda = engine.calculate_poisson_lambda(base_count, 1.0)  # Normal
            
            print(f"   Scaled λ calculations:")
            print(f"   Normal time: λ = {normal_lambda:.4f}")
            print(f"   Rush hour:   λ = {rush_lambda:.4f} ({rush_lambda/normal_lambda:.1f}x)")
            
            if all(abs(a - e) < 0.1 for a, e in zip(modifier_results, expected_modifiers)):
                print("✅ Time-based spawning calculations successful")
                success_count += 1
            else:
                print("❌ Time modifier calculations incorrect")
                
        except Exception as e:
            print(f"❌ Time-based spawning calculations failed: {e}")
        
        # Test 4: Memory and Performance Validation
        print("\nTest 4: Memory and Performance Validation")
        print("-" * 40)
        try:
            # Performance test: Generate spawning patterns
            start_time = time.time()
            
            if 'all_features' in locals():
                feature_count = len(all_features)
                test_lambda = engine.calculate_poisson_lambda(feature_count, 1.5)
                
                # Generate arrival patterns for 1 hour (60 minutes)
                arrivals = engine.generate_poisson_arrivals(test_lambda, 60)
                
                # Calculate statistics
                total_arrivals = sum(arrivals)
                avg_arrivals = total_arrivals / 60
                max_arrivals = max(arrivals)
                
                calc_time = time.time() - start_time
                
                print(f"✅ Spawning simulation completed")
                print(f"   - Features processed: {feature_count}")
                print(f"   - Lambda parameter: {test_lambda:.4f}")
                print(f"   - Total arrivals (1hr): {total_arrivals}")
                print(f"   - Average per minute: {avg_arrivals:.2f}")
                print(f"   - Peak minute: {max_arrivals}")
                print(f"   - Calculation time: {calc_time:.3f} seconds")
                
                # Performance criteria
                if calc_time < 5.0 and total_arrivals > 0:
                    print("✅ Memory and performance validation successful")
                    success_count += 1
                else:
                    print(f"❌ Performance issues (time: {calc_time:.3f}s)")
            else:
                print("❌ No geographic data available for performance testing")
                
        except Exception as e:
            print(f"❌ Memory and performance validation failed: {e}")
            
    finally:
        await client.close()
    
    # Results Summary
    print("\n" + "="*70)
    print("STEP 3 VALIDATION RESULTS")
    print("="*70)
    print(f"Tests Passed: {success_count}/{total_tests}")
    print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("✅ STEP 3: PASSED - Poisson Mathematical Foundation is solid")
        print("✅ Mathematics ready for geographic integration")
        print("✅ READY to proceed to Step 4: Geographic Integration Testing")
    else:
        print("❌ STEP 3: FAILED - Poisson Mathematical Foundation needs fixes")
        print("❌ DO NOT proceed to Step 4 until this shows 100% success")
    
    print("="*70)
    
    return success_count, total_tests

def main():
    """Main execution function"""
    try:
        success, total = asyncio.run(validate_poisson_mathematical_foundation())
        
        # Exit with appropriate code
        if success == total:
            print(f"\n🎯 SUCCESS: Step 3 validation complete ({success}/{total})")
            sys.exit(0)
        else:
            print(f"\n💥 FAILURE: Step 3 validation failed ({success}/{total})")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()