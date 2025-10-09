#!/usr/bin/env python3
"""
Test Depot Reservoir Functionality in Isolation
This script tests the depot passenger spawning system independently.
"""

import sys
import os
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_spawning_api import DatabaseSpawningAPI

def test_depot_reservoir():
    """Test depot reservoir functionality with detailed output"""
    print("🏪 DEPOT RESERVOIR TEST")
    print("=" * 50)
    
    # Test parameters
    test_hour = 8  # Peak morning hour
    time_window = 5  # 5-minute window
    
    print(f"📅 Testing Hour: {test_hour}")
    print(f"⏱️  Time Window: {time_window} minutes")
    print()
    
    # Generate passengers using database API and filter for depot only
    print("🔄 Generating depot passengers...")
    import asyncio
    from database_spawning_api import handle_spawn_request
    
    result = asyncio.run(handle_spawn_request(test_hour, time_window))
    all_passengers = result.get('spawn_requests', [])
    passengers = [p for p in all_passengers if p.get('spawn_type') == 'depot']
    
    # Analyze results
    print(f"✅ Generated {len(passengers)} depot passengers")
    print()
    
    if passengers:
        # Show sample passengers
        print("📋 Sample Passengers (first 5):")
        for i, passenger in enumerate(passengers[:5]):
            print(f"  {i+1}. Depot ID: {passenger.get('depot_id', 'N/A')}")
            print(f"     Location: ({passenger['latitude']:.6f}, {passenger['longitude']:.6f})")
            print(f"     Spawn Type: {passenger['spawn_type']}")
            print(f"     Location Name: {passenger.get('location_name', 'N/A')}")
            print(f"     Zone Type: {passenger.get('zone_type', 'N/A')}")
            print(f"     Spawn Rate: {passenger.get('spawn_rate', 'N/A')}")
            print(f"     Minute: {passenger.get('minute', 'N/A')}")
            print()
        
        # Statistics
        depot_ids = set(p.get('depot_id') for p in passengers if p.get('depot_id'))
        spawn_rates = [p.get('spawn_rate', 0) for p in passengers]
        minutes = [p.get('minute', 0) for p in passengers]
        
        print("📊 DEPOT STATISTICS:")
        print(f"   • Total Passengers: {len(passengers)}")
        print(f"   • Unique Depots: {len(depot_ids)}")
        print(f"   • Depot IDs: {sorted(depot_ids) if depot_ids else 'None'}")
        print(f"   • Average Spawn Rate: {sum(spawn_rates)/len(spawn_rates):.2f}" if spawn_rates else "   • Average Spawn Rate: N/A")
        print(f"   • Minute Range: {min(minutes)}-{max(minutes)}" if minutes else "   • Minute Range: N/A")
        
        # Verify data integrity
        print("\n🔍 DATA VALIDATION:")
        valid_passengers = 0
        for passenger in passengers:
            has_coords = 'latitude' in passenger and 'longitude' in passenger
            has_spawn_type = passenger.get('spawn_type') == 'depot'
            has_depot_id = 'depot_id' in passenger and passenger['depot_id'] is not None
            
            if has_coords and has_spawn_type and has_depot_id:
                valid_passengers += 1
        
        print(f"   • Valid Passengers: {valid_passengers}/{len(passengers)} ({100*valid_passengers/len(passengers):.1f}%)")
        
        # Peak hour multiplier check
        peak_multipliers = [p.get('spawn_rate', 0) for p in passengers]
        expected_multiplier = 2.5  # Hour 8 should have 2.5x multiplier
        
        if peak_multipliers:
            avg_multiplier = sum(peak_multipliers) / len(peak_multipliers)
            print(f"   • Peak Hour Multiplier: {avg_multiplier:.2f} (expected: {expected_multiplier})")
            
            multiplier_match = abs(avg_multiplier - expected_multiplier) < 0.1
            print(f"   • Multiplier Correct: {'✅' if multiplier_match else '❌'}")
        
    else:
        print("❌ NO PASSENGERS GENERATED!")
        print("   This indicates a problem with depot data or configuration.")
    
    print("\n" + "=" * 50)
    print("🏪 DEPOT RESERVOIR TEST COMPLETE")
    
    return len(passengers) > 0, passengers

def test_depot_data_source():
    """Test the underlying depot data source"""
    print("\n🔧 DEPOT DATA SOURCE TEST")
    print("=" * 30)
    
    try:
        # Test database connection by getting depot data through API
        import asyncio
        from database_spawning_api import DatabaseSpawningAPI
        
        db_api = DatabaseSpawningAPI()
        data = asyncio.run(db_api.get_database_data())
        depots = data.get('depots', [])
        
        if depots:
            print(f"✅ Depot data loaded: {len(depots)} depots")
            
            # Show sample depot data
            print("\n📋 Sample Depot Data (first 3):")
            for i, depot in enumerate(depots[:3]):
                print(f"  {i+1}. ID: {depot.get('id', 'N/A')}")
                print(f"     Name: {depot.get('name', 'N/A')}")
                print(f"     Location: ({depot.get('latitude', 'N/A')}, {depot.get('longitude', 'N/A')})")
                print(f"     Capacity: {depot.get('capacity', 'N/A')}")
                print()
        else:
            print("❌ No depot data found!")
            print("   Check database connection and depots table.")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("   Check PostgreSQL connection and credentials.")

if __name__ == "__main__":
    print("🚀 STARTING DEPOT RESERVOIR ISOLATION TEST")
    print("=" * 60)
    
    try:
        # Test data source first
        test_depot_data_source()
        
        # Test passenger generation
        success, passengers = test_depot_reservoir()
        
        if success:
            print(f"\n🎉 DEPOT TEST PASSED! Generated {len(passengers)} passengers")
        else:
            print(f"\n❌ DEPOT TEST FAILED! No passengers generated")
            
    except Exception as e:
        print(f"\n💥 DEPOT TEST ERROR: {e}")
        import traceback
        traceback.print_exc()