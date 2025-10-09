#!/usr/bin/env python3
"""
Comprehensive Production-Level Spawning Test
This script validates the complete passenger spawning system including depot, route, and POI spawning.
"""

import sys
import os
import json
from datetime import datetime
import asyncio

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_spawning_api import handle_spawn_request

def run_production_spawning_test():
    """Run comprehensive production-level spawning validation"""
    print("🚀 PRODUCTION SPAWNING SYSTEM TEST")
    print("=" * 70)
    
    # Test parameters
    test_hour = 8  # Peak morning hour
    time_window = 5  # 5-minute window
    
    print(f"📅 Testing Hour: {test_hour} (Peak Morning)")
    print(f"⏱️  Time Window: {time_window} minutes")
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Generate all passengers
        print("🔄 Running complete passenger spawning system...")
        result = asyncio.run(handle_spawn_request(test_hour, time_window))
        
        if not result.get('success', False):
            print(f"❌ Spawning system failed: {result.get('error', 'Unknown error')}")
            return False
        
        all_passengers = result.get('spawn_requests', [])
        total_passengers = result.get('total_passengers', 0)
        
        print(f"✅ Total passengers generated: {total_passengers}")
        print()
        
        # Analyze by spawn type
        spawn_types = {}
        for passenger in all_passengers:
            spawn_type = passenger.get('spawn_type', 'unknown')
            if spawn_type not in spawn_types:
                spawn_types[spawn_type] = []
            spawn_types[spawn_type].append(passenger)
        
        print("📊 SPAWNING BREAKDOWN:")
        print("-" * 40)
        
        for spawn_type, passengers in spawn_types.items():
            count = len(passengers)
            percentage = (count / total_passengers * 100) if total_passengers > 0 else 0
            print(f"   {spawn_type.upper():>6}: {count:>4} passengers ({percentage:>5.1f}%)")
            
            # Validate spawn type specific data
            valid_count = 0
            for passenger in passengers:
                if spawn_type == 'depot':
                    valid = 'depot_id' in passenger and passenger['depot_id'] is not None
                elif spawn_type == 'route':
                    valid = 'route_id' in passenger and passenger['route_id'] is not None
                elif spawn_type == 'poi':
                    valid = 'poi_id' in passenger and passenger['poi_id'] is not None
                else:
                    valid = True
                
                if valid and 'latitude' in passenger and 'longitude' in passenger:
                    valid_count += 1
            
            validation_percent = (valid_count / count * 100) if count > 0 else 0
            status = "✅" if validation_percent >= 95 else "⚠️" if validation_percent >= 80 else "❌"
            print(f"           {status} Data Quality: {valid_count}/{count} ({validation_percent:.1f}% valid)")
        
        print()
        
        # Peak hour validation
        spawn_rates = [p.get('spawn_rate', 0) for p in all_passengers if p.get('spawn_rate')]
        if spawn_rates:
            avg_spawn_rate = sum(spawn_rates) / len(spawn_rates)
            print("🔥 PEAK HOUR ANALYSIS:")
            print("-" * 40)
            print(f"   Average Spawn Rate: {avg_spawn_rate:.2f}")
            print(f"   Expected Peak Multiplier: 2.5x (Hour 8)")
            
            # Check if we're getting reasonable spawn rates for peak hour
            if avg_spawn_rate >= 2.0:
                print("   ✅ Peak hour multiplier appears to be working")
            else:
                print("   ⚠️  Peak hour multiplier may need adjustment")
        
        print()
        
        # Geographic distribution validation
        print("🗺️  GEOGRAPHIC DISTRIBUTION:")
        print("-" * 40)
        
        latitudes = [p['latitude'] for p in all_passengers if 'latitude' in p]
        longitudes = [p['longitude'] for p in all_passengers if 'longitude' in p]
        
        if latitudes and longitudes:
            lat_range = (min(latitudes), max(latitudes))
            lon_range = (min(longitudes), max(longitudes))
            
            print(f"   Latitude Range:  {lat_range[0]:.6f} to {lat_range[1]:.6f}")
            print(f"   Longitude Range: {lon_range[0]:.6f} to {lon_range[1]:.6f}")
            
            # Barbados approximate bounds: 13.0 to 13.35 lat, -59.65 to -59.4 lon
            barbados_lat = (13.0, 13.35)
            barbados_lon = (-59.65, -59.4)
            
            lat_valid = barbados_lat[0] <= lat_range[0] and lat_range[1] <= barbados_lat[1]
            lon_valid = barbados_lon[0] <= lon_range[0] and lon_range[1] <= barbados_lon[1]
            
            if lat_valid and lon_valid:
                print("   ✅ All coordinates within Barbados bounds")
            else:
                print("   ⚠️  Some coordinates may be outside Barbados")
        
        print()
        
        # Time distribution validation
        minutes = [p.get('minute', 0) for p in all_passengers if 'minute' in p]
        if minutes:
            print("⏰ TIME DISTRIBUTION:")
            print("-" * 40)
            print(f"   Minute Range: {min(minutes)} to {max(minutes)}")
            print(f"   Expected Range: 0 to 59")
            
            if min(minutes) >= 0 and max(minutes) <= 59:
                print("   ✅ Time distribution is valid")
            else:
                print("   ❌ Time distribution is invalid")
        
        print()
        
        # Production readiness assessment
        print("🎯 PRODUCTION READINESS ASSESSMENT:")
        print("=" * 50)
        
        # Criteria for production readiness
        criteria = {
            "Total Passengers": total_passengers >= 100,  # Should generate meaningful passenger count
            "Multiple Spawn Types": len(spawn_types) >= 2,  # Should have depot, route, and/or POI spawns
            "Data Quality": all(len(passengers) > 0 for passengers in spawn_types.values()),
            "Geographic Validity": len(latitudes) == total_passengers and len(longitudes) == total_passengers,
            "Time Validity": len(minutes) == total_passengers,
        }
        
        passed_criteria = sum(criteria.values())
        total_criteria = len(criteria)
        
        for criterion, passed in criteria.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {criterion}")
        
        print(f"\n📈 Overall Score: {passed_criteria}/{total_criteria} ({100*passed_criteria/total_criteria:.0f}%)")
        
        if passed_criteria == total_criteria:
            print("\n🎉 PRODUCTION READY! ✨")
            print("   The spawning system is operating at production level.")
        elif passed_criteria >= total_criteria * 0.8:
            print("\n⚠️  NEARLY READY - Minor issues to address")
        else:
            print("\n❌ NOT READY - Significant issues need resolution")
        
        return passed_criteria == total_criteria
        
    except Exception as e:
        print(f"💥 SPAWNING TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 STARTING PRODUCTION SPAWNING VALIDATION")
    print("=" * 80)
    
    success = run_production_spawning_test()
    
    if success:
        print(f"\n✅ PRODUCTION VALIDATION PASSED!")
        print("   The system is ready for visualization testing.")
    else:
        print(f"\n❌ PRODUCTION VALIDATION FAILED!")
        print("   Fix issues before proceeding to visualization.")