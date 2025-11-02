"""
Analyze spawned passengers from database and create bar charts
"""
import requests
from collections import defaultdict
from datetime import datetime

STRAPI_URL = "http://localhost:1337"

def fetch_all_passengers():
    """Fetch all passengers from database"""
    all_passengers = []
    page = 1
    page_size = 100
    
    while True:
        response = requests.get(
            f"{STRAPI_URL}/api/active-passengers",
            params={
                'pagination[page]': page,
                'pagination[pageSize]': page_size,
                'sort': 'spawned_at:asc'
            }
        )
        
        data = response.json()
        passengers = data.get('data', [])
        
        if not passengers:
            break
        
        all_passengers.extend(passengers)
        
        # Check if there are more pages
        meta = data.get('meta', {})
        pagination = meta.get('pagination', {})
        if page >= pagination.get('pageCount', 1):
            break
        
        page += 1
    
    return all_passengers


def analyze_passengers(passengers):
    """Analyze passengers by hour and day"""
    hourly_counts = defaultdict(int)
    daily_counts = defaultdict(int)
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for passenger in passengers:
        spawned_at_str = passenger.get('spawned_at')
        if not spawned_at_str:
            continue
        
        # Parse spawned_at timestamp
        spawned_at = datetime.fromisoformat(spawned_at_str.replace('Z', '+00:00'))
        
        hour = spawned_at.hour
        day_of_week = spawned_at.weekday()  # 0=Monday, 6=Sunday
        
        hourly_counts[hour] += 1
        daily_counts[day_of_week] += 1
    
    return hourly_counts, daily_counts, day_names


def print_bar_chart(title, data, labels=None, max_bar_width=60):
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
            print(f"{key:>9}: {value:>4} |{bar}")
    
    print()
    print(f"Total: {sum(data.values())} passengers")


def main():
    print("=" * 80)
    print("SPAWNED PASSENGERS ANALYSIS")
    print("=" * 80)
    print()
    
    # Fetch all passengers
    print("Fetching passengers from database...")
    passengers = fetch_all_passengers()
    print(f"✅ Fetched {len(passengers)} passengers")
    
    if not passengers:
        print("❌ No passengers found in database!")
        return
    
    # Analyze
    hourly_counts, daily_counts, day_names = analyze_passengers(passengers)
    
    # Print hourly distribution
    print_bar_chart("HOURLY DISTRIBUTION (All Days Combined)", hourly_counts)
    
    # Print daily distribution
    print_bar_chart("DAILY DISTRIBUTION (Full Week)", daily_counts, labels=day_names)
    
    # Summary statistics
    print()
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    print(f"Total Passengers: {len(passengers)}")
    print(f"Peak Hour: {max(hourly_counts, key=hourly_counts.get):02d}:00 ({hourly_counts[max(hourly_counts, key=hourly_counts.get)]} passengers)")
    print(f"Peak Day: {day_names[max(daily_counts, key=daily_counts.get)]} ({daily_counts[max(daily_counts, key=daily_counts.get)]} passengers)")
    print()
    
    # Check depot vs route distribution
    depot_count = sum(1 for p in passengers if p.get('depot_id'))
    route_count = len(passengers) - depot_count
    
    print(f"Depot Passengers: {depot_count}")
    print(f"Route Passengers: {route_count}")
    print()


if __name__ == "__main__":
    main()
