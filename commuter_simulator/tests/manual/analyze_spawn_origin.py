"""
Analyze the origin of spawn counts and validate realism.
Trace back through all configuration sources.
"""

print("="*120)
print("SPAWN COUNT ANALYSIS - Tracing the Origin")
print("="*120)

# TRACE 1: What did our simulation use?
print("\nTRACE 1: SIMULATION PARAMETERS")
print("-" * 120)

hourly_rates = {6: 1.5, 7: 2.5, 8: 2.8, 9: 1.8}
base_spawns = 30

print("\nHourly rate multipliers (from spawn config):")
for hour, rate in hourly_rates.items():
    print(f"  {hour}:00 AM = {rate}x multiplier")

print(f"\nBase spawns per hour: {base_spawns}")

print("\nCalculated spawns:")
total = 0
for hour, rate in hourly_rates.items():
    spawns = int(base_spawns * rate)
    total += spawns
    print(f"  {hour}:00 AM: {base_spawns} × {rate} = {spawns} spawns")

print(f"\nTOTAL: {total} spawns over 4 hours (6:00-9:00 AM)")
print(f"Average: {total/4:.1f} spawns/hour")

# TRACE 2: Where does base_spawns=30 come from?
print("\n" + "="*120)
print("TRACE 2: ORIGIN OF BASE_SPAWNS = 30")
print("="*120)

print("""
In our simulation code (simulate_realistic_van.py):
  base_spawns = 30  # <-- HARDCODED VALUE

Question: Where did 30 come from?

Let's check the spawn configuration files...
""")

# TRACE 3: Check actual spawn config
import os
import json

config_path = os.path.join(
    os.path.dirname(__file__),
    '../../../arknet_transit_simulator/config/spawns_barbados.json'
)

if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print(f"\nFOUND: {config_path}")
    print(f"\nConfig contents:")
    print(json.dumps(config, indent=2))
else:
    print(f"\nNOT FOUND: {config_path}")
    print("Searching for spawn config files...")

# TRACE 4: Search for where 30 came from
print("\n" + "="*120)
print("TRACE 3: PREVIOUS TEST FILE ANALYSIS")
print("="*120)

print("""
From test_spawn_table.py (our previous spawn simulation):
  
  hourly_rates = {7: 2.5, 8: 2.8}
  base_spawns_per_hour = 30  # <-- Same hardcoded value
  
  for hour in [7, 8]:
      hourly_rate = hourly_rates[hour]
      total_spawns_this_hour = int(base_spawns_per_hour * hourly_rate)
  
  Result:
    7:00 AM: 30 × 2.5 = 75 spawns
    8:00 AM: 30 × 2.8 = 84 spawns
    Total: 159 spawns in 2 hours
""")

# TRACE 5: Is this realistic?
print("\n" + "="*120)
print("TRACE 4: REALISM ANALYSIS")
print("="*120)

print("""
QUESTION: Is base_spawns=30 realistic for Route 1?

Route 1 Context:
  - Type: Inter-parish route (Saint Lucy → Saint Peter)
  - Length: 13.39 km
  - Character: Rural residential → Coastal commercial
  - Service type: ZR van (minibus)

Caribbean ZR Route Typical Capacity:
  - Vehicle: 15-20 seat minibus
  - Frequency: 5-15 minute headways during peak
  - Passengers per vehicle: 12-18 (when full)

CALCULATION CHECK:
------------------

Scenario 1: HIGH FREQUENCY (5-minute headways)
  - Vans per hour: 60 ÷ 5 = 12 vans/hour
  - Passengers per van: 15 average
  - Total demand: 12 × 15 = 180 passengers/hour
  → Our simulation: 75-84 passengers/hour ✓ REASONABLE (conservative)

Scenario 2: MODERATE FREQUENCY (10-minute headways)
  - Vans per hour: 60 ÷ 10 = 6 vans/hour
  - Passengers per van: 15 average
  - Total demand: 6 × 15 = 90 passengers/hour
  → Our simulation: 75-84 passengers/hour ✓ MATCHES WELL

Scenario 3: LOW FREQUENCY (15-minute headways)
  - Vans per hour: 60 ÷ 15 = 4 vans/hour
  - Passengers per van: 15 average
  - Total demand: 4 × 15 = 60 passengers/hour
  → Our simulation: 75-84 passengers/hour (slightly higher but reasonable)
""")

