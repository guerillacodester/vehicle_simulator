"""
Check raw spawn data to diagnose clustering issues
"""
import requests
from datetime import datetime

# Fetch route passengers
response = requests.get(
    'http://localhost:1337/api/active-passengers',
    params={
        'filters[depot_id][$null]': 'true',
        'pagination[pageSize]': 100,
        'sort': 'spawned_at:asc'
    }
)

data = response.json()['data']

print("=" * 120)
print("RAW PASSENGER DATA FROM DATABASE")
print("=" * 120)
print()

print(f"Total route passengers fetched: {len(data)}")
print()

# Group by spawn hour
from collections import defaultdict
hour_counts = defaultdict(int)
location_distribution = defaultdict(int)

for p in data:
    spawned_at = p.get('spawned_at', '')
    if spawned_at:
        dt = datetime.fromisoformat(spawned_at.replace('Z', '+00:00'))
        hour_counts[dt.hour] += 1
    
    # Round coordinates to see distribution
    lat = p.get('latitude', 0)
    lon = p.get('longitude', 0)
    lat_rounded = round(lat, 3)
    lon_rounded = round(lon, 3)
    location_distribution[(lat_rounded, lon_rounded)] += 1

print("SPAWN TIME DISTRIBUTION:")
print("-" * 40)
for hour in sorted(hour_counts.keys()):
    print(f"Hour {hour:02d}:00 - {hour_counts[hour]} passengers")

print()
print("LOCATION CLUSTERING (rounded to 3 decimals):")
print("-" * 60)
print(f"{'Count':<8} {'Latitude':<12} {'Longitude':<12}")
print("-" * 60)
for (lat, lon), count in sorted(location_distribution.items(), key=lambda x: -x[1])[:15]:
    print(f"{count:<8} {lat:<12.3f} {lon:<12.3f}")

print()
print("SAMPLE PASSENGERS (first 20):")
print("-" * 120)
print(f"{'#':<4} {'Spawn Time':<20} {'Start Lat':<12} {'Start Lon':<12} {'Dest Lat':<12} {'Dest Lon':<12} {'Same?':<6}")
print("-" * 120)

for idx, p in enumerate(data[:20], 1):
    spawn_time = p.get('spawned_at', 'N/A')[:19]
    start_lat = p.get('latitude', 0)
    start_lon = p.get('longitude', 0)
    dest_lat = p.get('destination_lat', 0)
    dest_lon = p.get('destination_lon', 0)
    
    same = "YES" if (start_lat == dest_lat and start_lon == dest_lon) else "NO"
    
    print(f"{idx:<4} {spawn_time:<20} {start_lat:<12.6f} {start_lon:<12.6f} {dest_lat:<12.6f} {dest_lon:<12.6f} {same:<6}")

print()
print("DIAGNOSIS:")
print("-" * 60)

# Check for identical start/destination
same_location_count = sum(1 for p in data if 
    p.get('latitude') == p.get('destination_lat') and 
    p.get('longitude') == p.get('destination_lon'))

if same_location_count > 0:
    print(f"⚠️  {same_location_count} passengers have IDENTICAL start and destination!")
    print(f"   This causes 0.00 km commute distances")

# Check for clustering
unique_locations = len(location_distribution)
print(f"\n📊 {unique_locations} unique pickup locations (out of {len(data)} passengers)")
if len(data) > 0 and unique_locations / len(data) < 0.3:
    print(f"⚠️  Only {unique_locations/len(data)*100:.1f}% unique locations - severe clustering!")

# Check time distribution
unique_hours = len(hour_counts)
print(f"\n⏰ Passengers spawned across {unique_hours} different hours")
for hour, count in sorted(hour_counts.items()):
    print(f"   {hour:02d}:00 - {count} passengers")
