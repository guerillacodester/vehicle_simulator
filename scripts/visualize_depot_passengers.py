"""
Depot Passenger Visualization - 24-Hour Bar Chart with Emojis

Fetches depot passengers from database and creates a beautiful colored bar chart
showing hourly distribution across the full week with emoji time indicators.
"""
import requests
from collections import defaultdict
from datetime import datetime
import sys


# ANSI Color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Hour colors (gradient throughout day)
    NIGHT = '\033[38;5;17m'      # Dark blue
    EARLY = '\033[38;5;33m'      # Blue
    MORNING = '\033[38;5;214m'   # Orange
    MIDDAY = '\033[38;5;226m'    # Yellow
    AFTERNOON = '\033[38;5;208m' # Dark orange
    EVENING = '\033[38;5;196m'   # Red
    LATE = '\033[38;5;93m'       # Purple
    
    # Bar colors
    BAR_LOW = '\033[38;5;28m'    # Green
    BAR_MED = '\033[38;5;220m'   # Yellow
    BAR_HIGH = '\033[38;5;202m'  # Orange
    BAR_PEAK = '\033[38;5;196m'  # Red


# Time period emojis
TIME_EMOJIS = {
    0: '🌙', 1: '🌙', 2: '🌙', 3: '🌙', 4: '🌙',           # Night
    5: '🌅', 6: '🌅',                                     # Dawn
    7: '🌄', 8: '🌄', 9: '🌄',                            # Morning
    10: '☀️', 11: '☀️',                                   # Mid-morning
    12: '🌞', 13: '🌞', 14: '🌞',                         # Midday
    15: '🌤️', 16: '🌤️', 17: '🌤️',                        # Afternoon
    18: '🌆', 19: '🌆',                                   # Evening
    20: '🌃', 21: '🌃', 22: '🌃', 23: '🌃'                # Night
}


def get_hour_color(hour):
    """Get color for hour based on time of day"""
    if 0 <= hour < 5:
        return Colors.NIGHT
    elif 5 <= hour < 7:
        return Colors.EARLY
    elif 7 <= hour < 10:
        return Colors.MORNING
    elif 10 <= hour < 14:
        return Colors.MIDDAY
    elif 14 <= hour < 17:
        return Colors.AFTERNOON
    elif 17 <= hour < 20:
        return Colors.EVENING
    else:
        return Colors.LATE


def get_bar_color(count, max_count):
    """Get bar color based on passenger count"""
    if max_count == 0:
        return Colors.BAR_LOW
    
    ratio = count / max_count
    if ratio >= 0.8:
        return Colors.BAR_PEAK
    elif ratio >= 0.5:
        return Colors.BAR_HIGH
    elif ratio >= 0.25:
        return Colors.BAR_MED
    else:
        return Colors.BAR_LOW


