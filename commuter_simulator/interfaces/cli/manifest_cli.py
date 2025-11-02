"""
Manifest CLI
------------

Command-line interface for visualizing passenger manifests.

Usage:
    # Bar chart for full day
    python -m commuter_simulator.interfaces.cli.manifest_cli --day monday --route 1 --format barchart
    
    # Table for specific time range
    python -m commuter_simulator.interfaces.cli.manifest_cli --day monday --route 1 --format table --start-hour 7 --end-hour 9
    
    # Using specific date instead of day name
    python -m commuter_simulator.interfaces.cli.manifest_cli --date 2024-11-04 --route 1 --format table
"""
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import Optional
import httpx

from commuter_simulator.application.queries.manifest_visualization import (
    fetch_passengers_from_strapi,
    generate_barchart_data,
    format_barchart_ascii,
    enrich_passengers_with_geocoding,
    calculate_route_metrics,
    format_table_ascii
)
from commuter_simulator.infrastructure.config import get_config


# Load configuration
try:
    config = get_config()
    STRAPI_URL = config.infrastructure.strapi_url
    GEOSPATIAL_URL = config.infrastructure.geospatial_url
except Exception as e:
    print(f"⚠️  Warning: Could not load config.ini, using defaults: {e}")
    STRAPI_URL = "http://localhost:1337"
    GEOSPATIAL_URL = "http://localhost:6000"


async def get_route_id_from_name(route_short_name: str) -> Optional[str]:
    """Fetch route document ID from short name"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{STRAPI_URL}/api/routes")
        routes = response.json().get('data', [])
        
        for r in routes:
            if r.get('short_name') == route_short_name:
                return r.get('documentId')
    
    return None


def parse_target_date(day: Optional[str], date: Optional[str]) -> datetime:
    """Parse target date from --day or --date argument"""
    if date:
        return datetime.strptime(date, '%Y-%m-%d')
    
    # Map day name to a fixed base week
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    base_date = datetime(2024, 11, 4)  # Monday, Nov 4, 2024
    day_offset = day_map[day.lower()]
    return base_date + timedelta(days=day_offset)


async def display_barchart(args):
    """Display bar chart visualization"""
    target_date = parse_target_date(args.day, args.date)
    
    # Get route ID if specified
    route_id = None
    route_name = "All Routes"
    
    if args.route:
        route_id = await get_route_id_from_name(args.route)
        if not route_id:
            print(f"❌ Route '{args.route}' not found!")
            return
        route_name = f"Route {args.route}"
    
    # Fetch passengers
    print(f"📡 Fetching passengers from Strapi...")
    passengers = await fetch_passengers_from_strapi(
        strapi_url=STRAPI_URL,
        route_id=route_id,
        target_date=target_date,
        start_hour=args.start_hour,
        end_hour=args.end_hour
    )
    
    if not passengers:
        print(f"❌ No passengers found for {target_date.strftime('%A, %Y-%m-%d')} ({args.start_hour:02d}:00-{args.end_hour:02d}:00)")
        return
    
    # Generate and display bar chart
    barchart_data = generate_barchart_data(passengers)
    output = format_barchart_ascii(barchart_data, target_date, route_name)
    print(output)


async def display_table(args):
    """Display detailed table visualization"""
    target_date = parse_target_date(args.day, args.date)
    
    # Get route ID if specified
    route_id = None
    route_name = "All Routes"
    
    if args.route:
        route_id = await get_route_id_from_name(args.route)
        if not route_id:
            print(f"❌ Route '{args.route}' not found!")
            return
        route_name = f"Route {args.route}"
    
    # Fetch passengers
    print(f"📡 Fetching passengers from Strapi...")
    passengers = await fetch_passengers_from_strapi(
        strapi_url=STRAPI_URL,
        route_id=route_id,
        target_date=target_date,
        start_hour=args.start_hour,
        end_hour=args.end_hour
    )
    
    if not passengers:
        print(f"❌ No passengers found for {target_date.strftime('%A, %Y-%m-%d')} ({args.start_hour:02d}:00-{args.end_hour:02d}:00)")
        return
    
    # Enrich with geocoding
    print(f"🗺️  Fetching depot coordinates...")
    print(f"🗺️  Reverse geocoding {len(passengers)} passengers (batched)...")
    enriched_passengers = await enrich_passengers_with_geocoding(passengers, GEOSPATIAL_URL)
    print(f"   ✅ Geocoded {len(enriched_passengers)} passengers!")
    
    # Calculate metrics
    metrics = calculate_route_metrics(enriched_passengers)
    
    # Format and display table
    output = format_table_ascii(enriched_passengers, metrics, target_date, route_name)
    print(output)


async def main():
    parser = argparse.ArgumentParser(
        description="Display passenger manifest as bar chart or detailed table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Bar chart for full day
  python -m commuter_simulator.interfaces.cli.manifest_cli --day monday --route 1 --format barchart
  
  # Table for specific time range
  python -m commuter_simulator.interfaces.cli.manifest_cli --day monday --route 1 --format table --start-hour 7 --end-hour 9
  
  # Using specific date
  python -m commuter_simulator.interfaces.cli.manifest_cli --date 2024-11-04 --route 1 --format table
        """
    )
    
    parser.add_argument(
        '--day',
        choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        help='Day of week to display (alternative to --date)'
    )
    
    parser.add_argument(
        '--date',
        help='Specific date to display (YYYY-MM-DD format, alternative to --day)'
    )
    
    parser.add_argument(
        '--route',
        default=None,
        help='Route short_name (e.g., "1")'
    )
    
    parser.add_argument(
        '--format',
        choices=['barchart', 'table'],
        default='barchart',
        help='Output format: barchart (hourly distribution) or table (detailed list)'
    )
    
    parser.add_argument(
        '--start-hour',
        type=int,
        default=0,
        help='Start hour (0-23, default: 0)'
    )
    
    parser.add_argument(
        '--end-hour',
        type=int,
        default=23,
        help='End hour (0-23, default: 23)'
    )
    
    args = parser.parse_args()
    
    # Validate that either --day or --date is provided
    if not args.day and not args.date:
        parser.error("Either --day or --date must be specified")
    
    if args.day and args.date:
        parser.error("Cannot specify both --day and --date")
    
    # Validate hour range
    if args.start_hour < 0 or args.start_hour > 23:
        parser.error("--start-hour must be between 0 and 23")
    
    if args.end_hour < 0 or args.end_hour > 23:
        parser.error("--end-hour must be between 0 and 23")
    
    if args.start_hour > args.end_hour:
        parser.error("--start-hour cannot be greater than --end-hour")
    
    # Display based on format
    if args.format == 'barchart':
        await display_barchart(args)
    else:
        await display_table(args)


def cli_entrypoint():
    """Entry point for CLI execution"""
    asyncio.run(main())


if __name__ == "__main__":
    cli_entrypoint()
