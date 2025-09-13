"""
Demo: Location-Based Passenger Generation

This demonstrates how the system would work with actual location names GeoJSON data.
We'll create a mock dataset to show the concept.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime

# Create mock location data to demonstrate the concept
def create_mock_location_data():
    """Create mock location names data for demonstration"""
    
    # Mock locations around Barbados Route 1
    mock_locations = [
        # Around Bridgetown Terminal
        {"name": "Central Bank of Barbados", "type": "government", "lat": 13.1067, "lon": -59.6195},
        {"name": "Broad Street Shopping", "type": "commercial", "lat": 13.1065, "lon": -59.6200},
        {"name": "Bridgetown Port", "type": "transport", "lat": 13.1070, "lon": -59.6190},
        {"name": "St. Michael's Cathedral", "type": "religious", "lat": 13.1064, "lon": -59.6201},
        {"name": "Government Headquarters", "type": "government", "lat": 13.1069, "lon": -59.6198},
        
        # Around Main Transport Depot
        {"name": "Industrial Estate", "type": "industrial", "lat": 13.2810, "lon": -59.6460},
        {"name": "Sunset Apartments", "type": "residential", "lat": 13.2805, "lon": -59.6465},
        {"name": "Community Health Clinic", "type": "healthcare", "lat": 13.2812, "lon": -59.6458},
        {"name": "Workers Village", "type": "residential", "lat": 13.2808, "lon": -59.6463},
        {"name": "Transport Workers Union", "type": "government", "lat": 13.2811, "lon": -59.6461},
        
        # Around University Campus
        {"name": "Cave Hill Campus", "type": "educational", "lat": 13.1340, "lon": -59.6240},
        {"name": "Student Housing Complex", "type": "residential", "lat": 13.1345, "lon": -59.6235},
        {"name": "University Hospital", "type": "healthcare", "lat": 13.1338, "lon": -59.6242},
        {"name": "Faculty of Medicine", "type": "educational", "lat": 13.1342, "lon": -59.6238},
        {"name": "Campus Sports Centre", "type": "recreation", "lat": 13.1344, "lon": -59.6241},
        
        # Additional locations along the route
        {"name": "Plantation House", "type": "residential", "lat": 13.2000, "lon": -59.6300},
        {"name": "Sugar Factory", "type": "industrial", "lat": 13.2100, "lon": -59.6350},
        {"name": "Village Market", "type": "commercial", "lat": 13.1800, "lon": -59.6250},
        {"name": "Primary School", "type": "educational", "lat": 13.1900, "lon": -59.6280},
        {"name": "Community Centre", "type": "recreation", "lat": 13.2200, "lon": -59.6400},
    ]
    
    return mock_locations

def demonstrate_location_based_generation():
    """Demonstrate location-based passenger generation with mock data"""
    
    print("🌍 LOCATION-BASED PASSENGER GENERATION DEMONSTRATION")
    print("=" * 60)
    
    # Create mock data
    locations = create_mock_location_data()
    
    # Define passenger generation rates by location type
    generation_rates = {
        'residential': {'base_rate': 2.5, 'peak_multiplier': 3.0, 'description': 'Houses, apartments, communities'},
        'commercial': {'base_rate': 8.0, 'peak_multiplier': 2.5, 'description': 'Shops, markets, businesses'},
        'educational': {'base_rate': 15.0, 'peak_multiplier': 4.0, 'description': 'Schools, universities'},
        'healthcare': {'base_rate': 6.0, 'peak_multiplier': 1.8, 'description': 'Hospitals, clinics'},
        'government': {'base_rate': 4.0, 'peak_multiplier': 2.2, 'description': 'Offices, ministries'},
        'religious': {'base_rate': 3.0, 'peak_multiplier': 1.5, 'description': 'Churches, temples'},
        'recreation': {'base_rate': 4.5, 'peak_multiplier': 1.8, 'description': 'Parks, sports, entertainment'},
        'industrial': {'base_rate': 3.5, 'peak_multiplier': 2.8, 'description': 'Factories, warehouses'},
        'transport': {'base_rate': 12.0, 'peak_multiplier': 3.5, 'description': 'Stations, terminals, ports'},
    }
    
    print("📊 LOCATION TYPE ANALYSIS")
    print("-" * 30)
    
    # Group locations by type
    type_counts = {}
    for location in locations:
        loc_type = location['type']
        if loc_type not in type_counts:
            type_counts[loc_type] = 0
        type_counts[loc_type] += 1
    
    print("Location distribution around Route 1:")
    for loc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        rate_info = generation_rates.get(loc_type, {})
        base_rate = rate_info.get('base_rate', 1.0)
        description = rate_info.get('description', 'Unknown type')
        print(f"   🏢 {loc_type.title()}: {count} locations ({description})")
        print(f"      Base rate: {base_rate} passengers/hour/location")
    
    # Simulate passenger generation for different time periods
    time_periods = [
        (7, 30, "Morning Rush", 3.5),
        (12, 0, "Midday", 1.2),
        (17, 30, "Evening Rush", 3.0),
        (22, 0, "Evening", 1.0)
    ]
    
    print(f"\n🕐 PASSENGER GENERATION BY TIME PERIOD")
    print("-" * 40)
    
    for hour, minute, period_name, global_multiplier in time_periods:
        print(f"\n⏰ {period_name} ({hour:02d}:{minute:02d}) - Global multiplier: ×{global_multiplier}")
        
        total_passengers = 0
        location_breakdown = {}
        
        for location in locations:
            loc_type = location['type']
            rate_info = generation_rates.get(loc_type, {'base_rate': 1.0, 'peak_multiplier': 1.0})
            
            # Calculate passengers for this location (30-second generation period)
            base_rate = rate_info['base_rate']
            type_peak_multiplier = rate_info['peak_multiplier']
            
            # Total rate = base × global peak × type peak × time scaling
            hourly_rate = base_rate * global_multiplier * type_peak_multiplier
            passengers_30sec = hourly_rate / 120  # 120 thirty-second periods per hour
            
            # Use Poisson distribution for realistic variation
            passenger_count = max(0, np.random.poisson(passengers_30sec))
            
            if passenger_count > 0:
                if loc_type not in location_breakdown:
                    location_breakdown[loc_type] = {'count': 0, 'locations': []}
                location_breakdown[loc_type]['count'] += passenger_count
                location_breakdown[loc_type]['locations'].append({
                    'name': location['name'],
                    'passengers': passenger_count
                })
            
            total_passengers += passenger_count
        
        print(f"   👥 Total passengers generated: {total_passengers}")
        
        if location_breakdown:
            print("   📍 Breakdown by location type:")
            for loc_type, data in sorted(location_breakdown.items(), key=lambda x: x[1]['count'], reverse=True):
                print(f"      {loc_type.title()}: {data['count']} passengers")
                # Show top contributing locations
                top_locations = sorted(data['locations'], key=lambda x: x['passengers'], reverse=True)[:2]
                for loc in top_locations:
                    print(f"        • {loc['name']}: {loc['passengers']} passengers")
    
    # Show realistic passenger journey examples
    print(f"\n🚶 SAMPLE PASSENGER JOURNEYS")
    print("-" * 28)
    
    sample_journeys = [
        {
            'origin': 'Student Housing Complex',
            'origin_type': 'residential',
            'boarding_stop': 'University Campus',
            'walk_distance': 120,
            'trip_purpose': 'education',
            'time': '07:45'
        },
        {
            'origin': 'Government Headquarters',
            'origin_type': 'government',
            'boarding_stop': 'Bridgetown Terminal',
            'walk_distance': 85,
            'trip_purpose': 'work_commute',
            'time': '08:15'
        },
        {
            'origin': 'Workers Village',
            'origin_type': 'residential', 
            'boarding_stop': 'Main Transport Depot',
            'walk_distance': 200,
            'trip_purpose': 'work_commute',
            'time': '07:30'
        },
        {
            'origin': 'Broad Street Shopping',
            'origin_type': 'commercial',
            'boarding_stop': 'Bridgetown Terminal',
            'walk_distance': 150,
            'trip_purpose': 'shopping_leisure',
            'time': '14:20'
        }
    ]
    
    for i, journey in enumerate(sample_journeys, 1):
        walk_time = journey['walk_distance'] / 80  # 80m/min walking speed
        print(f"   🚶 Journey {i} at {journey['time']}:")
        print(f"      From: {journey['origin']} ({journey['origin_type']})")
        print(f"      To: {journey['boarding_stop']} stop")
        print(f"      Walk: {journey['walk_distance']}m ({walk_time:.1f} min)")
        print(f"      Purpose: {journey['trip_purpose']}")
    
    print(f"\n✅ BENEFITS OF LOCATION-BASED GENERATION")
    print("-" * 42)
    print("🎯 More realistic passenger origins (not just stops)")
    print("🎯 Walking distance and time modeling")
    print("🎯 Location-specific passenger generation rates")
    print("🎯 Trip purpose inference from origin type")
    print("🎯 Dynamic catchment areas around stops")
    print("🎯 Distance decay factors (closer = more passengers)")

if __name__ == "__main__":
    demonstrate_location_based_generation()