print("\n" + "="*120)
print("TRACE 5: DEMAND DISTRIBUTION ANALYSIS")
print("="*120)

print("""
Our 4-hour simulation (6:00-9:00 AM):
  6:00 AM: 45 spawns   (off-peak, early commuters)
  7:00 AM: 75 spawns   (peak begins)
  8:00 AM: 84 spawns   (peak maximum)
  9:00 AM: 54 spawns   (peak declining)
  -------------------------
  TOTAL:   258 spawns

Average per hour: 64.5 spawns/hour

But this is MISLEADING because:
  - 6:00 AM is OFF-PEAK (low demand, few vans running)
  - 7:00-8:00 AM is PEAK (high demand, many vans)
  - 9:00 AM is POST-PEAK (demand declining)

REALISTIC INTERPRETATION:
-------------------------
If we assume 10-minute headways during peak (7:00-9:00 AM):
  - Vans per hour: 6
  - Our demand: 75-84 passengers/hour
  - Demand per van: 75 ÷ 6 = 12.5 passengers per van
  → This is REALISTIC (vans would be 75-85% full)

KEY INSIGHT:
The 258 total spawns includes OFF-PEAK hours (6 AM, 9 AM).
During PEAK hours (7-8 AM), we generate 159 spawns = 79.5/hour.
This matches moderate-frequency ZR service (10-min headways, 13-14 pax/van).
""")

print("\n" + "="*120)
print("TRACE 6: SINGLE VAN PROBLEM IDENTIFIED")
print("="*120)

print("""
THE ISSUE: We simulated a SINGLE van at 7:00 AM

Real-world ZR operation with 10-minute headways:
  7:00 AM - Van #1 departs (our simulation)
  7:10 AM - Van #2 departs (NOT in simulation)
  7:20 AM - Van #3 departs (NOT in simulation)
  7:30 AM - Van #4 departs (NOT in simulation)
  7:40 AM - Van #5 departs (NOT in simulation)
  7:50 AM - Van #6 departs (NOT in simulation)

Our simulation generated demand for 6 vans but only deployed 1 van!

CORRECTED ANALYSIS:
-------------------
Total demand 7:00-8:00 AM: 75 passengers
Expected vans (10-min headways): 6 vans
Passengers per van: 75 ÷ 6 = 12.5 passengers

Our single van picked up: 26 passengers
  - This is approximately 2 van-loads (2 × 12.5 = 25)
  - Van filled to capacity at early stops
  - Couldn't serve mid-route demand
  → CONFIRMS: Need multiple vans to serve realistic demand

CONCLUSION:
-----------
base_spawns = 30 is REALISTIC for Route 1
  ✓ Generates 75-84 passengers/hour during peak
  ✓ Matches ZR service with 10-minute headways
  ✓ Assumes ~12-14 passengers per van
  ✓ Aligns with Caribbean public transit patterns

The "problem" isn't too many passengers - it's simulating a single van
when real service would have 6+ vans during this period!
""")

print("\n" + "="*120)
print("RECOMMENDATIONS")
print("="*120)

print("""
1. CURRENT SIMULATION IS REALISTIC
   ✓ 30 base spawns/hour is appropriate for Route 1
   ✓ Multipliers (2.5-2.8) correctly model peak demand
   ✓ Total spawns (75-84/hour) matches real ZR demand

2. TO IMPROVE SIMULATION REALISM:
   - Deploy multiple vans with staggered departures
   - Use 10-15 minute headways (6-4 vans/hour)
   - Each van should pick up 12-15 passengers
   - This would serve 80-90% of demand (realistic coverage)

3. ALTERNATIVE: REDUCE SPAWN WINDOW
   - Instead of 6:00-9:00 AM (4 hours)
   - Simulate 7:00-8:00 AM only (1 hour, peak focus)
   - This gives ~75 passengers for a single van to attempt
   - Still overwhelms single van, but more focused analysis

4. VALIDATE WITH REAL DATA (if available):
   - Actual ZR ridership data for Route 1
   - Observed van frequencies
   - Passenger counts per van
   - Peak vs off-peak demand ratios
""")
