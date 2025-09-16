#!/usr/bin/env python3
"""
Real-World Passenger Load Analysis
==================================

Analyze whether 50 concurrent passengers per route is realistic
compared to actual transit systems worldwide.
"""

def analyze_real_world_passenger_loads():
    print("🌍 REAL-WORLD PASSENGER LOAD ANALYSIS")
    print("=" * 50)
    
    print("📊 MAJOR TRANSIT SYSTEMS COMPARISON:")
    print("-" * 40)
    
    transit_systems = [
        {
            "city": "London, UK",
            "system": "Bus Network",
            "routes": 700,
            "daily_passengers": 6_500_000,
            "peak_hours": 4,  # 2 morning + 2 evening
            "service_hours": 20
        },
        {
            "city": "New York, USA", 
            "system": "MTA Bus",
            "routes": 234,
            "daily_passengers": 2_300_000,
            "peak_hours": 6,
            "service_hours": 24
        },
        {
            "city": "Singapore",
            "system": "SBS Transit",
            "routes": 250,
            "daily_passengers": 3_200_000,
            "peak_hours": 4,
            "service_hours": 18
        },
        {
            "city": "Hong Kong",
            "system": "KMB + Citybus",
            "routes": 400,
            "daily_passengers": 4_100_000,
            "peak_hours": 4,
            "service_hours": 20
        }
    ]
    
    print("Real-world concurrent passenger estimates:")
    print()
    
    for system in transit_systems:
        # Calculate concurrent passengers during peak
        peak_passenger_ratio = 0.4  # 40% of daily passengers during peak hours
        peak_passengers = system["daily_passengers"] * peak_passenger_ratio
        concurrent_per_route = peak_passengers / system["routes"]
        
        # Average journey time assumption (15-45 minutes)
        avg_journey_minutes = 25
        # Passengers board and alight continuously, so concurrent = throughput * journey_time
        concurrent_multiplier = avg_journey_minutes / 60  # Convert to hours
        estimated_concurrent = concurrent_per_route * concurrent_multiplier
        
        print(f"🚌 {system['city']} ({system['system']}):")
        print(f"   Routes: {system['routes']:,}")
        print(f"   Daily passengers: {system['daily_passengers']:,}")
        print(f"   Peak concurrent/route: ~{estimated_concurrent:.0f} passengers")
        print(f"   Peak throughput/route: ~{concurrent_per_route:.0f} passengers/hour")
        print()
    
    print("🏝️  BARBADOS SPECIFIC ANALYSIS:")
    print("-" * 35)
    
    # Barbados specific data
    barbados_population = 280_000
    transit_usage_rate = 0.15  # 15% use public transit daily
    daily_transit_users = barbados_population * transit_usage_rate
    
    # Barbados has fewer routes, higher density per route
    barbados_routes = 31  # From your system
    barbados_daily_per_route = daily_transit_users / barbados_routes
    
    # Peak hour analysis for Barbados
    peak_ratio = 0.35  # Higher ratio due to concentrated work/school hours
    peak_passengers_per_route = barbados_daily_per_route * peak_ratio
    
    # Journey times in Barbados (smaller island, shorter trips)
    avg_journey_barbados = 20  # minutes
    concurrent_barbados = peak_passengers_per_route * (avg_journey_barbados / 60)
    
    print(f"📍 Barbados Transit Analysis:")
    print(f"   Population: {barbados_population:,}")
    print(f"   Daily transit users: {daily_transit_users:,.0f}")
    print(f"   Routes: {barbados_routes}")
    print(f"   Daily passengers per route: {barbados_daily_per_route:.0f}")
    print(f"   Peak concurrent per route: {concurrent_barbados:.0f} passengers")
    print(f"   Peak throughput per route: {peak_passengers_per_route:.0f} passengers/hour")
    
    print(f"\n🎯 VERDICT ON 50 CONCURRENT PASSENGERS/ROUTE:")
    print("-" * 50)
    
    if concurrent_barbados >= 50:
        verdict = "✅ REALISTIC"
        explanation = "Barbados peak usage supports this level"
    elif concurrent_barbados >= 30:
        verdict = "⚠️  HIGH BUT POSSIBLE"
        explanation = "Above normal but achievable during peak events"
    else:
        verdict = "❌ UNREALISTIC"
        explanation = "Significantly higher than expected demand"
    
    print(f"   {verdict}")
    print(f"   Estimated realistic concurrent: {concurrent_barbados:.0f} passengers/route")
    print(f"   Your target: 50 passengers/route")
    print(f"   Assessment: {explanation}")
    
    return concurrent_barbados

