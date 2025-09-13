#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passenger Generation Demo

Demonstrates how to use the passenger model to generate realistic passenger flows
at the Bridgetown depot and along Route 1, including distance-based modeling,
group patterns, and capacity limits.
"""

import datetime
import json
import random
from pathlib import Path

# Try to import the passenger generation components
try:
    from world.arknet_transit_simulator.services.passenger_generation_engine import (
        PassengerGenerationEngine, GeneratedPassenger, PassengerBatch
    )
    from world.arknet_transit_simulator.services.passenger_model_loader import (
        PassengerModelLoader, PassengerFlowResult
    )
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Running in demonstration mode with mock data")
    COMPONENTS_AVAILABLE = False


class PassengerGenerationDemo:
    """Demonstration of model-driven passenger generation."""
    
    def __init__(self):
        self.setup_components()
        self.route_1_stops = [
            "DEPOT_MAIN",
            "BRIDGETOWN_TERMINAL", 
            "JUBILEE_MARKET",
            "UNIVERSITY_MAIN",
            "INDUSTRIAL_ESTATE",
            "MALL_JUNCTION",
            "SOUTH_COAST_TERMINAL"
        ]
    
    def setup_components(self):
        """Setup passenger generation components."""
        if COMPONENTS_AVAILABLE:
            try:
                # Initialize model loader
                model_dir = Path(__file__).parent / "world" / "arknet_transit_simulator" / "models" / "passenger_analytics"
                self.model_loader = PassengerModelLoader(str(model_dir))
                
                # Load the Route 1/1A/1B model
                model_loaded = self.model_loader.load_model("route_1_1a_1b_model.json")
                if model_loaded:
                    print("✅ Loaded Route 1/1A/1B passenger model")
                else:
                    print("⚠️ Could not load passenger model")
                
                # Initialize generation engine
                self.generator = PassengerGenerationEngine(self.model_loader)
                self.generator.set_passenger_limit(50)  # Max 50 passengers total
                
            except Exception as e:
                print(f"⚠️ Setup error: {e}")
                self.model_loader = None
                self.generator = None
        else:
            self.model_loader = None
            self.generator = None
    
    def run_complete_demo(self):
        """Run the complete passenger generation demonstration."""
        print("=" * 80)
        print("🚌 PASSENGER GENERATION DEMO - ROUTE 1 & BRIDGETOWN DEPOT")
        print("=" * 80)
        
        if not COMPONENTS_AVAILABLE:
            self.show_conceptual_demo()
            return
        
        # Step 1: Generate passengers at Bridgetown depot (morning peak)
        print("\n🏢 STEP 1: Generating Passengers at Bridgetown Depot")
        print("-" * 50)
        self.demo_depot_passenger_generation()
        
        # Step 2: Generate passengers along Route 1 stops
        print("\n🚌 STEP 2: Generating Passengers Along Route 1")
        print("-" * 50)
        self.demo_route_passenger_generation()
        
        # Step 3: Show capacity management
        print("\n⚖️ STEP 3: Capacity Management & Limits")
        print("-" * 50)
        self.demo_capacity_management()
        
        # Step 4: Show distance-based passenger flow
        print("\n📏 STEP 4: Distance-Based Passenger Modeling")
        print("-" * 50)
        self.demo_distance_modeling()
        
        # Step 5: Show group pattern generation
        print("\n👥 STEP 5: Group Pattern Generation")
        print("-" * 50)
        self.demo_group_patterns()
        
        print("\n✅ Passenger generation demo completed!")
        print("=" * 80)
    
    def show_conceptual_demo(self):
        """Show conceptual demo when components aren't available."""
        print("\n🎯 CONCEPTUAL DEMO: Model-Driven Passenger Generation")
        print("-" * 60)
        
        print("📊 HOW THE MODEL WORKS:")
        print("   1. Load passenger model (route_1_1a_1b_model.json)")
        print("   2. Specify location (DEPOT_MAIN, BRIDGETOWN_TERMINAL, etc.)")
        print("   3. Set time period (morning peak, off-peak, etc.)")
        print("   4. Generate passengers based on model parameters")
        
        print("\n🏢 BRIDGETOWN DEPOT GENERATION:")
        print("   • High boarding rates during morning peak (6:00-9:00 AM)")
        print("   • Lower boarding rates during off-peak hours")
        print("   • Mostly work commuters and connecting passengers")
        print("   • Distance decay: passengers come from nearby areas")
        
        print("\n🚌 ROUTE 1 STOPS GENERATION:")
        print("   • University: High student boarding, group patterns")
        print("   • Industrial Estate: Work commuters, peak hour patterns")
        print("   • Mall Junction: Shopping trips, family groups")
        print("   • Each stop has unique passenger characteristics")
        
        print("\n⚖️ CAPACITY MANAGEMENT:")
        print("   • Maximum 50 total passengers system-wide")
        print("   • Dynamic adjustment based on current passenger count")
        print("   • Priority boarding for high-demand stops")
        
        # Show mock generation results
        self.show_mock_generation_results()
    
    def show_mock_generation_results(self):
        """Show example passenger generation results."""
        print("\n📋 EXAMPLE GENERATION RESULTS:")
        print("-" * 40)
        
        # Mock morning peak at depot
        current_time = datetime.datetime.now().replace(hour=7, minute=30, second=0, microsecond=0)
        
        print(f"🏢 DEPOT_MAIN at {current_time.strftime('%H:%M')}")
        print("   📈 Boarding Rate: 45 passengers/hour")
        print("   👥 Expected Boarding: 23 passengers (30 min period)")
        print("   🎯 Trip Purposes: 70% work commute, 20% connecting, 10% other")
        print("   ⏱️ Average Wait Time: 8 minutes")
        print("   🚶 Walking Distance: 85% within 400m, 15% beyond")
        
        university_time = current_time + datetime.timedelta(minutes=15)
        print(f"\n🎓 UNIVERSITY_MAIN at {university_time.strftime('%H:%M')}")
        print("   📈 Boarding Rate: 35 passengers/hour")
        print("   👥 Expected Boarding: 18 passengers (30 min period)")
        print("   🎯 Trip Purposes: 80% school commute, 15% work, 5% other")
        print("   ⏱️ Average Wait Time: 6 minutes")
        print("   👫 Group Patterns: 40% groups of 2-4, 60% solo")
        
        industrial_time = current_time + datetime.timedelta(minutes=25)
        print(f"\n🏭 INDUSTRIAL_ESTATE at {industrial_time.strftime('%H:%M')}")
        print("   📈 Boarding Rate: 25 passengers/hour")
        print("   👥 Expected Boarding: 13 passengers (30 min period)")
        print("   🎯 Trip Purposes: 85% work commute, 10% business, 5% other")
        print("   ⏱️ Average Wait Time: 10 minutes")
        print("   🚶 Walking Distance: 60% within 300m, 40% beyond")
    
    def demo_depot_passenger_generation(self):
        """Demonstrate passenger generation at the depot."""
        if not self.generator:
            print("❌ Generator not available - using mock demonstration")
            return
        
        print("🏢 Generating passengers at DEPOT_MAIN (morning peak)...")
        
        # Generate passengers for morning peak hour (7:30-8:00 AM)
        current_time = datetime.datetime.now().replace(hour=7, minute=30, second=0, microsecond=0)
        
        try:
            batch = self.generator.generate_passenger_batch(
                model_name="route_1_1a_1b_transit_model",
                location_id="DEPOT_MAIN",
                target_time=current_time,
                duration_minutes=30
            )
            
            if batch:
                print(f"✅ Generated passenger batch for DEPOT_MAIN")
                print(f"   📊 Boarding passengers: {batch.total_boarding}")
                print(f"   📉 Alighting passengers: {batch.total_alighting}")
                print(f"   🕒 Time period: {current_time.strftime('%H:%M')}-{(current_time + datetime.timedelta(minutes=30)).strftime('%H:%M')}")
                
                # Show sample passengers
                if batch.boarding_passengers:
                    print(f"\n👥 Sample boarding passengers:")
                    for i, passenger in enumerate(batch.boarding_passengers[:5]):
                        print(f"   {i+1}. {passenger.passenger_id}: {passenger.trip_purpose} - wait {passenger.wait_time_seconds//60}min")
                
                # Show applied factors
                if batch.applied_factors:
                    print(f"\n📈 Applied factors:")
                    for factor, value in batch.applied_factors.items():
                        print(f"   • {factor}: {value:.2f}")
            else:
                print("❌ No passenger batch generated")
                
        except Exception as e:
            print(f"❌ Generation error: {e}")
    
    def demo_route_passenger_generation(self):
        """Demonstrate passenger generation along Route 1 stops."""
        if not self.generator:
            print("❌ Generator not available - using mock demonstration")
            return
        
        print("🚌 Generating passengers along Route 1 stops...")
        
        # Generate for key stops during morning commute
        base_time = datetime.datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        key_stops = ["BRIDGETOWN_TERMINAL", "UNIVERSITY_MAIN", "INDUSTRIAL_ESTATE"]
        
        total_boarding = 0
        total_alighting = 0
        
        for i, stop_id in enumerate(key_stops):
            stop_time = base_time + datetime.timedelta(minutes=i*10)
            
            try:
                batch = self.generator.generate_passenger_batch(
                    model_name="route_1_1a_1b_transit_model",
                    location_id=stop_id,
                    target_time=stop_time,
                    duration_minutes=20
                )
                
                if batch:
                    total_boarding += batch.total_boarding
                    total_alighting += batch.total_alighting
                    
                    print(f"\n📍 {stop_id} at {stop_time.strftime('%H:%M')}")
                    print(f"   ⬆️ Boarding: {batch.total_boarding}")
                    print(f"   ⬇️ Alighting: {batch.total_alighting}")
                    
                    # Show dominant trip purpose
                    if batch.boarding_passengers:
                        purposes = [p.trip_purpose for p in batch.boarding_passengers]
                        dominant_purpose = max(set(purposes), key=purposes.count)
                        print(f"   🎯 Dominant purpose: {dominant_purpose}")
                else:
                    print(f"\n📍 {stop_id}: No passengers generated")
                    
            except Exception as e:
                print(f"❌ Error generating for {stop_id}: {e}")
        
        print(f"\n📊 ROUTE TOTALS:")
        print(f"   Total boarding: {total_boarding}")
        print(f"   Total alighting: {total_alighting}")
        print(f"   Net passenger change: {total_boarding - total_alighting}")
    
    def demo_capacity_management(self):
        """Demonstrate capacity management and passenger limits."""
        print("⚖️ Demonstrating capacity management (max 50 passengers)...")
        
        if not self.generator:
            print("❌ Generator not available")
            return
        
        # Show current passenger count
        current_count = len(self.generator.active_passengers)
        print(f"📊 Current active passengers: {current_count}")
        print(f"🎯 Maximum allowed: {self.generator.max_total_passengers}")
        print(f"🔓 Available slots: {self.generator.max_total_passengers - current_count}")
        
        # Simulate high-demand scenario
        print(f"\n🚨 Simulating high-demand scenario...")
        
        # Add some mock active passengers
        for i in range(30):
            passenger_id = f"mock_passenger_{i}"
            mock_passenger = type('MockPassenger', (), {
                'passenger_id': passenger_id,
                'location_id': 'IN_TRANSIT',
                'action': 'traveling'
            })()
            self.generator.active_passengers[passenger_id] = mock_passenger
        
        print(f"📊 Added 30 active passengers (simulated)")
        print(f"🎯 Remaining capacity: {self.generator.max_total_passengers - len(self.generator.active_passengers)}")
        
        # Try to generate more passengers
        current_time = datetime.datetime.now().replace(hour=8, minute=30, second=0, microsecond=0)
        
        try:
            batch = self.generator.generate_passenger_batch(
                model_name="route_1_1a_1b_transit_model",
                location_id="UNIVERSITY_MAIN",
                target_time=current_time,
                duration_minutes=15
            )
            
            if batch:
                print(f"✅ Generated batch respecting capacity limits")
                print(f"   📊 Boarding (capacity-adjusted): {batch.total_boarding}")
                print(f"   ⚖️ System would have generated more but hit capacity limit")
            else:
                print("❌ No batch generated - possibly due to capacity")
                
        except Exception as e:
            print(f"❌ Capacity management error: {e}")
    
    def demo_distance_modeling(self):
        """Demonstrate distance-based passenger flow modeling."""
        print("📏 Demonstrating distance-based passenger modeling...")
        
        if not self.model_loader:
            print("❌ Model loader not available")
            return
        
        print("🎯 Distance decay modeling shows how passenger demand")
        print("   decreases with walking distance to bus stops")
        
        print(f"\n📍 Example: UNIVERSITY_MAIN stop catchment")
        print("   🟢 Primary catchment (0-200m): 80% of passengers")
        print("   🟡 Secondary catchment (200-500m): 15% of passengers") 
        print("   🔴 Extended catchment (500m+): 5% of passengers")
        
        print(f"\n📍 Example: DEPOT_MAIN stop catchment")
        print("   🟢 Primary catchment (0-300m): 70% of passengers")
        print("   🟡 Secondary catchment (300-600m): 25% of passengers")
        print("   🔴 Extended catchment (600m+): 5% of passengers")
        
        print(f"\n📊 Distance factors affect:")
        print("   • Total passenger generation rate")
        print("   • Walking time to stop")
        print("   • Likelihood of choosing this stop vs alternatives")
    
    def demo_group_patterns(self):
        """Demonstrate group pattern generation."""
        print("👥 Demonstrating group pattern modeling...")
        
        print("🎓 UNIVERSITY_MAIN group patterns:")
        print("   • 60% groups of 2-4 (students traveling together)")
        print("   • 35% solo travelers")
        print("   • 5% large groups (5+)")
        print("   • Longer boarding times for groups")
        
        print(f"\n🏢 DEPOT_MAIN group patterns:")
        print("   • 75% solo travelers (work commuters)")
        print("   • 20% pairs")
        print("   • 5% small groups")
        print("   • Faster boarding (experienced commuters)")
        
        print(f"\n🛍️ MALL_JUNCTION group patterns:")
        print("   • 45% pairs and small groups (shopping trips)")
        print("   • 40% solo travelers")
        print("   • 15% family groups (3-5 people)")
        print("   • Variable boarding times (packages, children)")
        
        print(f"\n📊 Group patterns affect:")
        print("   • Boarding time calculations")
        print("   • Passenger distribution in vehicle")
        print("   • Trip purpose correlation")
        print("   • Total capacity utilization")


def main():
    """Run the passenger generation demonstration."""
    demo = PassengerGenerationDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()