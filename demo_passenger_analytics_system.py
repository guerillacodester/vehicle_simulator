#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passenger Analytics System Demo

Demonstrates the complete passenger analytics system:
- JSON-based model loading
- Real-time factor processing
- Passenger generation with capacity limits
- Rate analysis and reporting
"""

import os
import sys
import datetime
import json
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir
sys.path.insert(0, str(project_root))

try:
    from world.arknet_transit_simulator.services.passenger_model_loader import PassengerModelLoader
    from world.arknet_transit_simulator.services.passenger_generation_engine import PassengerGenerationEngine
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Running in standalone mode with mock data")


class PassengerAnalyticsDemo:
    """Demo of the complete passenger analytics system."""
    
    def __init__(self):
        # Initialize components
        try:
            self.model_loader = PassengerModelLoader()
            self.generation_engine = PassengerGenerationEngine(self.model_loader)
        except Exception as e:
            print(f"⚠️ Could not initialize full system: {e}")
            self.model_loader = None
            self.generation_engine = None
        
        # Set passenger limit (as requested by user)
        if self.generation_engine:
            self.generation_engine.set_passenger_limit(50)
        
        self.demo_results = []
    
    def run_complete_demo(self):
        """Run the complete passenger analytics demo."""
        print("=" * 80)
        print("🚌 PASSENGER ANALYTICS SYSTEM DEMO")
        print("=" * 80)
        
        # Step 1: Load available models
        print("\n📊 STEP 1: Loading Passenger Models")
        print("-" * 40)
        self.demo_model_loading()
        
        # Step 2: Configure real-time conditions
        print("\n🌤️ STEP 2: Setting Real-Time Conditions")
        print("-" * 40)
        self.demo_realtime_conditions()
        
        # Step 3: Generate passenger flows
        print("\n🚶 STEP 3: Generating Passenger Flows")
        print("-" * 40)
        self.demo_passenger_generation()
        
        # Step 4: Analyze rates and patterns
        print("\n📈 STEP 4: Analyzing Passenger Rates")
        print("-" * 40)
        self.demo_rate_analysis()
        
        # Step 5: Show capacity management
        print("\n🚌 STEP 5: Demonstrating Capacity Management")
        print("-" * 40)
        self.demo_capacity_management()
        
        # Step 6: Generate reports
        print("\n📋 STEP 6: Generating Analytics Reports")
        print("-" * 40)
        self.demo_analytics_reports()
        
        print("\n✅ Demo completed successfully!")
        print("=" * 80)
    
    def demo_model_loading(self):
        """Demonstrate model loading capabilities."""
        if not self.model_loader:
            print("❌ Model loader not available - using mock data")
            return
        
        # Show available models
        available_models = self.model_loader.get_available_models()
        print(f"📁 Available model files: {available_models}")
        
        # Load the Bridgetown transit model
        if "bridgetown_transit_model.json" in available_models:
            success = self.model_loader.load_model("bridgetown_transit_model.json")
            if success:
                loaded_models = self.model_loader.list_loaded_models()
                print(f"✅ Loaded models: {loaded_models}")
            else:
                print("❌ Failed to load Bridgetown model")
        else:
            print("⚠️ Bridgetown model not found - creating mock model")
            self.create_mock_model()
    
    def create_mock_model(self):
        """Create a mock model for demonstration."""
        mock_model = {
            "model_info": {
                "name": "demo_transit_model",
                "version": "1.0.0",
                "description": "Mock model for demonstration"
            },
            "locations": {
                "downtown_station": {
                    "name": "Downtown Station",
                    "passenger_rates": {
                        "boarding": {
                            "peak_hours": {"rate_per_hour": 15, "variance": 0.2, "confidence_level": 0.8},
                            "off_peak_hours": {"rate_per_hour": 6, "variance": 0.3, "confidence_level": 0.7}
                        },
                        "alighting": {
                            "peak_hours": {"rate_per_hour": 12, "variance": 0.2, "confidence_level": 0.8},
                            "off_peak_hours": {"rate_per_hour": 4, "variance": 0.3, "confidence_level": 0.7}
                        }
                    }
                }
            },
            "time_patterns": {
                "peak_hours": [
                    {"start_time": "07:00", "end_time": "09:00", "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"], "multiplier": 1.5}
                ],
                "day_types": {"weekday": 1.0, "saturday": 0.7, "sunday": 0.5, "holiday": 0.3}
            },
            "demand_profiles": {
                "commute": {"percentage": 40, "peak_preference": True},
                "leisure": {"percentage": 30, "peak_preference": False},
                "shopping": {"percentage": 20, "peak_preference": False},
                "other": {"percentage": 10, "peak_preference": False}
            }
        }
        
        if self.model_loader:
            self.model_loader.loaded_models["demo_transit_model"] = mock_model
            print("✅ Created mock model for demo")
    
    def demo_realtime_conditions(self):
        """Demonstrate real-time condition updates."""
        if not self.model_loader:
            print("❌ Model loader not available")
            return
        
        # Set various real-time conditions
        conditions = {
            "weather": "heavy_rain",
            "service_status": "normal",
            "economic_condition": "normal",
            "infrastructure_status": "normal"
        }
        
        self.model_loader.update_conditions(conditions)
        print(f"🔄 Set conditions: {conditions}")
        
        # Show how conditions affect calculations
        current_time = datetime.datetime.now().replace(hour=8, minute=30)  # Peak time
        model_name = "demo_transit_model" if "demo_transit_model" in self.model_loader.loaded_models else "bridgetown_transit_model"
        
        if model_name in self.model_loader.loaded_models:
            # Calculate with current conditions
            flow_result = self.model_loader.calculate_passenger_flow(
                model_name, "downtown_station", current_time, 60
            )
            
            if flow_result:
                print(f"🌧️ With heavy rain conditions:")
                print(f"   Boarding rate: {flow_result.boarding_rate:.1f} passengers/hour")
                print(f"   Applied factors: {flow_result.applied_factors}")
        
        # Change to pleasant weather
        self.model_loader.update_conditions({"weather": "pleasant_weather"})
        flow_result2 = self.model_loader.calculate_passenger_flow(
            model_name, "downtown_station", current_time, 60
        )
        
        if flow_result2:
            print(f"☀️ With pleasant weather:")
            print(f"   Boarding rate: {flow_result2.boarding_rate:.1f} passengers/hour")
            print(f"   Weather impact: {flow_result2.boarding_rate / flow_result.boarding_rate:.2f}x")
    
    def demo_passenger_generation(self):
        """Demonstrate passenger generation with capacity limits."""
        if not self.generation_engine:
            print("❌ Generation engine not available")
            return
        
        model_name = "demo_transit_model"
        current_time = datetime.datetime.now()
        
        print(f"🚌 Passenger limit set to: {self.generation_engine.max_total_passengers}")
        
        # Generate passengers for multiple time periods
        locations = ["downtown_station", "mall_stop", "university_gate"]
        
        for i, location in enumerate(locations):
            time_offset = current_time + datetime.timedelta(minutes=i * 30)
            
            batch = self.generation_engine.generate_passenger_batch(
                model_name, location, time_offset, 30
            )
            
            if batch:
                print(f"📍 {location} at {time_offset.strftime('%H:%M')}:")
                print(f"   Boarding: {batch.total_boarding} passengers")
                print(f"   Alighting: {batch.total_alighting} passengers")
                
                # Show some passenger details
                if batch.boarding_passengers:
                    sample_passenger = batch.boarding_passengers[0]
                    print(f"   Sample passenger: {sample_passenger.passenger_id} ({sample_passenger.trip_purpose})")
        
        # Show current statistics
        stats = self.generation_engine.get_passenger_statistics()
        print(f"\n📊 Current statistics:")
        print(f"   Active passengers: {stats['currently_active_passengers']}")
        print(f"   Capacity utilization: {stats['capacity_utilization']:.1f}%")
        print(f"   Trip purposes: {stats['trip_purpose_breakdown']}")
    
    def demo_rate_analysis(self):
        """Demonstrate passenger rate analysis."""
        print("📈 Passenger Rate Analysis:")
        
        # Show rate calculations for different times
        times_to_analyze = [
            ("Peak Morning", 8, 0),
            ("Lunch Hour", 12, 30),
            ("Peak Evening", 17, 30),
            ("Late Evening", 22, 0)
        ]
        
        base_date = datetime.datetime.now().date()
        
        for time_name, hour, minute in times_to_analyze:
            analysis_time = datetime.datetime.combine(base_date, datetime.time(hour, minute))
            
            if self.model_loader and "demo_transit_model" in self.model_loader.loaded_models:
                flow_result = self.model_loader.calculate_passenger_flow(
                    "demo_transit_model", "downtown_station", analysis_time, 60
                )
                
                if flow_result:
                    print(f"🕐 {time_name} ({hour:02d}:{minute:02d}):")
                    print(f"   Boarding rate: {flow_result.boarding_rate:.1f} passengers/hour")
                    print(f"   Alighting rate: {flow_result.alighting_rate:.1f} passengers/hour")
                    print(f"   Confidence: {flow_result.confidence_level:.1%}")
    
    def demo_capacity_management(self):
        """Demonstrate capacity management features."""
        print("🚌 Capacity Management Demo:")
        
        # Show how passenger limit affects generation
        original_limit = self.generation_engine.max_total_passengers if self.generation_engine else 50
        
        print(f"📊 Current passenger limit: {original_limit}")
        
        # Simulate approaching capacity
        if self.generation_engine:
            # Fill up most of the capacity with mock passengers
            for i in range(45):  # Fill to 45/50
                passenger_id = f"MOCK_{i:03d}"
                mock_passenger = type('MockPassenger', (), {
                    'passenger_id': passenger_id,
                    'location_id': 'downtown_station',
                    'action': 'board',
                    'timestamp': datetime.datetime.now(),
                    'trip_purpose': 'commute'
                })()
                self.generation_engine.active_passengers[passenger_id] = mock_passenger
            
            stats = self.generation_engine.get_passenger_statistics()
            print(f"🔄 Simulated high capacity: {stats['currently_active_passengers']}/{stats['passenger_limit']}")
            print(f"📈 Utilization: {stats['capacity_utilization']:.1f}%")
            
            # Try to generate more passengers - should be limited
            batch = self.generation_engine.generate_passenger_batch(
                "demo_transit_model", "downtown_station", datetime.datetime.now(), 30
            )
            
            if batch:
                print(f"⚠️ With near-full capacity, generated only {batch.total_boarding} new passengers")
            
            # Show what happens at full capacity
            print("\n🚫 Testing full capacity scenario...")
            # Fill remaining slots
            for i in range(45, 50):
                passenger_id = f"MOCK_{i:03d}"
                mock_passenger = type('MockPassenger', (), {
                    'passenger_id': passenger_id,
                    'location_id': 'downtown_station',
                    'action': 'board',
                    'timestamp': datetime.datetime.now(),
                    'trip_purpose': 'commute'
                })()
                self.generation_engine.active_passengers[passenger_id] = mock_passenger
            
            # Try to generate at full capacity
            batch_full = self.generation_engine.generate_passenger_batch(
                "demo_transit_model", "downtown_station", datetime.datetime.now(), 30
            )
            
            if batch_full:
                print(f"🚫 At full capacity (50/50), generated {batch_full.total_boarding} new passengers")
            
            # Reset for cleanup
            self.generation_engine.reset_simulation()
    
    def demo_analytics_reports(self):
        """Generate comprehensive analytics reports."""
        print("📋 Analytics Report Generation:")
        
        if not self.model_loader:
            print("❌ Cannot generate full reports without model loader")
            return
        
        # Generate a daily schedule analysis
        start_time = datetime.datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(hours=18)  # 6 AM to midnight
        
        print(f"📅 Generating schedule from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}")
        
        try:
            schedule = self.model_loader.generate_passenger_schedule(
                "demo_transit_model", start_time, end_time, interval_minutes=60
            )
            
            if schedule:
                print(f"✅ Generated {len(schedule)} time periods")
                
                # Summarize by hour
                hourly_summary = {}
                for result in schedule:
                    hour = result.timestamp.hour
                    if hour not in hourly_summary:
                        hourly_summary[hour] = {"boarding": 0, "alighting": 0, "locations": set()}
                    
                    hourly_summary[hour]["boarding"] += result.expected_boarding_count
                    hourly_summary[hour]["alighting"] += result.expected_alighting_count
                    hourly_summary[hour]["locations"].add(result.location_id)
                
                print("\n🕐 Hourly Passenger Flow Summary:")
                print("Hour | Boarding | Alighting | Locations")
                print("-" * 45)
                
                for hour in sorted(hourly_summary.keys()):
                    data = hourly_summary[hour]
                    locations_count = len(data["locations"])
                    print(f"{hour:2d}:00 | {data['boarding']:8d} | {data['alighting']:9d} | {locations_count}")
                
                # Find peak hours
                peak_boarding_hour = max(hourly_summary.keys(), 
                                       key=lambda h: hourly_summary[h]["boarding"])
                peak_alighting_hour = max(hourly_summary.keys(), 
                                        key=lambda h: hourly_summary[h]["alighting"])
                
                print(f"\n📊 Peak Analysis:")
                print(f"   Peak boarding: {peak_boarding_hour:02d}:00 ({hourly_summary[peak_boarding_hour]['boarding']} passengers)")
                print(f"   Peak alighting: {peak_alighting_hour:02d}:00 ({hourly_summary[peak_alighting_hour]['alighting']} passengers)")
        
        except Exception as e:
            print(f"❌ Error generating schedule: {e}")
        
        # Show model effectiveness
        print(f"\n🎯 Model Effectiveness:")
        if self.model_loader.loaded_models:
            for model_name, model_data in self.model_loader.loaded_models.items():
                print(f"   Model: {model_name}")
                print(f"   Version: {model_data['model_info']['version']}")
                print(f"   Locations: {len(model_data.get('locations', {}))}")
                print(f"   Demand profiles: {len(model_data.get('demand_profiles', {}))}")


def main():
    """Run the passenger analytics demo."""
    demo = PassengerAnalyticsDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()