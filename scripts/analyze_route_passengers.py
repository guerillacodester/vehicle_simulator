"""
Route Passengers Analysis
-------------------------

Query and visualize route passenger patterns from database.
Shows 24-hour distribution for each day of the week.
Async implementation for faster data fetching.

Usage:
    python scripts/analyze_route_passengers.py
"""

import asyncio
import httpx
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

STRAPI_URL = "http://localhost:1337"

async def fetch_page(client: httpx.AsyncClient, page: int, page_size: int = 100) -> Dict:
    """Fetch a single page of passengers"""
    response = await client.get(
        f"{STRAPI_URL}/api/active-passengers",
        params={
            "pagination[page]": page,
            "pagination[pageSize]": page_size,
            "sort": "spawned_at:asc"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Error fetching page {page}: {response.status_code}")
        return {"data": [], "meta": {}}
    
    return response.json()


async def fetch_all_passengers() -> List[Dict]:
    """Fetch all passengers from Strapi API with concurrent pagination"""
    all_passengers = []
    page_size = 100
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, fetch page 1 to get total page count
        first_page_data = await fetch_page(client, 1, page_size)
        passengers = first_page_data.get("data", [])
        all_passengers.extend(passengers)
        
        # Get total pages
        meta = first_page_data.get("meta", {})
        pagination = meta.get("pagination", {})
        total_pages = pagination.get("pageCount", 1)
        
        if total_pages > 1:
            # Fetch remaining pages concurrently
            tasks = [fetch_page(client, page, page_size) for page in range(2, total_pages + 1)]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                passengers = result.get("data", [])
                all_passengers.extend(passengers)
    
    return all_passengers


def analyze_passengers(passengers: List[Dict]) -> Dict:
    """Analyze route passengers by hour and day of week"""
    
    # Separate route passengers (those WITHOUT depot_id)
    route_passengers = [p for p in passengers if p.get("depot_id") is None]
    depot_passengers = [p for p in passengers if p.get("depot_id") is not None]
    
    print(f"✅ Fetched {len(passengers)} total passengers")
    print(f"✅ Found {len(route_passengers)} route passengers (without depot_id)")
    print(f"✅ Found {len(depot_passengers)} depot passengers (with depot_id)")
    
    # Group by hour (all days combined)
    hourly_counts = defaultdict(int)
    
    # Group by day of week
    daily_counts = defaultdict(int)
    
    # Group by day of week and hour
    day_hour_counts = defaultdict(lambda: defaultdict(int))
    
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for passenger in route_passengers:
        spawned_at = passenger.get("spawned_at")
        if not spawned_at:
            continue
        
        # Parse datetime
        dt = datetime.fromisoformat(spawned_at.replace("Z", "+00:00"))
        
        hour = dt.hour
        day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
        day_name = day_names[day_of_week]
        
        hourly_counts[hour] += 1
        daily_counts[day_name] += 1
        day_hour_counts[day_name][hour] += 1
    
    return {
        "total_route": len(route_passengers),
        "total_depot": len(depot_passengers),
        "total_all": len(passengers),
        "hourly_counts": hourly_counts,
        "daily_counts": daily_counts,
        "day_hour_counts": day_hour_counts
    }


def create_bar_chart(value: int, max_value: int, width: int = 50) -> str:
    """Create a simple ASCII bar chart"""
    if max_value == 0:
        return ""
    
    bar_length = int((value / max_value) * width)
    return "█" * bar_length


def display_results(analysis: Dict):
    """Display analysis results with bar charts"""
    
    print("\n" + "=" * 80)
    print("ROUTE PASSENGERS - HOURLY DISTRIBUTION (All Days Combined)")
    print("=" * 80)
    print()
    
    hourly = analysis["hourly_counts"]
    max_hourly = max(hourly.values()) if hourly else 1
    
    for hour in range(24):
        count = hourly.get(hour, 0)
        bar = create_bar_chart(count, max_hourly)
        print(f"  {hour:02d}:00 : {count:4d} |{bar}")
    
    print(f"\nTotal: {analysis['total_route']} passengers")
    
    # Daily distribution
    print("\n" + "=" * 80)
    print("ROUTE PASSENGERS - DAILY DISTRIBUTION (Full Week)")
    print("=" * 80)
    print()
    
    daily = analysis["daily_counts"]
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    max_daily = max(daily.values()) if daily else 1
    
    for day in day_order:
        count = daily.get(day, 0)
        bar = create_bar_chart(count, max_daily)
        print(f"{day:>10}: {count:4d} |{bar}")
    
    print(f"\nTotal: {analysis['total_route']} passengers")
    
    # Hourly breakdown by day
    print("\n" + "=" * 80)
    print("ROUTE PASSENGERS - HOURLY BREAKDOWN BY DAY OF WEEK")
    print("=" * 80)
    
    day_hour = analysis["day_hour_counts"]
    
    for day in day_order:
        print(f"\n{day}")
        print("-" * 80)
        
        day_data = day_hour.get(day, {})
        max_hour = max(day_data.values()) if day_data else 1
        daily_total = 0
        
        for hour in range(24):
            count = day_data.get(hour, 0)
            daily_total += count
            bar = create_bar_chart(count, max_hour)
            print(f"  {hour:02d}:00 - {count:3d} passengers |{bar}")
        
        print(f"  Daily Total: {daily_total} passengers")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    print(f"Total Route Passengers: {analysis['total_route']}")
    print(f"Total Depot Passengers: {analysis['total_depot']}")
    print(f"Total All Passengers: {analysis['total_all']}")
    print()
    
    # Find peak hour
    if hourly:
        peak_hour = max(hourly.items(), key=lambda x: x[1])
        print(f"Peak Hour: {peak_hour[0]:02d}:00 ({peak_hour[1]} route passengers)")
    
    # Find peak day
    if daily:
        peak_day = max(daily.items(), key=lambda x: x[1])
        print(f"Peak Day: {peak_day[0]} ({peak_day[1]} route passengers)")
    
    # Calculate vans needed
    if hourly:
        peak_passengers = max(hourly.values())
        vans_needed = peak_passengers / 15
        print(f"\nVans needed at peak (15 passengers/van): {vans_needed:.1f} vans/hour")


def main():
    """Main execution"""
    print("=" * 80)
    print("ROUTE PASSENGERS ANALYSIS FROM DATABASE")
    print("=" * 80)
    print()
    
    # Fetch passengers asynchronously
    print("Fetching passengers from database...")
    passengers = asyncio.run(fetch_all_passengers())
    
    if not passengers:
        print("❌ No passengers found")
        return
    
    # Analyze
    analysis = analyze_passengers(passengers)
    
    # Display
    display_results(analysis)


if __name__ == "__main__":
    main()
