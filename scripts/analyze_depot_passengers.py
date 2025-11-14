"""
Analyze Depot Passengers from Database - Bar Charts

Queries spawned depot passengers and creates bar charts showing:
- Hourly distribution over 24 hours
- Daily distribution over full week
- Depot vs Route breakdown

Uses actual database records, not calculated expectations.
Async implementation for faster data fetching.
"""
import asyncio
import httpx
from collections import defaultdict
from datetime import datetime

STRAPI_URL = "http://localhost:1337"


async def fetch_page(client: httpx.AsyncClient, page: int, page_size: int = 100):
    """Fetch a single page of passengers"""
    response = await client.get(
        f"{STRAPI_URL}/api/active-passengers",
        params={
            'pagination[page]': page,
            'pagination[pageSize]': page_size,
            'sort': 'spawned_at:asc'
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Error fetching page {page}: {response.status_code}")
        return {"data": [], "meta": {}}
    
    return response.json()


async def fetch_all_passengers():
    """Fetch all passengers from database with concurrent pagination"""
    all_passengers = []
    page_size = 100
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, fetch page 1 to get total page count
        first_page_data = await fetch_page(client, 1, page_size)
        passengers = first_page_data.get('data', [])
        all_passengers.extend(passengers)
        
        # Get total pages
        meta = first_page_data.get('meta', {})
        pagination = meta.get('pagination', {})
        total_pages = pagination.get('pageCount', 1)
        
        if total_pages > 1:
            # Fetch remaining pages concurrently
            tasks = [fetch_page(client, page, page_size) for page in range(2, total_pages + 1)]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                passengers = result.get('data', [])
                all_passengers.extend(passengers)
    
    return all_passengers


def analyze_depot_passengers(passengers):
    """Analyze depot passengers by hour and day"""
    hourly_counts = defaultdict(int)
    daily_counts = defaultdict(int)
    weekly_hourly = defaultdict(lambda: defaultdict(int))  # day -> hour -> count
    
    depot_passengers = [p for p in passengers if p.get('depot_id')]
    
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for passenger in depot_passengers:
        spawned_at_str = passenger.get('spawned_at')
        if not spawned_at_str:
            continue
        
        # Parse spawned_at timestamp
        spawned_at = datetime.fromisoformat(spawned_at_str.replace('Z', '+00:00'))
        
        hour = spawned_at.hour
        day_of_week = spawned_at.weekday()  # 0=Monday, 6=Sunday
        
        hourly_counts[hour] += 1
        daily_counts[day_of_week] += 1
        weekly_hourly[day_of_week][hour] += 1
    
    return hourly_counts, daily_counts, weekly_hourly, day_names, depot_passengers


def print_bar_chart(title, data, labels=None, max_bar_width=50):
    """Print horizontal bar chart"""
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print()
    
    if not data:
        print("No data to display")
        return
    
    max_value = max(data.values()) if data else 1
    
    for key in sorted(data.keys()):
        value = data[key]
        bar_length = int((value / max_value) * max_bar_width) if max_value > 0 else 0
        bar = '█' * bar_length
        
        if labels:
            label = labels[key] if key < len(labels) else str(key)
            print(f"{label:>9}: {value:>4} |{bar}")
        else:
            print(f"  {key:>02d}:00 : {value:>4} |{bar}")
    
    print()
    print(f"Total: {sum(data.values())} passengers")


def print_weekly_hourly_breakdown(weekly_hourly, day_names):
    """Print 24-hour breakdown for each day of the week"""
    print()
    print("=" * 80)
    print("DEPOT PASSENGERS - HOURLY BREAKDOWN BY DAY OF WEEK")
    print("=" * 80)
    print()
    
    for day_idx in sorted(weekly_hourly.keys()):
        day_name = day_names[day_idx]
        hourly_data = weekly_hourly[day_idx]
        
        print(f"{day_name}")
        print("-" * 80)
        
        max_value = max(hourly_data.values()) if hourly_data else 1
        
        for hour in range(24):
            count = hourly_data.get(hour, 0)
            bar_length = int((count / max_value) * 40) if max_value > 0 else 0
            bar = '█' * bar_length
            print(f"  {hour:02d}:00 - {count:>3} passengers |{bar}")
        
        day_total = sum(hourly_data.values())
        print(f"  Daily Total: {day_total} passengers")
        print()


def main():
    print("=" * 80)
    print("DEPOT PASSENGERS ANALYSIS FROM DATABASE")
    print("=" * 80)
    print()
    
    # Fetch all passengers asynchronously
    print("Fetching passengers from database...")
    passengers = asyncio.run(fetch_all_passengers())
    print(f"✅ Fetched {len(passengers)} total passengers")
    
    if not passengers:
        print("❌ No passengers found in database!")
        return
    
    # Analyze depot passengers
    hourly_counts, daily_counts, weekly_hourly, day_names, depot_passengers = analyze_depot_passengers(passengers)
    
    print(f"✅ Found {len(depot_passengers)} depot passengers (with depot_id)")
    print(f"✅ Found {len(passengers) - len(depot_passengers)} route passengers (without depot_id)")
    
    if not depot_passengers:
        print()
        print("⚠️  No depot passengers found! Run spawn_full_week_combined.py to create depot passengers.")
        return
    
    # Print overall hourly distribution
    print_bar_chart("DEPOT PASSENGERS - HOURLY DISTRIBUTION (All Days Combined)", hourly_counts)
    
    # Print daily distribution
    print_bar_chart("DEPOT PASSENGERS - DAILY DISTRIBUTION (Full Week)", daily_counts, labels=day_names)
    
    # Print weekly hourly breakdown
    print_weekly_hourly_breakdown(weekly_hourly, day_names)
    
    # Summary statistics
    print()
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    print(f"Total Depot Passengers: {len(depot_passengers)}")
    print(f"Total Route Passengers: {len(passengers) - len(depot_passengers)}")
    print(f"Total All Passengers: {len(passengers)}")
    print()
    
    if hourly_counts:
        peak_hour = max(hourly_counts, key=hourly_counts.get)
        print(f"Peak Hour: {peak_hour:02d}:00 ({hourly_counts[peak_hour]} depot passengers)")
    
    if daily_counts:
        peak_day_idx = max(daily_counts, key=daily_counts.get)
        peak_day = day_names[peak_day_idx]
        print(f"Peak Day: {peak_day} ({daily_counts[peak_day_idx]} depot passengers)")
    
    print()
    
    # Calculate vans needed at peak
    if hourly_counts:
        peak_hour_count = max(hourly_counts.values())
        vans_at_peak = peak_hour_count / 15
        print(f"Vans needed at peak (15 passengers/van): {vans_at_peak:.1f} vans/hour")
    
    print()


if __name__ == "__main__":
    main()
