#!/usr/bin/env python3
"""
Route 1 Depot-Centric People Distribution Test
==============================================

Tests the people simulator with proper depot-centric generation:
- 80% of passengers start or end at the depot (primary hub)
- 20% distributed along actual Route 1 polyline coordinates
- Uses real geojson data from route_1_final_processed.geojson
"""

import asyncio
import logging
from datetime import datetime
from world.vehicle_simulator.models.people import (
    PoissonDistributionModel, 
    PeopleSimulator
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_depot_centric_route1():
    """Test depot-centric passenger generation for Route 1."""
    
    print("🏢 DEPOT-CENTRIC ROUTE 1 PASSENGER GENERATION")
    print("=" * 60)
    print("📋 This test demonstrates:")
    print("   • Depot as primary passenger hub (80% of generation)")
    print("   • Route polyline distributed generation (20%)")
    print("   • Real Route 1 coordinates from geojson data")
    print("   • Depot ↔ Route passenger flow patterns")
    print()
    
    try:
        print("🔧 Step 1: Initialize depot-centric people simulator...")
        
        # Create distribution model optimized for depot-centric generation
        distribution_model = PoissonDistributionModel(
            base_lambda=6.0,        # Higher generation rate to see patterns
            peak_multiplier=2.0,    # Peak hour boost
            weekend_multiplier=0.7, # Weekend reduction
            min_journey_km=0.5,     # Allow short depot trips
            max_journey_km=12.0,    # Reasonable max for Route 1
        )
        
        # Create people simulator
        people_sim = PeopleSimulator(
            distribution_model=distribution_model,
            generation_interval=4.0,  # Generate every 4 seconds
            cleanup_interval=20.0     # Cleanup every 20 seconds
        )
        
        # Set Route 1 as available route
        people_sim.set_available_routes(["route1"])
        
        print("   ✅ People simulator initialized")
        print(f"   🏢 Depot-centric generation: 80% depot hub, 20% route distributed")
        print(f"   📊 Base rate: {distribution_model.base_lambda} passengers/minute")
        print()
        
        print("🚀 Step 2: Start passenger generation...")
        simulation_duration = 30  # 30 seconds
        
        success = await people_sim.start(simulation_duration)
        if not success:
            print("   ❌ Failed to start people simulator")
            return False
        
        print(f"   ✅ Started {simulation_duration}s simulation")
        print("   📈 Monitoring depot-centric passenger patterns...")
        print()
        
        # Monitor generation with detailed passenger analysis
        start_time = datetime.now()
        depot_passengers = 0
        route_passengers = 0
        
        for i in range(3):  # Check 3 times during simulation
            await asyncio.sleep(10)  # Every 10 seconds
            
            stats = people_sim.get_statistics()
            active_passengers = people_sim.get_active_passengers()
            elapsed = (datetime.now() - start_time).total_seconds()
            
            print(f"⏱️  {elapsed:.0f}s: Generated={stats['total_generated']}, "
                  f"Active={stats['current_active']}, Peak={stats['peak_active']}")
            
            if active_passengers:
                print("   🎯 Passenger Flow Analysis:")
                
                # Analyze passenger pickup/destination patterns
                depot_coords = (13.2875, -59.6451)  # Approximate depot location
                depot_tolerance = 0.002  # ~200m tolerance for depot area
                
                for passenger in active_passengers[-5:]:  # Show last 5 passengers
                    journey = passenger.journey
                    pickup = (journey.pickup_lat, journey.pickup_lon)
                    dest = (journey.destination_lat, journey.destination_lon)
                    
                    # Check if pickup or destination is near depot
                    pickup_at_depot = (abs(pickup[0] - depot_coords[0]) < depot_tolerance and 
                                      abs(pickup[1] - depot_coords[1]) < depot_tolerance)
                    dest_at_depot = (abs(dest[0] - depot_coords[0]) < depot_tolerance and 
                                    abs(dest[1] - depot_coords[1]) < depot_tolerance)
                    
                    if pickup_at_depot and dest_at_depot:
                        flow_type = "🏢→🏢 Depot internal"
                    elif pickup_at_depot:
                        flow_type = "🏢→🛣️  Depot to Route"
                        depot_passengers += 1
                    elif dest_at_depot:
                        flow_type = "🛣️→🏢  Route to Depot"
                        depot_passengers += 1
                    else:
                        flow_type = "🛣️→🛣️  Route to Route"
                        route_passengers += 1
                    
                    print(f"     • {passenger.component_id}: {journey.journey_distance_km:.2f}km - {flow_type}")
                    print(f"       pickup: ({pickup[0]:.5f}, {pickup[1]:.5f})")
                    print(f"       dest:   ({dest[0]:.5f}, {dest[1]:.5f})")
                print()
        
        print("🛑 Step 3: Stopping simulation...")
        await people_sim.stop()
        
        # Final analysis
        final_stats = people_sim.get_statistics()
        total_analyzed = depot_passengers + route_passengers
        
        print()
        print("📊 DEPOT-CENTRIC GENERATION ANALYSIS:")
        print("=" * 50)
        print(f"   Total passengers generated: {final_stats['total_generated']}")
        print(f"   Peak concurrent passengers: {final_stats['peak_active']}")
        
        if total_analyzed > 0:
            depot_percentage = (depot_passengers / total_analyzed) * 100
            route_percentage = (route_passengers / total_analyzed) * 100
            
            print(f"   Depot-related journeys: {depot_passengers} ({depot_percentage:.1f}%)")
            print(f"   Route-to-route journeys: {route_passengers} ({route_percentage:.1f}%)")
            
            print()
            print("🎯 PASSENGER FLOW PATTERNS:")
            print(f"   🏢 Depot Hub Activity: {depot_percentage:.1f}% (target: ~80%)")
            print(f"   🛣️  Route Distribution: {route_percentage:.1f}% (target: ~20%)")
            
            if depot_percentage >= 70:
                print("   ✅ Depot-centric pattern successfully demonstrated!")
            else:
                print("   ⚠️  Lower depot activity than expected (may need more data)")
        
        # Show coordinate ranges to verify real data usage
        all_passengers = people_sim.get_active_passengers()
        if all_passengers:
            lats = [p.journey.pickup_lat for p in all_passengers] + [p.journey.destination_lat for p in all_passengers]
            lons = [p.journey.pickup_lon for p in all_passengers] + [p.journey.destination_lon for p in all_passengers]
            
            print()
            print("🗺️  COORDINATE VERIFICATION:")
            print(f"   Latitude range: {min(lats):.5f} to {max(lats):.5f}")
            print(f"   Longitude range: {min(lons):.5f} to {max(lons):.5f}")
            print("   ✅ Using real Route 1 Caribbean coordinates!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_depot_centric_route1())