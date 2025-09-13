#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-World Data Extraction Demo

Demonstrates how to use the data extraction system to create passenger models
from real-world observations, including distance analysis and group patterns.
"""

import datetime
import json
import os
from pathlib import Path

# Import the data extraction components
try:
    from world.arknet_transit_simulator.services.real_world_data_extractor import (
        RealWorldDataExtractor, StopSurveyData, RouteTimingData, DistanceAnalysisData
    )
    from world.arknet_transit_simulator.services.passenger_model_loader import PassengerModelLoader
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Running in demonstration mode")


class RealWorldExtractionDemo:
    """Demonstration of real-world data extraction for transit modeling."""
    
    def __init__(self):
        self.extractor = RealWorldDataExtractor() if 'RealWorldDataExtractor' in globals() else None
        self.demo_route_stops = [
            {"stop_id": "BRIDGETOWN_TERMINAL", "stop_name": "Bridgetown Bus Terminal", "coordinates": [-59.6142, 13.0969]},
            {"stop_id": "UNIVERSITY_MAIN", "stop_name": "University of the West Indies", "coordinates": [-59.6234, 13.1456]},
            {"stop_id": "DEPOT_MAIN", "stop_name": "Main Bus Depot", "coordinates": [-59.6462136, 13.2809774]},
            {"stop_id": "SOUTH_COAST_TERMINAL", "stop_name": "South Coast Terminal", "coordinates": [-59.5234, 13.0534]}
        ]
    
    def run_complete_demo(self):
        """Run the complete real-world data extraction demo."""
        print("=" * 80)
        print("🌍 REAL-WORLD DATA EXTRACTION DEMO")
        print("=" * 80)
        
        if not self.extractor:
            print("❌ Data extractor not available - showing conceptual demo")
            self.show_conceptual_demo()
            return
        
        # Step 1: Create data collection templates
        print("\n📋 STEP 1: Creating Data Collection Templates")
        print("-" * 50)
        self.demo_template_creation()
        
        # Step 2: Simulate field data collection
        print("\n📊 STEP 2: Simulating Field Data Collection")
        print("-" * 50)
        self.demo_field_data_collection()
        
        # Step 3: Distance and group analysis
        print("\n📏 STEP 3: Distance and Group Pattern Analysis")
        print("-" * 50)
        self.demo_distance_group_analysis()
        
        # Step 4: Model generation from real data
        print("\n🔧 STEP 4: Generating Model from Real Data")
        print("-" * 50)
        self.demo_model_generation()
        
        # Step 5: Data quality and validation
        print("\n✅ STEP 5: Data Quality and Validation")
        print("-" * 50)
        self.demo_quality_validation()
        
        print("\n✅ Real-world data extraction demo completed!")
        print("=" * 80)
    
    def show_conceptual_demo(self):
        """Show conceptual demo when components aren't available."""
        print("\n📋 CONCEPTUAL DEMO: Real-World Data Extraction Process")
        print("-" * 60)
        
        print("🎯 PURPOSE:")
        print("   Extract real-world passenger data to create accurate simulation models")
        print("   that account for distances, group patterns, and actual travel behavior")
        
        print("\n📊 DATA COLLECTION METHODS:")
        print("   1. Passenger Counting: Manual counts at stops during different periods")
        print("   2. Timing Analysis: Measure boarding times, dwell times, travel times")
        print("   3. Distance Surveys: Map where passengers walk from to reach stops")
        print("   4. Group Pattern Analysis: Observe how passengers travel in groups")
        print("   5. Trip Purpose Surveys: Ask passengers about their travel reasons")
        
        print("\n🔧 MODEL INTEGRATION:")
        print("   • Distance decay models based on walking distance observations")
        print("   • Group boarding patterns from field observations")
        print("   • Passenger rates calibrated to actual counts")
        print("   • Real-time factors based on observed conditions")
        
        print("\n📈 BENEFITS:")
        print("   ✓ Accurate passenger demand prediction")
        print("   ✓ Realistic group boarding behavior")
        print("   ✓ Distance-based catchment area modeling")
        print("   ✓ Data-driven capacity planning")
    
    def demo_template_creation(self):
        """Demonstrate creation of data collection templates."""
        print("📝 Creating survey templates for Routes 1, 1A, and 1B...")
        
        route_ids = ["1", "1A", "1B"]
        stop_ids = [stop["stop_id"] for stop in self.demo_route_stops]
        
        # Create survey template
        survey_template = self.extractor.create_survey_template(route_ids, stop_ids)
        
        print(f"✅ Created survey template with {len(survey_template['stops_to_survey'])} stops")
        print(f"📋 Survey periods: {len(survey_template['stops_to_survey'][0]['survey_periods'])} per stop")
        print(f"🎯 Trip purposes to track: {len(survey_template['trip_purpose_codes'])}")
        
        # Show sample template structure
        sample_stop = survey_template['stops_to_survey'][0]
        print(f"\n📍 Sample stop template: {sample_stop['stop_id']}")
        for period in sample_stop['survey_periods']:
            print(f"   • {period['period_type']}: {period['start_time']}-{period['end_time']}")
        
        # Create distance analysis template
        distance_template = self.extractor.create_distance_analysis_template(self.demo_route_stops)
        
        print(f"\n📏 Distance analysis template created")
        print(f"   • Catchment analysis for {len(distance_template['stops_analysis'])} stops")
        print(f"   • Primary catchment radius: {distance_template['stops_analysis'][0]['distance_analysis']['primary_catchment_radius_m']}m")
        
        # Save templates
        template_file = "survey_template_route_1.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(survey_template, f, indent=2)
        print(f"💾 Saved survey template to {template_file}")
        
        distance_file = "distance_analysis_template.json"
        with open(distance_file, 'w', encoding='utf-8') as f:
            json.dump(distance_template, f, indent=2)
        print(f"💾 Saved distance template to {distance_file}")
    
    def demo_field_data_collection(self):
        """Demonstrate simulated field data collection."""
        print("🚌 Simulating field data collection at key stops...")
        
        # Simulate morning peak data collection
        current_time = datetime.datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        
        # Bridgetown Terminal - busy terminal
        bridgetown_data = StopSurveyData(
            stop_id="BRIDGETOWN_TERMINAL",
            stop_name="Bridgetown Bus Terminal",
            survey_time=current_time,
            boarding_count=15,
            alighting_count=8,
            group_sizes=[1, 1, 2, 1, 3, 1, 1, 2, 1, 1, 4, 1, 2],  # Mix of solo and groups
            wait_times_seconds=[120, 180, 90, 240, 150, 200, 45, 300, 180, 120, 60, 210, 150],
            boarding_times_seconds=[3, 4, 6, 3, 8, 2, 3, 5, 4, 3, 12, 4, 7],
            trip_purposes=["commute_work", "commute_work", "shopping", "commute_work", 
                          "leisure", "commute_work", "business", "shopping", "commute_work",
                          "commute_work", "leisure", "medical", "shopping"],
            weather_condition="pleasant_weather",
            notes="Busy terminal, orderly queuing observed"
        )
        
        self.extractor.add_survey_data(bridgetown_data)
        
        # University - student-heavy location
        university_data = StopSurveyData(
            stop_id="UNIVERSITY_MAIN",
            stop_name="University of the West Indies",
            survey_time=current_time + datetime.timedelta(minutes=30),
            boarding_count=22,
            alighting_count=5,
            group_sizes=[2, 3, 1, 2, 4, 1, 3, 2, 1, 2, 3, 5, 1, 2, 3],  # Larger groups
            wait_times_seconds=[60, 90, 45, 120, 80, 150, 75, 100, 200, 90, 110, 85, 180, 95, 70],
            boarding_times_seconds=[5, 8, 3, 6, 10, 2, 7, 5, 4, 5, 9, 15, 3, 6, 8],
            trip_purposes=["commute_school", "commute_school", "commute_work", "commute_school",
                          "commute_school", "medical", "commute_school", "commute_school",
                          "business", "commute_school", "commute_school", "commute_school",
                          "commute_work", "commute_school", "commute_school"],
            weather_condition="pleasant_weather",
            notes="Student groups common, longer boarding times due to group coordination"
        )
        
        self.extractor.add_survey_data(university_data)
        
        # Main Depot - bus operations center
        depot_data = StopSurveyData(
            stop_id="DEPOT_MAIN",
            stop_name="Main Bus Depot",
            survey_time=current_time + datetime.timedelta(hours=1),  # Mid-morning
            boarding_count=25,
            alighting_count=5,
            group_sizes=[1, 1, 2, 1, 1, 3, 1, 2, 1, 1, 4, 1, 1, 2, 1, 1, 3, 2, 1, 1, 2],  # Mix of solo and small groups
            wait_times_seconds=[60, 90, 120, 45, 180, 100, 150, 80, 200, 70, 110, 95, 160, 85, 130, 75, 140, 105, 90, 120, 170],
            boarding_times_seconds=[3, 4, 5, 2, 3, 7, 4, 5, 3, 3, 9, 3, 3, 6, 4, 3, 8, 5, 3, 4, 6],
            trip_purposes=["commute_work", "commute_work", "shopping", "commute_work", "business", 
                          "commute_work", "medical", "commute_work", "commute_work", "shopping",
                          "leisure", "commute_work", "business", "shopping", "commute_work",
                          "commute_work", "leisure", "shopping", "commute_work", "business", "medical"],
            weather_condition="pleasant_weather",
            notes="Main departure point - high boarding, mostly work commute and connecting passengers"
        )
        
        self.extractor.add_survey_data(depot_data)
        
        print(f"📊 Collected survey data for {len(self.extractor.survey_data)} observation periods")
        
        # Analyze collected data
        for stop_id in ["BRIDGETOWN_TERMINAL", "UNIVERSITY_MAIN", "DEPOT_MAIN"]:
            group_analysis = self.extractor.analyze_group_patterns(stop_id)
            if group_analysis:
                print(f"\n📈 {stop_id} group patterns:")
                print(f"   Average group size: {group_analysis['average_group_size']:.1f}")
                dist = group_analysis['group_size_distribution']
                print(f"   Solo travelers: {dist['solo']:.1%}")
                print(f"   Pairs: {dist['pair']:.1%}")
                print(f"   Small groups (3-4): {dist['small_group_3_4']:.1%}")
    
    def demo_distance_group_analysis(self):
        """Demonstrate distance and group pattern analysis."""
        print("📏 Conducting distance analysis for key stops...")
        
        # Simulate distance data collection
        bridgetown_distance = DistanceAnalysisData(
            stop_id="BRIDGETOWN_TERMINAL",
            walking_distances_to_stop_m=[50, 120, 200, 350, 180, 450, 80, 300, 150, 400, 
                                        250, 100, 380, 220, 500, 90, 320, 180, 420, 160],
            passenger_origins=[(13.0980, -59.6150), (13.0965, -59.6135), (13.0955, -59.6145),
                              (13.0975, -59.6160), (13.0990, -59.6140), (13.0970, -59.6155)],
            competing_stops_distances_m=[300, 450, 200],
            accessibility_barriers=["Some curbs without ramps", "Busy street crossing"],
            land_use_types=["commercial", "institutional", "mixed_residential"]
        )
        
        self.extractor.add_distance_data(bridgetown_distance)
        
        # University distance analysis
        university_distance = DistanceAnalysisData(
            stop_id="UNIVERSITY_MAIN",
            walking_distances_to_stop_m=[80, 150, 250, 120, 300, 180, 220, 90, 350, 200,
                                       160, 280, 110, 240, 320, 140, 260, 190, 180, 210],
            passenger_origins=[(13.1465, -59.6240), (13.1450, -59.6225), (13.1470, -59.6250),
                              (13.1445, -59.6235), (13.1460, -59.6220), (13.1475, -59.6245)],
            competing_stops_distances_m=[150, 250],
            accessibility_barriers=["Steps at main entrance", "Limited lighting at night"],
            land_use_types=["institutional", "student_housing", "residential"]
        )
        
        self.extractor.add_distance_data(university_distance)
        
        print(f"📏 Analyzed walking distances for {len(self.extractor.distance_data)} stops")
        
        # Calculate distance decay parameters
        for stop_id in ["BRIDGETOWN_TERMINAL", "UNIVERSITY_MAIN"]:
            decay_params = self.extractor.calculate_distance_decay_parameters(stop_id)
            if decay_params:
                print(f"\n🎯 {stop_id} distance decay model:")
                print(f"   Function: {decay_params['decay_function']}")
                print(f"   Primary catchment: {decay_params['primary_radius_m']:.0f}m")
                print(f"   Secondary catchment: {decay_params['secondary_radius_m']:.0f}m")
                print(f"   Threshold distance: {decay_params['threshold_distance_m']:.0f}m")
    
    def demo_model_generation(self):
        """Demonstrate generating a passenger model from collected data."""
        print("🔧 Generating passenger model from collected real-world data...")
        
        # Export to model format
        model_file = "extracted_route_1_model.json"
        success = self.extractor.export_to_model_format(model_file, ["1", "1A", "1B"])
        
        if success:
            print(f"✅ Generated model file: {model_file}")
            
            # Load and display model summary
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    model_data = json.load(f)
                
                print(f"\n📊 Model Summary:")
                print(f"   Routes covered: {', '.join(model_data['model_info']['route_ids'])}")
                print(f"   Locations modeled: {len(model_data['locations'])}")
                print(f"   Distance models: {len(model_data['distance_analytics']['distance_decay_models'])}")
                
                # Show sample location data
                if model_data['locations']:
                    sample_location = list(model_data['locations'].values())[0]
                    print(f"\n📍 Sample location: {sample_location['stop_name']}")
                    rates = sample_location['passenger_rates']
                    if 'peak_hours' in rates:
                        peak_boarding = rates['peak_hours']['boarding']['rate_per_hour']
                        peak_alighting = rates['peak_hours']['alighting']['rate_per_hour']
                        print(f"   Peak boarding rate: {peak_boarding:.1f} passengers/hour")
                        print(f"   Peak alighting rate: {peak_alighting:.1f} passengers/hour")
                        print(f"   Data confidence: {rates['peak_hours']['boarding']['confidence_level']:.1%}")
                
            except Exception as e:
                print(f"⚠️ Could not load generated model: {e}")
        
        # Export survey data for further analysis
        csv_file = "survey_data_export.csv"
        csv_success = self.extractor.export_survey_data_csv(csv_file)
        if csv_success:
            print(f"📊 Exported survey data to {csv_file}")
    
    def demo_quality_validation(self):
        """Demonstrate data quality validation procedures."""
        print("✅ Demonstrating data quality validation...")
        
        # Generate data collection guide
        guide_file = "data_collection_guide.json"
        guide_success = self.extractor.generate_data_collection_guide(guide_file)
        
        if guide_success:
            print(f"📋 Generated data collection guide: {guide_file}")
            
            # Load and show guide highlights
            try:
                with open(guide_file, 'r', encoding='utf-8') as f:
                    guide = json.load(f)
                
                print(f"\n📋 Guide Highlights:")
                print(f"   Equipment needed: {len(guide['preparation']['equipment_needed'])} items")
                print(f"   Team requirements: {len(guide['preparation']['team_requirements'])} considerations")
                print(f"   Safety considerations: {len(guide['safety_considerations'])} points")
                
                # Show accuracy targets
                accuracy = guide['data_quality']['accuracy_targets']
                print(f"\n🎯 Accuracy Targets:")
                for target in accuracy:
                    print(f"   • {target}")
                
            except Exception as e:
                print(f"⚠️ Could not load guide: {e}")
        
        # Validation summary
        print(f"\n📈 Data Collection Summary:")
        print(f"   Survey observations: {len(self.extractor.survey_data)}")
        print(f"   Distance analyses: {len(self.extractor.distance_data)}")
        print(f"   Timing measurements: {len(self.extractor.timing_data)}")
        
        if self.extractor.survey_data:
            total_passengers = sum(s.boarding_count + s.alighting_count for s in self.extractor.survey_data)
            total_groups = sum(len(s.group_sizes) for s in self.extractor.survey_data)
            print(f"   Total passengers observed: {total_passengers}")
            print(f"   Total groups analyzed: {total_groups}")
            
            # Data quality indicators
            complete_surveys = [s for s in self.extractor.survey_data 
                              if s.boarding_count > 0 or s.alighting_count > 0]
            quality_score = len(complete_surveys) / len(self.extractor.survey_data)
            print(f"   Data completeness: {quality_score:.1%}")
        
        print(f"\n🔧 Next Steps for Real Implementation:")
        print(f"   1. Use generated templates for field data collection")
        print(f"   2. Follow data collection guide for accuracy")
        print(f"   3. Validate model against additional observations")
        print(f"   4. Calibrate model parameters based on seasonal patterns")
        print(f"   5. Integrate with real-time data sources")


def main():
    """Run the real-world data extraction demo."""
    demo = RealWorldExtractionDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()