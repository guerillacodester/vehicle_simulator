import asyncio
import httpx
import matplotlib.pyplot as plt
import numpy as np

async def validate_temporal_stats():
    """Validate that hourly spawn rates are realistic across 24 hours"""
    
    # Fetch spawn config
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "http://localhost:1337/api/spawn-configs?filters[country][name][$eq]=Barbados&populate=*"
        )
        data = response.json()
    
    config = data['data'][0]
    hourly_rates = sorted(config['hourly_spawn_rates'], key=lambda x: x['hour'])
    
    print("=" * 80)
    print("TEMPORAL SPAWN RATE VALIDATION - 24 Hour Analysis")
    print("=" * 80)
    print()
    
    # Display all hours
    print(f"{'Hour':<10} {'Rate':<10} {'Period':<20} {'Expected Demand':<25} {'Status'}")
    print("-" * 95)
    
    issues = []
    
    for h in hourly_rates:
        hour = h['hour']
        rate = h['spawn_rate']
        
        # Classify time period
        if 0 <= hour < 5:
            period = "Night"
            expected_range = (0.05, 0.2)
            expected_desc = "Minimal (night)"
        elif 5 <= hour < 6:
            period = "Pre-Dawn"
            expected_range = (0.1, 0.4)
            expected_desc = "Very Low (pre-dawn)"
        elif 6 <= hour < 7:
            period = "Early Morning"
            expected_range = (0.3, 1.0)
            expected_desc = "Low (early commute start)"
        elif 7 <= hour < 9:
            period = "Morning Peak"
            expected_range = (2.0, 3.0)
            expected_desc = "Peak (rush hour)"
        elif 9 <= hour < 12:
            period = "Mid-Morning"
            expected_range = (0.8, 1.5)
            expected_desc = "Moderate (post-peak)"
        elif 12 <= hour < 14:
            period = "Lunch"
            expected_range = (1.0, 1.8)
            expected_desc = "Moderate-High (lunch)"
        elif 14 <= hour < 17:
            period = "Afternoon"
            expected_range = (0.8, 1.5)
            expected_desc = "Moderate (afternoon)"
        elif 17 <= hour < 19:
            period = "Evening Peak"
            expected_range = (1.8, 2.8)
            expected_desc = "High (evening rush)"
        elif 19 <= hour < 22:
            period = "Evening"
            expected_range = (0.5, 1.2)
            expected_desc = "Low-Moderate (evening)"
        else:
            period = "Late Night"
            expected_range = (0.1, 0.4)
            expected_desc = "Very Low (late night)"
        
        # Check if rate is in expected range
        if expected_range[0] <= rate <= expected_range[1]:
            status = "✓ OK"
        elif rate < expected_range[0]:
            status = "⚠ TOO LOW"
            issues.append(f"Hour {hour}: Rate {rate} < expected minimum {expected_range[0]}")
        else:
            status = "⚠ TOO HIGH"
            issues.append(f"Hour {hour}: Rate {rate} > expected maximum {expected_range[1]}")
        
        print(f"{hour:<10} {rate:<10.2f} {period:<20} {expected_desc:<25} {status}")
    
    print()
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    if issues:
        print(f"⚠ FOUND {len(issues)} ISSUES:")
        print()
        for issue in issues:
            print(f"  • {issue}")
        print()
        print("RECOMMENDATION: Update spawn-config hourly_spawn_rates in database")
    else:
        print("✓ All hourly rates are within realistic ranges!")
    
    print()
    print("CURRENT SIMULATION (6:00-7:00 AM):")
    hour_6_rate = next(h['spawn_rate'] for h in hourly_rates if h['hour'] == 6)
    print(f"  Hour 6 rate: {hour_6_rate}")
    print(f"  Expected for rural pre-dawn: 0.3-1.0")
    
    if hour_6_rate > 1.0:
        print(f"  ⚠ PROBLEM: Rate too high for 6 AM rural area!")
        print(f"  This explains why 48 passengers spawned (should be ~10-20)")
    else:
        print(f"  ✓ Rate is realistic for early morning")
    
    # Calculate what passenger count we should expect
    print()
    print("EXPECTED PASSENGER COUNT (6:00-7:00 AM, rural area):")
    print(f"  With rate {hour_6_rate}: ~{48} passengers generated")
    print(f"  With recommended rate 0.5: ~{int(48 * 0.5 / hour_6_rate)} passengers expected")
    
    # Plot the rates
    hours = [h['hour'] for h in hourly_rates]
    rates = [h['spawn_rate'] for h in hourly_rates]
    
    plt.figure(figsize=(14, 6))
    plt.plot(hours, rates, marker='o', linewidth=2, markersize=6)
    plt.axhline(y=2.5, color='r', linestyle='--', alpha=0.3, label='Peak threshold')
    plt.axhline(y=1.0, color='orange', linestyle='--', alpha=0.3, label='Moderate threshold')
    plt.axhline(y=0.5, color='g', linestyle='--', alpha=0.3, label='Low threshold')
    plt.xlabel('Hour of Day', fontsize=12)
    plt.ylabel('Spawn Rate Multiplier', fontsize=12)
    plt.title('24-Hour Spawn Rate Pattern - Barbados', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.xticks(range(0, 24))
    plt.legend()
    plt.tight_layout()
    plt.savefig('hourly_spawn_rates.png', dpi=150)
    print()
    print("📊 Chart saved: hourly_spawn_rates.png")

asyncio.run(validate_temporal_stats())
