#!/usr/bin/env python3
"""
Intensive Route 1 People Distribution Demo
==========================================

Shows realistic passenger generation patterns with higher rates to demonstrate
the distribution model effectively.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from world.arknet_transit_simulator.models.people import (
    PoissonDistributionModel, 
    PeopleSimulator
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def demo_route1_intensive_distribution():
    """Demonstrate intensive passenger generation for Route 1."""
    
    print("🚌 INTENSIVE ROUTE 1 PEOPLE DISTRIBUTION DEMO")
    print("=" * 60)
    print("🎯 High-rate passenger generation to show distribution patterns")
    print()
    
    try:
        # Create high-rate distribution model
        distribution_model = PoissonDistributionModel(
            base_lambda=8.0,        # 8 passengers per minute (much higher rate)
            peak_multiplier=2.0,    # 2x during peak hours
            weekend_multiplier=0.6, # 60% of weekday traffic
            min_journey_km=0.8,     # Minimum journey distance
            max_journey_km=20.0,    # Maximum journey distance
        )
        
        # Create people simulator with faster generation
        people_sim = PeopleSimulator(
            distribution_model=distribution_model,
            generation_interval=3.0,  # Generate every 3 seconds
            cleanup_interval=15.0     # Cleanup every 15 seconds
        )
        
        people_sim.set_available_routes(["route1"])
        
        print(f"🔧 Model: {distribution_model.get_model_name()}")
        print(f"📊 Base rate: {distribution_model.base_lambda} passengers/minute")
        print(f"⚡ Generation interval: 3 seconds")
        print()
        
        # Start simulation
        simulation_duration = 45  # 45 seconds
        await people_sim.start(simulation_duration)
        
        print(f"🚀 Running intensive generation for {simulation_duration} seconds...")
        print()
        
        # Monitor with detailed output
        start_time = datetime.now()
        
        for i in range(5):  # Check 5 times during simulation
            await asyncio.sleep(9)  # Every 9 seconds
            
            stats = people_sim.get_statistics()
            active_passengers = people_sim.get_active_passengers()
            elapsed = (datetime.now() - start_time).total_seconds()
            
            print(f"⏱️  {elapsed:.0f}s: Generated={stats['total_generated']}, "
                  f"Active={stats['current_active']}, Completed={stats['total_completed']}")
            
            # Show passenger details
            if active_passengers:
                print("   📍 Recent passengers:")
                for passenger in active_passengers[-3:]:  # Show last 3
                    j = passenger.journey
                    status = "✅ Picked up" if passenger.is_picked_up else "⏳ Waiting"
                    print(f"     • {passenger.component_id}: {j.journey_distance_km:.1f}km - {status}")
        
        await people_sim.stop()
        
        # Final results
        final_stats = people_sim.get_statistics()
        print()
        print("📈 ROUTE 1 DISTRIBUTION RESULTS:")
        print("=" * 40)
        print(f"Total generated: {final_stats['total_generated']} passengers")
        print(f"Peak concurrent: {final_stats['peak_active']} passengers")
        print(f"Completed journeys: {final_stats['total_completed']} passengers")
        
        # Show journey distance distribution
        active_passengers = people_sim.get_active_passengers()
        if active_passengers:
            distances = [p.journey.journey_distance_km for p in active_passengers]
            avg_distance = sum(distances) / len(distances)
            min_distance = min(distances)
            max_distance = max(distances)
            
            print()
            print("🛣️  JOURNEY DISTANCE ANALYSIS:")
            print(f"   Average: {avg_distance:.2f}km")
            print(f"   Range: {min_distance:.2f}km - {max_distance:.2f}km")
            print(f"   Sample journeys:")
            
            for i, passenger in enumerate(active_passengers[:5]):
                j = passenger.journey
                print(f"     {i+1}. {j.journey_distance_km:.2f}km - "
                      f"({j.pickup_lat:.4f}, {j.pickup_lon:.4f}) → "
                      f"({j.destination_lat:.4f}, {j.destination_lon:.4f})")
        
        generation_rate = final_stats['total_generated'] / (simulation_duration / 60.0)
        print(f"\n🎯 Actual generation rate: {generation_rate:.1f} passengers/minute")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def demo_peak_hour_effect():
    """Demonstrate peak hour passenger generation effect."""
    
    print("\n" + "=" * 60)
    print("🕐 PEAK HOUR EFFECT DEMONSTRATION")
    print("=" * 60)
    
    distribution_model = PoissonDistributionModel(base_lambda=5.0, peak_multiplier=3.0)
    
    # Test different times
    test_times = [
        ("Normal (2 PM)", datetime.now().replace(hour=14, minute=0)),
        ("Morning Peak (8 AM)", datetime.now().replace(hour=8, minute=0)),
        ("Evening Peak (6 PM)", datetime.now().replace(hour=18, minute=0)),
        ("Late Night (11 PM)", datetime.now().replace(hour=23, minute=0)),
    ]
    
    print("🧪 Testing passenger generation at different times:")
    print()
    
    for time_label, test_time in test_times:
        # Generate passengers multiple times and average
        total_passengers = 0
        tests = 5
        
        for _ in range(tests):
            passengers = await distribution_model.generate_passengers(
                ["route1"], test_time, 3600
            )
            total_passengers += len(passengers)
        
        avg_passengers = total_passengers / tests
        print(f"   {time_label:20}: {avg_passengers:.1f} passengers (avg of {tests} tests)")
    
    print("\n✅ Peak hour effect demonstration completed")


if __name__ == "__main__":
    async def main():
        success = await demo_route1_intensive_distribution()
        if success:
            await demo_peak_hour_effect()
    
    asyncio.run(main())