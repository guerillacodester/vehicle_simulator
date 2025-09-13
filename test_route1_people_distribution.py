#!/usr/bin/env python3
"""
Test People Distribution for Route 1
====================================

This test demonstrates the people simulator generating passengers for Route 1
with realistic distribution patterns including peak times and passenger flow.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from world.arknet_transit_simulator.models.people import (
    PoissonDistributionModel, 
    PeopleSimulator, 
    create_poisson_people_simulator
)

# Configure logging to see passenger generation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_route1_people_distribution():
    """Test people distribution patterns for Route 1."""
    
    print("🚌 PEOPLE DISTRIBUTION TEST FOR ROUTE 1")
    print("=" * 60)
    print("📋 This test demonstrates:")
    print("   • Passenger generation using Poisson distribution")
    print("   • Peak time modeling (higher generation rates)")
    print("   • Realistic pickup and destination coordinates")
    print("   • Passenger lifecycle management")
    print("   • Real-time statistics and monitoring")
    print()
    
    try:
        print("🔧 Step 1: Initialize people simulator...")
        
        # Create Poisson distribution model with realistic parameters
        distribution_model = PoissonDistributionModel(
            base_lambda=3.0,        # 3 passengers per minute base rate
            peak_multiplier=2.5,    # 2.5x during peak hours
            weekend_multiplier=0.7, # 70% of weekday traffic on weekends
            min_journey_km=1.0,     # Minimum 1km journey
            max_journey_km=15.0,    # Maximum 15km journey
            business_area_boost=1.3 # 30% boost in business areas
        )
        
        # Create people simulator
        people_sim = PeopleSimulator(
            distribution_model=distribution_model,
            generation_interval=5.0,  # Generate passengers every 5 seconds
            cleanup_interval=10.0     # Clean up completed passengers every 10 seconds
        )
        
        # Set available routes (Route 1 only for this test)
        people_sim.set_available_routes(["route1"])
        
        print("   ✅ People simulator initialized")
        print(f"   📊 Model: {distribution_model.get_model_name()}")
        print(f"   ⚙️  Parameters: {distribution_model.get_model_parameters()}")
        print()
        
        print("🚀 Step 2: Start passenger generation for Route 1...")
        simulation_duration = 60  # Run for 60 seconds
        
        success = await people_sim.start(simulation_duration)
        if not success:
            print("   ❌ Failed to start people simulator")
            return False
        
        print(f"   ✅ People simulator started for {simulation_duration} seconds")
        print("   📈 Monitoring passenger generation patterns...")
        print()
        
        # Monitor passenger generation for the duration
        start_time = datetime.now()
        last_stats_time = start_time
        
        while (datetime.now() - start_time).total_seconds() < simulation_duration:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            # Get current statistics
            stats = people_sim.get_statistics()
            active_passengers = people_sim.get_active_passengers()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"⏱️  Time: {elapsed:.0f}s | "
                  f"Generated: {stats['total_generated']} | "
                  f"Active: {stats['current_active']} | "
                  f"Completed: {stats['total_completed']} | "
                  f"Peak: {stats['peak_active']}")
            
            # Show details of some active passengers
            if active_passengers:
                print("   📍 Sample active passengers:")
                for i, passenger in enumerate(active_passengers[:3]):  # Show first 3
                    journey = passenger.journey
                    print(f"     • {passenger.component_id}: "
                          f"pickup ({journey.pickup_lat:.4f}, {journey.pickup_lon:.4f}) → "
                          f"dest ({journey.destination_lat:.4f}, {journey.destination_lon:.4f}), "
                          f"{journey.journey_distance_km:.2f}km")
        
        print()
        print("🛑 Step 3: Stopping people simulator...")
        await people_sim.stop()
        
        # Final statistics
        final_stats = people_sim.get_statistics()
        print()
        print("📊 FINAL ROUTE 1 PASSENGER DISTRIBUTION STATISTICS:")
        print("=" * 60)
        print(f"   Total passengers generated: {final_stats['total_generated']}")
        print(f"   Total passengers completed: {final_stats['total_completed']}")
        print(f"   Peak concurrent passengers: {final_stats['peak_active']}")
        print(f"   Final active passengers: {final_stats['current_active']}")
        
        # Calculate generation rate
        total_time_minutes = simulation_duration / 60.0
        generation_rate = final_stats['total_generated'] / total_time_minutes
        print(f"   Average generation rate: {generation_rate:.2f} passengers/minute")
        
        print()
        print("✅ Route 1 people distribution test completed successfully!")
        
        # Show passenger journey details if any completed
        completed_passengers = people_sim.completed_passengers
        if completed_passengers:
            print()
            print("🎯 COMPLETED PASSENGER JOURNEYS:")
            print("-" * 40)
            for journey in completed_passengers[:5]:  # Show first 5 completed journeys
                pickup_coords = journey['pickup_coords']
                dest_coords = journey['destination_coords']
                distance = journey['journey_distance_km']
                print(f"   • {journey['passenger_id']}: {distance:.2f}km journey")
                print(f"     pickup: ({pickup_coords[0]:.4f}, {pickup_coords[1]:.4f})")
                print(f"     dest:   ({dest_coords[0]:.4f}, {dest_coords[1]:.4f})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_peak_vs_normal_distribution():
    """Compare passenger generation during peak vs normal hours."""
    
    print("\n" + "=" * 60)
    print("🕐 PEAK VS NORMAL HOURS COMPARISON")
    print("=" * 60)
    
    try:
        # Test normal hours (2 PM)
        print("📊 Testing normal hours (2 PM)...")
        normal_model = PoissonDistributionModel(base_lambda=2.0)
        
        # Simulate 2 PM time
        normal_time = datetime.now().replace(hour=14, minute=0, second=0)
        normal_passengers = await normal_model.generate_passengers(
            ["route1"], normal_time, 3600
        )
        
        print(f"   Normal hours: {len(normal_passengers)} passengers generated")
        
        # Test peak hours (8 AM)
        print("📊 Testing peak hours (8 AM)...")
        peak_time = datetime.now().replace(hour=8, minute=0, second=0)
        peak_passengers = await normal_model.generate_passengers(
            ["route1"], peak_time, 3600
        )
        
        print(f"   Peak hours: {len(peak_passengers)} passengers generated")
        
        # Show the difference
        if len(normal_passengers) > 0:
            multiplier = len(peak_passengers) / len(normal_passengers)
            print(f"   📈 Peak hour multiplier: {multiplier:.2f}x normal hours")
        
        print("   ✅ Peak vs normal comparison completed")
        
    except Exception as e:
        print(f"   ❌ Peak comparison failed: {e}")


if __name__ == "__main__":
    async def main():
        success = await test_route1_people_distribution()
        if success:
            await test_peak_vs_normal_distribution()
    
    asyncio.run(main())