def fetch_depot_passengers():
    """Fetch all depot passengers from database"""
    STRAPI_URL = "http://localhost:1337"
    all_passengers = []
    page = 1
    page_size = 100
    
    print(f"{Colors.BOLD}📡 Fetching depot passengers from database...{Colors.RESET}")
    
    while True:
        response = requests.get(
            f"{STRAPI_URL}/api/active-passengers",
            params={
                'filters[depot_id][$notnull]': 'true',  # Only depot passengers
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
        
        meta = data.get('meta', {})
        pagination = meta.get('pagination', {})
        total = pagination.get('total', 0)
        
        print(f"   Fetched {len(all_passengers)}/{total} passengers...", end='\r')
        
        if page >= pagination.get('pageCount', 1):
            break
        
        page += 1
    
    print(f"\n{Colors.BOLD}✅ Fetched {len(all_passengers)} depot passengers{Colors.RESET}\n")
    return all_passengers


def analyze_by_day_hour(passengers):
    """Group passengers by day of week and hour"""
    day_hour_counts = defaultdict(lambda: defaultdict(int))
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for passenger in passengers:
        spawned_at_str = passenger.get('spawned_at')
        if not spawned_at_str:
            continue
        
        spawned_at = datetime.fromisoformat(spawned_at_str.replace('Z', '+00:00'))
        day_of_week = spawned_at.weekday()  # 0=Monday, 6=Sunday
        hour = spawned_at.hour
        
        day_hour_counts[day_of_week][hour] += 1
    
    return day_hour_counts, day_names


def print_24hour_barchart(day_hour_counts, day_names):
    """Print beautiful 24-hour bar chart for each day"""
    
    print(f"\n{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.BOLD}{'🚐 DEPOT PASSENGERS - 24-HOUR DISTRIBUTION BY DAY 🚐':^100}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*100}{Colors.RESET}\n")
    
    # Find global max for consistent scaling
    all_counts = [count for day_counts in day_hour_counts.values() for count in day_counts.values()]
    max_count = max(all_counts) if all_counts else 1
    max_bar_width = 50
    
    for day_idx in range(7):
        day_name = day_names[day_idx]
        hour_counts = day_hour_counts.get(day_idx, {})
        day_total = sum(hour_counts.values())
        
        # Day header with emoji
        day_emoji = "📅" if day_idx < 5 else "🎉" if day_idx == 5 else "☀️"
        print(f"\n{Colors.BOLD}{day_emoji}  {day_name.upper()}{Colors.RESET} (Total: {Colors.BOLD}{day_total}{Colors.RESET} passengers)")
        print(f"{Colors.BOLD}{'-'*100}{Colors.RESET}")
        
        # Print each hour
        for hour in range(24):
            count = hour_counts.get(hour, 0)
            
            # Calculate bar length
            bar_length = int((count / max_count) * max_bar_width) if max_count > 0 else 0
            
            # Get colors
            hour_color = get_hour_color(hour)
            bar_color = get_bar_color(count, max_count)
            
            # Build bar
            bar = '█' * bar_length
            
            # Time emoji
            emoji = TIME_EMOJIS.get(hour, '⏰')
            
            # Print formatted line
            hour_str = f"{hour:02d}:00"
            count_str = f"{count:>3}"
            
            print(f"{emoji} {hour_color}{hour_str}{Colors.RESET} {count_str} passengers │{bar_color}{bar}{Colors.RESET}")
        
        print()


def print_summary_stats(day_hour_counts, day_names):
    """Print summary statistics"""
    print(f"\n{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.BOLD}{'📊 SUMMARY STATISTICS 📊':^100}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*100}{Colors.RESET}\n")
    
    # Daily totals
    print(f"{Colors.BOLD}Daily Totals:{Colors.RESET}")
    for day_idx in range(7):
        day_name = day_names[day_idx]
        hour_counts = day_hour_counts.get(day_idx, {})
        day_total = sum(hour_counts.values())
        
        day_emoji = "📅" if day_idx < 5 else "🎉" if day_idx == 5 else "☀️"
        print(f"  {day_emoji}  {day_name:>9}: {Colors.BOLD}{day_total:>4}{Colors.RESET} passengers")
    
    # Weekly total
    total_passengers = sum(sum(counts.values()) for counts in day_hour_counts.values())
    print(f"\n{Colors.BOLD}📈 Weekly Total: {total_passengers} depot passengers{Colors.RESET}")
    
    # Peak hour analysis
    peak_hour = None
    peak_count = 0
    peak_day = None
    
    for day_idx, hour_counts in day_hour_counts.items():
        for hour, count in hour_counts.items():
            if count > peak_count:
                peak_count = count
                peak_hour = hour
                peak_day = day_idx
    
    if peak_hour is not None:
        peak_emoji = TIME_EMOJIS.get(peak_hour, '⏰')
        print(f"\n{Colors.BOLD}🔥 Peak Hour:{Colors.RESET}")
        print(f"  {peak_emoji}  {day_names[peak_day]} at {peak_hour:02d}:00 - {Colors.BOLD}{Colors.BAR_PEAK}{peak_count} passengers{Colors.RESET}")
        
        vans_needed = peak_count // 15 + (1 if peak_count % 15 > 0 else 0)
        print(f"  🚐  Vans needed (15 pass/van): {Colors.BOLD}{vans_needed}{Colors.RESET}")
    
    print()


def main():
    """Main visualization function"""
    try:
        # Fetch data
        passengers = fetch_depot_passengers()
        
        if not passengers:
            print(f"{Colors.BOLD}❌ No depot passengers found in database!{Colors.RESET}")
            print(f"   Run the spawning test first: python tests/integration/spawn_full_week_combined.py")
            return
        
        # Analyze
        day_hour_counts, day_names = analyze_by_day_hour(passengers)
        
        # Visualize
        print_24hour_barchart(day_hour_counts, day_names)
        print_summary_stats(day_hour_counts, day_names)
        
    except Exception as e:
        print(f"{Colors.BOLD}❌ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