def analyze_peak_scenarios():
    """Analyze special scenarios that could justify high passenger loads."""
    print(f"\n🎪 SPECIAL EVENT SCENARIOS:")
    print("-" * 30)
    
    scenarios = [
        {
            "event": "Crop Over Festival",
            "duration_days": 3,
            "visitor_increase": 50000,
            "transit_usage": 0.8,
            "description": "Major cultural festival, high tourist influx"
        },
        {
            "event": "Cricket Match (Kensington Oval)",
            "duration_hours": 8,
            "visitor_increase": 25000,
            "transit_usage": 0.6,
            "description": "International cricket, concentrated travel"
        },
        {
            "event": "School Term Start",
            "duration_weeks": 2,
            "visitor_increase": 15000,
            "transit_usage": 0.9,
            "description": "Students returning, parents driving less"
        },
        {
            "event": "Cruise Ship Days",
            "duration_hours": 10,  
            "visitor_increase": 8000,
            "transit_usage": 0.4,
            "description": "Multiple cruise ships in port"
        }
    ]
    
    for scenario in scenarios:
        extra_passengers = scenario["visitor_increase"] * scenario["transit_usage"]
        routes_affected = 15  # Assume half the routes affected by events
        extra_per_route = extra_passengers / routes_affected
        
        # Peak concentration (events create 2-3 hour surges)
        surge_multiplier = 3
        surge_concurrent = extra_per_route * surge_multiplier * (25/60)  # 25min journey
        
        print(f"📅 {scenario['event']}:")
        print(f"   Extra passengers: {extra_passengers:,.0f}")
        print(f"   Routes affected: {routes_affected}")
        print(f"   Surge concurrent/route: +{surge_concurrent:.0f} passengers")
        print(f"   Total concurrent: {15 + surge_concurrent:.0f} passengers/route")
        print(f"   {scenario['description']}")
        print()

def recommend_realistic_configuration():
    """Recommend a realistic configuration based on analysis."""
    print(f"\n🎯 REALISTIC CONFIGURATION RECOMMENDATIONS:")
    print("-" * 50)
    
    base_concurrent = 15  # Normal operations
    peak_concurrent = 25  # Peak hours
    event_concurrent = 45  # Special events
    
    print(f"📊 TIERED APPROACH:")
    print(f"   Normal operations: {base_concurrent} concurrent/route")
    print(f"   Peak hours: {peak_concurrent} concurrent/route") 
    print(f"   Special events: {event_concurrent} concurrent/route")
    print(f"   Emergency capacity: 50 concurrent/route")
    
    print(f"\n🔧 ADAPTIVE CONFIGURATION:")
    print(f"   Base: max_concurrent_spawns = {base_concurrent}")
    print(f"   Peak mode (7-9am, 4-6pm): max_concurrent_spawns = {peak_concurrent}")
    print(f"   Event mode (festivals, sports): max_concurrent_spawns = {event_concurrent}")
    print(f"   Emergency mode: max_concurrent_spawns = 50")
    
    print(f"\n⚡ CPU USAGE BY MODE:")
    # Rough CPU estimates based on previous analysis
    cpu_base = 35  # 15 passengers * scaling factor
    cpu_peak = 50  # 25 passengers
    cpu_event = 75  # 45 passengers
    cpu_emergency = 96  # 50 passengers (from previous analysis)
    
    print(f"   Normal: ~{cpu_base}% CPU (smooth operation)")
    print(f"   Peak: ~{cpu_peak}% CPU (good performance)")
    print(f"   Event: ~{cpu_event}% CPU (acceptable)")
    print(f"   Emergency: ~{cpu_emergency}% CPU (maximum capacity)")

if __name__ == "__main__":
    realistic_concurrent = analyze_real_world_passenger_loads()
    analyze_peak_scenarios()
    recommend_realistic_configuration()