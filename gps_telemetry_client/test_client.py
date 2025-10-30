#!/usr/bin/env python3
"""
Simple CLI test tool for GPS telemetry client.

Demonstrates how to use the interface-agnostic library from a console application.

Usage:
    python test_client.py list
    python test_client.py watch
    python test_client.py poll --interval 2
"""

import argparse
import sys
import time
from datetime import datetime

# Import the interface-agnostic library
from gps_telemetry_client import (
    GPSTelemetryClient,
    CallbackObserver,
    Vehicle
)


def format_vehicle_line(vehicle: Vehicle) -> str:
    """Format vehicle data as single line."""
    driver = vehicle.get_driver_display_name()
    age = vehicle.get_age_seconds()
    stale = " [STALE]" if vehicle.is_stale() else ""
    
    return (
        f"{vehicle.deviceId:15} | "
        f"Route {vehicle.route:3} | "
        f"{vehicle.vehicleReg:8} | "
        f"({vehicle.lat:9.5f}, {vehicle.lon:9.5f}) | "
        f"Speed: {vehicle.speed:6.1f} km/h | "
        f"Heading: {vehicle.heading:6.1f}° | "
        f"Driver: {driver:20} | "
        f"Age: {age:4.0f}s{stale}"
    )


def cmd_list(client: GPSTelemetryClient, args):
    """List all devices (one-time snapshot)."""
    print("Fetching devices...\n")
    
    try:
        vehicles = client.get_all_devices()
        
        if not vehicles:
            print("No active devices found.")
            return
        
        print(f"Found {len(vehicles)} active device(s):\n")
        print("-" * 140)
        
        for vehicle in vehicles:
            print(format_vehicle_line(vehicle))
        
        print("-" * 140)
        print(f"\nTotal: {len(vehicles)} devices")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_watch(client: GPSTelemetryClient, args):
    """Watch devices in real-time (SSE streaming)."""
    device_filter = args.device_id or args.route
    filter_msg = ""
    if args.device_id:
        filter_msg = f" (device: {args.device_id})"
    elif args.route:
        filter_msg = f" (route: {args.route})"
    
    print(f"Watching GPS telemetry stream{filter_msg}...")
    print("Press Ctrl+C to stop\n")
    print("-" * 140)
    
    def on_update(vehicle: Vehicle):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {format_vehicle_line(vehicle)}")
    
    def on_connected():
        print("[CONNECTED] Stream started")
    
    def on_disconnected():
        print("\n[DISCONNECTED] Stream ended")
    
    def on_error(error: Exception):
        print(f"\n[ERROR] {error}", file=sys.stderr)
    
    # Register callback observer
    observer = CallbackObserver(
        on_vehicle_update=on_update,
        on_connected=on_connected,
        on_disconnected=on_disconnected,
        on_error=on_error
    )
    client.add_observer(observer)
    
    try:
        # Blocking stream (runs until Ctrl+C)
        client.start_stream(
            device_id=args.device_id,
            route_code=args.route,
            blocking=True
        )
    except KeyboardInterrupt:
        print("\n\nStopping stream...")
        client.stop_stream()


def cmd_poll(client: GPSTelemetryClient, args):
    """Poll devices at regular interval (HTTP polling)."""
    print(f"Polling every {args.interval}s (Press Ctrl+C to stop)\n")
    
    try:
        while True:
            timestamp = datetime.now().strftime('%H:%M:%S')
            vehicles = client.get_all_devices()
            
            print(f"\n[{timestamp}] Active devices: {len(vehicles)}")
            print("-" * 140)
            
            for vehicle in vehicles:
                print(format_vehicle_line(vehicle))
            
            print("-" * 140)
            
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n\nStopped polling.")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_analytics(client: GPSTelemetryClient, args):
    """Show fleet analytics."""
    print("Fetching analytics...\n")
    
    try:
        analytics = client.get_analytics()
        
        print(f"Total Active Devices: {analytics.totalDevices}\n")
        
        if analytics.routes:
            print("Per-Route Statistics:")
            print("-" * 60)
            print(f"{'Route':<10} {'Devices':<15} {'Avg Speed (km/h)':<20}")
            print("-" * 60)
            
            for route_code, stats in analytics.routes.items():
                print(f"{route_code:<10} {stats.count:<15} {stats.avgSpeed:<20.2f}")
            
            print("-" * 60)
        else:
            print("No route data available.")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_health(client: GPSTelemetryClient, args):
    """Check server health."""
    print("Checking server health...\n")
    
    try:
        health = client.get_health()
        
        print(f"Status:         {health.status.upper()}")
        print(f"Uptime:         {health.uptime_sec:.1f} seconds ({health.uptime_sec/60:.1f} minutes)")
        print(f"Active Devices: {health.devices}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="GPS Telemetry Test Client - Interface-agnostic library demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_client.py list
  python test_client.py watch
  python test_client.py watch --device-id GPS-ZR102
  python test_client.py watch --route 1
  python test_client.py poll --interval 2
  python test_client.py analytics
  python test_client.py health
        """
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='GPS server base URL (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--prefix',
        default='/gps',
        help='API prefix (default: /gps for unified services, use "" for standalone)'
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # List command
    subparsers.add_parser(
        'list',
        help='List all devices (one-time snapshot)'
    )
    
    # Watch command (SSE streaming)
    watch_parser = subparsers.add_parser(
        'watch',
        help='Watch devices in real-time (SSE streaming)'
    )
    watch_parser.add_argument(
        '--device-id',
        help='Filter to specific device ID'
    )
    watch_parser.add_argument(
        '--route',
        help='Filter to specific route code'
    )
    
    # Poll command (HTTP polling)
    poll_parser = subparsers.add_parser(
        'poll',
        help='Poll devices at regular interval'
    )
    poll_parser.add_argument(
        '--interval',
        type=int,
        default=1,
        help='Poll interval in seconds (default: 1)'
    )
    
    # Analytics command
    subparsers.add_parser(
        'analytics',
        help='Show fleet analytics'
    )
    
    # Health command
    subparsers.add_parser(
        'health',
        help='Check server health'
    )
    
    args = parser.parse_args()
    
    # Create client
    client = GPSTelemetryClient(base_url=args.url, api_prefix=args.prefix)
    
    # Test connection
    print(f"Connecting to {args.url}...")
    if not client.test_connection():
        print(f"Error: Cannot connect to {args.url}", file=sys.stderr)
        print("Make sure the GPS server is running.", file=sys.stderr)
        sys.exit(1)
    print("Connected!\n")
    
    # Execute command
    if args.command == 'list':
        cmd_list(client, args)
    elif args.command == 'watch':
        cmd_watch(client, args)
    elif args.command == 'poll':
        cmd_poll(client, args)
    elif args.command == 'analytics':
        cmd_analytics(client, args)
    elif args.command == 'health':
        cmd_health(client, args)


if __name__ == '__main__':
    main()
