#!/usr/bin/env python3
"""
Commuter Service Client Console

Interactive console client for remote commuter service management.
Can connect to local or remote commuter service instances.

Usage:
    python clients/commuter/client_console.py
    
    # Commands:
    connect [url]        - Connect to commuter service (default: http://localhost:4000)
    disconnect           - Disconnect from service
    manifest <route>     - Get manifest for route
    barchart <route>     - Get barchart for route
    subscribe <route>    - Subscribe to real-time events
    unsubscribe <route>  - Unsubscribe from events
    seed <route> <day> <start-end> - Seed passengers (e.g., seed 1 monday 7-9)
    stats                - Show connection statistics
    help                 - Show this help
    exit                 - Exit console
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import httpx

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clients.commuter.connector import CommuterConnector, EventType


class CommuterConsole:
    """Interactive console for remote commuter service management"""
    
    def __init__(self):
        self.connector: Optional[CommuterConnector] = None
        self.running = False
        self.event_count = 0
        self.streaming = False
        self.base_url = "http://localhost:4000"
        
    async def start(self):
        """Start the console"""
        print("=" * 80)
        print("COMMUTER SERVICE CLIENT CONSOLE")
        print("=" * 80)
        print("Type 'help' for commands, 'exit' to quit")
        print()
        
        self.running = True
        
        while self.running:
            try:
                # Get command
                cmd_input = await asyncio.to_thread(input, "commuter> ")
                cmd_input = cmd_input.strip()
                
                if not cmd_input:
                    continue
                
                # Parse command
                parts = cmd_input.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                # Execute command
                await self.execute_command(cmd, args)
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Use 'exit' to quit")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def execute_command(self, cmd: str, args: list):
        """Execute a console command"""
        
        if cmd == "help":
            self.show_help()
        
        elif cmd == "exit" or cmd == "quit":
            print("Disconnecting...")
            if self.connector:
                await self.connector.disconnect()
            self.running = False
            print("Goodbye!")
        
        elif cmd == "connect":
            url = args[0] if args else None
            await self.cmd_connect(url)
        
        elif cmd == "disconnect":
            await self.cmd_disconnect()
        
        elif cmd == "manifest":
            route = args[0] if args else "1"
            date = args[1] if len(args) > 1 else None
            hours = args[2] if len(args) > 2 else None
            await self.cmd_manifest(route, date, hours)
        
        elif cmd == "barchart":
            route = args[0] if args else "1"
            date = args[1] if len(args) > 1 else None
            await self.cmd_barchart(route, date)
        
        elif cmd == "json":
            route = args[0] if args else "1"
            date = args[1] if len(args) > 1 else None
            await self.cmd_json(route, date)
        
        elif cmd == "subscribe":
            route = args[0] if args else "1"
            await self.cmd_subscribe(route)
        
        elif cmd == "unsubscribe":
            route = args[0] if args else "1"
            await self.cmd_unsubscribe(route)
        
        elif cmd == "seed":
            if len(args) < 3:
                print("❌ Usage: seed <route> <day> <start-end>")
                print("   Example: seed 1 monday 7-9")
                return
            route = args[0]
            day = args[1]
            hours = args[2]
            await self.cmd_seed(route, day, hours)
        
        elif cmd == "list":
            await self.cmd_list_passengers(args)
        
        elif cmd == "get":
            if not args:
                print("❌ Usage: get <passenger_id>")
                return
            await self.cmd_get_passenger(args[0])
        
        elif cmd == "board":
            if len(args) < 2:
                print("❌ Usage: board <passenger_id> <vehicle_id>")
                return
            await self.cmd_board(args[0], args[1])
        
        elif cmd == "alight":
            if not args:
                print("❌ Usage: alight <passenger_id>")
                return
            await self.cmd_alight(args[0])
        
        elif cmd == "cancel":
            if not args:
                print("❌ Usage: cancel <passenger_id>")
                return
            await self.cmd_cancel(args[0])
        
        elif cmd == "delete":
            await self.cmd_delete(args)
        
        elif cmd == "monitor":
            await self.cmd_monitor_stats()
        
        elif cmd == "stats":
            self.cmd_stats()
        
        else:
            print(f"Unknown command: {cmd}")
            print("Type 'help' for available commands")
    
    def show_help(self):
        """Show help message"""
        print()
        print("=" * 80)
        print("AVAILABLE COMMANDS")
        print("=" * 80)
        print("CONNECTION:")
        print("  connect [url]               - Connect to service (default: http://localhost:4000)")
        print("  disconnect                  - Disconnect from service")
        print()
        print("QUERIES:")
        print("  manifest <route> [date] [start_hour-end_hour]  - Manifest table")
        print("                                                    Examples:")
        print("                                                      manifest 1")
        print("                                                      manifest 1 2024-11-04")
        print("                                                      manifest 1 2024-11-04 7-9")
        print("  json <route> <date>         - Get raw JSON manifest data")
        print("  barchart <route> <date>     - Get barchart for route")
        print("  list [filters]              - List passengers with filters")
        print("                                  list route=1 status=WAITING")
        print("                                  list vehicle=BUS_001")
        print("  get <passenger_id>          - Get single passenger details")
        print()
        print("PASSENGER MANAGEMENT:")
        print("  board <id> <vehicle_id>     - Board passenger onto vehicle")
        print("  alight <id>                 - Alight passenger from vehicle")
        print("  cancel <id>                 - Cancel passenger")
        print("  delete [filters]            - Delete passengers with confirmation")
        print("                                  delete route=1")
        print("                                  delete date=2024-11-04")
        print("                                  delete route=1 status=WAITING")
        print("                                  delete route=1 date=2024-11-04 hours=7-9")
        print()
        print("SEEDING:")
        print("  seed <route> <day> <hrs>    - Seed passengers (e.g., seed 1 monday 7-9)")
        print()
        print("REAL-TIME:")
        print("  subscribe <route>           - Subscribe to real-time events (WebSocket)")
        print("  unsubscribe <route>         - Unsubscribe from events")
        print("  monitor                     - Show monitor statistics")
        print()
        print("SYSTEM:")
        print("  stats                       - Show connection statistics")
        print("  help                        - Show this help")
        print("  exit                        - Exit console")
        print("=" * 80)
        print()
    
    async def cmd_connect(self, url: Optional[str] = None):
        """Connect to commuter service"""
        if url:
            self.base_url = url
        
        print(f"Connecting to Commuter Service at {self.base_url}...")
        
        try:
            self.connector = CommuterConnector(
                base_url=self.base_url
            )
            
            # Subscribe to events
            self.connector.on('passenger:spawned', self.on_passenger_event)
            self.connector.on('passenger:boarded', self.on_passenger_event)
            self.connector.on('passenger:alighted', self.on_passenger_event)
            
            await self.connector.connect()
            
            print(f"✅ Connected successfully!")
            print(f"   HTTP API: {self.base_url}")
            
            if self.connector.is_websocket_connected:
                print(f"   WebSocket: ✅ Connected")
            else:
                print(f"   WebSocket: ⚠️ Not available (real-time streaming disabled)")
                print(f"   Note: HTTP queries still work (manifest, barchart, seed)")
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    async def cmd_disconnect(self):
        """Disconnect from service"""
        if not self.connector:
            print("Not connected")
            return
        
        await self.connector.disconnect()
        self.connector = None
        print("Disconnected")
    
    async def cmd_subscribe(self, route: str):
        """Subscribe to real-time events for a route"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        if not self.connector.is_websocket_connected:
            print("❌ WebSocket not connected. Real-time events unavailable.")
            return
        
        await self.connector.subscribe(route)
        print(f"📡 Subscribed to Route {route} events")
        print("   Listening for passenger:spawned, passenger:boarded, passenger:alighted")
    
    async def cmd_unsubscribe(self, route: str):
        """Unsubscribe from route events"""
        if not self.connector:
            print("❌ Not connected.")
            return
        
        if not self.connector.is_websocket_connected:
            return
        
        await self.connector.unsubscribe(route)
        print(f"🔕 Unsubscribed from Route {route}")
    
    async def cmd_manifest(self, route: str, date: Optional[str] = None, hours: Optional[str] = None):
        """Get manifest for route - displays all passengers in table format
        
        Args:
            route: Route short name (e.g., "1")
            date: Optional date filter (YYYY-MM-DD)
            hours: Optional hour range (e.g., "7-9" for 07:00-09:59)
        """
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        # Parse hour range
        start_hour, end_hour = None, None
        if hours:
            try:
                parts = hours.split('-')
                start_hour = int(parts[0])
                end_hour = int(parts[1]) if len(parts) > 1 else start_hour
            except:
                print(f"⚠️  Invalid hour range: {hours}. Use format: 7-9")
                return
        
        date_str = f" on {date}" if date else " (all dates)"
        hours_str = f" {start_hour:02d}:00-{end_hour:02d}:59" if hours else ""
        print(f"Fetching manifest for Route {route}{date_str}{hours_str}...")
        
        try:
            # Fetch passengers with filters
            manifest = await self.connector.get_manifest(
                route=route, 
                date=date, 
                start_hour=start_hour,
                end_hour=end_hour,
                limit=1000
            )
            passengers = manifest.passengers
            total = manifest.count
            
            print()
            print("=" * 140)
            print(f"PASSENGER MANIFEST - Route {route}{date_str}")
            print("=" * 140)
            print(f"Total Passengers: {total}")
            print("=" * 140)
            print()
            
            if passengers:
                # Table header
                print(f"{'#':<5} {'Passenger ID':<20} {'Time':<8} {'Status':<10} {'Start Lat':<11} {'Start Lon':<11} {'Stop Lat':<11} {'Stop Lon':<11} {'Distance':<10}")
                print("-" * 140)
                
                # Table rows
                for i, p in enumerate(passengers, 1):
                    passenger_id = p.get('passenger_id', 'N/A')
                    
                    # Format spawn time
                    spawn_time = p.get('spawned_at', 'N/A')
                    if spawn_time != 'N/A':
                        try:
                            dt = datetime.fromisoformat(spawn_time.replace('Z', '+00:00'))
                            spawn_time = dt.strftime('%H:%M')
                        except:
                            spawn_time = 'N/A'
                    
                    status = p.get('status', 'N/A')
                    
                    # Get coordinates - use correct field names from API
                    start_lat = p.get('latitude', 'N/A')
                    start_lon = p.get('longitude', 'N/A')
                    stop_lat = p.get('destination_lat', 'N/A')
                    stop_lon = p.get('destination_lon', 'N/A')
                    
                    # Format coordinates
                    if start_lat != 'N/A' and start_lat is not None:
                        start_lat = f"{start_lat:.6f}"
                    else:
                        start_lat = 'N/A'
                    
                    if start_lon != 'N/A' and start_lon is not None:
                        start_lon = f"{start_lon:.6f}"
                    else:
                        start_lon = 'N/A'
                    
                    if stop_lat != 'N/A' and stop_lat is not None:
                        stop_lat = f"{stop_lat:.6f}"
                    else:
                        stop_lat = 'N/A'
                    
                    if stop_lon != 'N/A' and stop_lon is not None:
                        stop_lon = f"{stop_lon:.6f}"
                    else:
                        stop_lon = 'N/A'
                    
                    # Get distance
                    distance = p.get('travel_distance_km', 'N/A')
                    if distance != 'N/A' and isinstance(distance, (int, float)):
                        distance = f"{distance:.2f} km"
                    
                    print(f"{i:<5} {passenger_id:<20} {spawn_time:<8} {status:<10} {start_lat:<11} {start_lon:<11} {stop_lat:<11} {stop_lon:<11} {distance:<10}")
                
                print()
            
            print("=" * 140)
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_json(self, route: str, date: Optional[str] = None):
        """Get raw JSON manifest data"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        date_str = f" on {date}" if date else " (all dates)"
        print(f"Fetching JSON manifest for Route {route}{date_str}...")
        
        try:
            import json
            
            # Fetch ALL passengers (limit=1000)
            manifest = await self.connector.get_manifest(route=route, date=date, limit=1000)
            
            # Convert Pydantic model to dict
            manifest_dict = manifest.model_dump()
            
            # Pretty print JSON
            print()
            print(json.dumps(manifest_dict, indent=2, default=str))
            print()
            print(f"Total: {manifest_dict['count']} passengers")
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_barchart(self, route: str, date: Optional[str] = None):
        """Get barchart for route"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        date_str = f" on {date}" if date else " (all dates)"
        print(f"Fetching barchart for Route {route}{date_str}...")
        
        try:
            # Note: connector uses 'day' parameter, not 'date'
            data = await self.connector.get_barchart(route=route)
            hourly_counts = data.get('hourly_counts', [])
            total = data.get('total', 0)
            peak_hour = data.get('peak_hour', 0)
            
            print()
            print("=" * 80)
            print(f"BARCHART - Route {route}{date_str}")
            print("=" * 80)
            print(f"Total: {total} | Peak Hour: {peak_hour}:00")
            print("=" * 80)
            
            if not hourly_counts:
                print("⚠️  No hourly data available")
                print(f"Debug: hourly_counts={hourly_counts}")
            else:
                max_count = max(hourly_counts) if hourly_counts else 1
                for hour, count in enumerate(hourly_counts):
                    if count > 0:  # Only show hours with passengers
                        bar_width = int((count / max_count) * 50) if max_count > 0 else 0
                        bar = "█" * bar_width
                        peak = "🔥" if hour == peak_hour else "  "
                        print(f"{hour:>2}:00 │ {bar:<50} {count:>3} {peak}")
            
            print("=" * 80)
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_stream(self, route: str):
        """Stream real-time events for route"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        if not self.connector.is_websocket_connected:
            print("❌ Socket.IO not connected. Real-time streaming unavailable.")
            return
        
        print()
        print("=" * 80)
        print(f"🔴 STREAMING EVENTS - Route {route}")
        print("=" * 80)
        print("Press Ctrl+C to stop streaming")
        print()
        
        self.streaming = True
        self.event_count = 0
        self.hourly_counts = {}
        
        try:
            async for event in self.connector.stream_events(route=route):
                if not self.streaming:
                    break
                
                self.event_count += 1
                hour = event.timestamp.hour
                self.hourly_counts[hour] = self.hourly_counts.get(hour, 0) + 1
                
                print(f"🚶 #{self.event_count:>4} | {event.event_type.value:<20} | Hour {hour:>2}:00 | Total: {self.hourly_counts[hour]:>3}")
        
        except KeyboardInterrupt:
            print("\n⏹️  Streaming stopped")
            self.streaming = False
    
    async def cmd_seed(self, route: str, day: str, hours: str):
        """Trigger passenger seeding on the server"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        # Parse hours (e.g., "7-9")
        try:
            start_hour, end_hour = map(int, hours.split('-'))
        except:
            print("❌ Invalid hours format. Use: seed <route> <day> <start-end> (e.g., seed 1 monday 7-9)")
            return
        
        print()
        print("=" * 80)
        print(f"🌱 SEEDING PASSENGERS")
        print("=" * 80)
        print(f"Route:        {route}")
        print(f"Day:          {day}")
        print(f"Hours:        {start_hour}:00 - {end_hour}:00")
        print("=" * 80)
        print()
        
        # Subscribe to route if WebSocket is available
        if self.connector.is_websocket_connected:
            print("📡 Subscribing to real-time seeding events...")
            
            # Set up event handlers for seed progress
            seed_event_count = [0]  # Use list for mutable counter in closure
            current_hour = [None]
            
            def on_seed_progress(data):
                """Handle individual passenger spawn events"""
                seed_event_count[0] += 1
                hour = data.get('hour', 0)
                passenger_id = data.get('passenger_id', 'UNKNOWN')
                total = data.get('total_so_far', 0)
                spawn_time = data.get('spawn_time', '')
                
                # Only show every 10th passenger to avoid spam
                if seed_event_count[0] % 10 == 0 or seed_event_count[0] == 1:
                    print(f"   └─ {passenger_id[:20]}... at {spawn_time[11:19]} (Total: {total})")
            
            def on_hour_complete(data):
                """Handle hour completion events"""
                hour = data.get('hour', 0)
                passengers = data.get('passengers_this_hour', 0)
                total = data.get('total_so_far', 0)
                percent = data.get('progress_percent', 0)
                completed = data.get('hours_completed', 0)
                total_hours = data.get('total_hours', 0)
                
                bar_width = int((percent / 100) * 50)
                bar = "█" * bar_width + "░" * (50 - bar_width)
                print(f"\n✅ Hour {hour:02d}:00 complete - {passengers} passengers spawned")
                print(f"   Progress: [{bar}] {percent:.1f}% ({completed}/{total_hours} hours) | Total: {total}")
            
            self.connector.on('seed:progress', on_seed_progress)
            self.connector.on('seed:hour_complete', on_hour_complete)
            await self.connector.subscribe(route)
            self.event_count = 0
            print()
        
        try:
            print("⏳ Triggering seeding on server...")
            
            result = await self.connector.seed_passengers(
                route=route,
                day=day,
                spawn_type="route",
                start_hour=start_hour,
                end_hour=end_hour
            )
            
            # Wait a bit for events to arrive
            if self.connector.is_websocket_connected:
                await asyncio.sleep(2)
            
            print()
            print("=" * 80)
            print("✅ SEEDING COMPLETE")
            print("=" * 80)
            
            # Safely access result fields
            if result:
                print(f"Success:          {result.get('success', 'N/A')}")
                print(f"Route:            {result.get('route', 'N/A')}")
                print(f"Date:             {result.get('date', 'N/A')}")
                print(f"Spawn Type:       {result.get('spawn_type', 'N/A')}")
                print(f"Route Passengers: {result.get('route_passengers', 0)}")
                print(f"Depot Passengers: {result.get('depot_passengers', 0)}")
                print(f"Total Created:    {result.get('total_created', 0)}")
            else:
                print("⚠️  No result returned from server")
                
            if self.connector.is_websocket_connected:
                print(f"Events Received:  {self.event_count}")
            print("=" * 80)
            print()
            
        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            import traceback
            traceback.print_exc()
            # Show more details if it's an HTTP error
            if hasattr(e, 'response'):
                try:
                    error_detail = e.response.json()
                    print(f"   Server error: {error_detail}")
                except:
                    print(f"   Status code: {e.response.status_code}")
                    print(f"   Response: {e.response.text}")

    
    def cmd_stats(self):
        """Show connection statistics"""
        if not self.connector:
            print("Not connected")
            return
        
        print()
        print("=" * 80)
        print("CONNECTION STATISTICS")
        print("=" * 80)
        print(f"Base URL:            {self.base_url}")
        print(f"WebSocket:           {'✅ Connected' if self.connector.is_websocket_connected else '❌ Not connected'}")
        print(f"Events received:     {self.event_count}")
        print("=" * 80)
        print()
    
    def on_passenger_event(self, data):
        """Handle passenger lifecycle events"""
        if not self.streaming:
            self.event_count += 1
            # Only show during seeding (when event_count is being tracked)
    
    async def cmd_list_passengers(self, args):
        """List passengers with filters"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        # Parse filter arguments
        params = {}
        i = 0
        while i < len(args):
            if args[i] == "route" and i + 1 < len(args):
                params["route"] = args[i + 1]
                i += 2
            elif args[i] == "status" and i + 1 < len(args):
                params["status"] = args[i + 1]
                i += 2
            elif args[i] == "vehicle" and i + 1 < len(args):
                params["vehicle_id"] = args[i + 1]
                i += 2
            else:
                i += 1
        
        try:
            response = await self.connector.http_client.get("/api/passengers", params=params)
            response.raise_for_status()
            result = response.json()
            
            passengers = result.get("data", [])
            
            print()
            print("=" * 120)
            print(f"PASSENGERS LIST - Total: {len(passengers)}")
            print("=" * 120)
            print(f"{'ID':<15} {'Status':<12} {'State':<12} {'Route':<8} {'Vehicle':<10} {'Spawned':<20}")
            print("-" * 120)
            
            for p in passengers:
                print(f"{p['passenger_id']:<15} {p['status']:<12} {p['computed_state']:<12} "
                      f"{p.get('route_id', 'N/A')[:8]:<8} {p.get('vehicle_id', 'N/A'):<10} "
                      f"{p['spawned_at'][:19]:<20}")
            
            print("=" * 120)
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_get_passenger(self, passenger_id):
        """Get detailed passenger information"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        try:
            response = await self.connector.http_client.get(f"/api/passengers/{passenger_id}")
            response.raise_for_status()
            p = response.json()
            
            print()
            print("=" * 80)
            print(f"PASSENGER DETAILS - {p['passenger_id']}")
            print("=" * 80)
            print(f"Document ID:      {p['documentId']}")
            print(f"Status:           {p['status']}")
            print(f"Computed State:   {p['computed_state']}")
            print(f"Route:            {p.get('route_id', 'N/A')}")
            print(f"Vehicle:          {p.get('vehicle_id', 'N/A')}")
            print()
            print(f"Location:         ({p['latitude']}, {p['longitude']})")
            print(f"Destination:      ({p['destination_lat']}, {p['destination_lon']})")
            print(f"Dest Name:        {p.get('destination_name', 'N/A')}")
            print()
            print(f"Spawned At:       {p.get('spawned_at', 'N/A')}")
            print(f"Boarded At:       {p.get('boarded_at', 'N/A')}")
            print(f"Alighted At:      {p.get('alighted_at', 'N/A')}")
            print()
            print(f"Created:          {p['createdAt']}")
            print(f"Updated:          {p['updatedAt']}")
            print("=" * 80)
            print()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"❌ Passenger {passenger_id} not found")
            else:
                print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_board(self, passenger_id, vehicle_id):
        """Board a passenger onto a vehicle"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        try:
            response = await self.connector.http_client.patch(
                f"/api/passengers/{passenger_id}/board",
                json={"vehicle_id": vehicle_id}
            )
            response.raise_for_status()
            p = response.json()
            
            print()
            print(f"✅ Passenger {p['passenger_id']} boarded onto {vehicle_id}")
            print(f"   Status: {p['status']} | State: {p['computed_state']}")
            print(f"   Boarded At: {p['boarded_at']}")
            print()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e))
            print(f"❌ Error: {error_detail}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_alight(self, passenger_id):
        """Alight a passenger from vehicle"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        try:
            response = await self.connector.http_client.patch(
                f"/api/passengers/{passenger_id}/alight",
                json={}
            )
            response.raise_for_status()
            p = response.json()
            
            print()
            print(f"✅ Passenger {p['passenger_id']} alighted")
            print(f"   Status: {p['status']} | State: {p['computed_state']}")
            print(f"   Alighted At: {p['alighted_at']}")
            print()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e))
            print(f"❌ Error: {error_detail}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_cancel(self, passenger_id):
        """Cancel a passenger"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        try:
            response = await self.connector.http_client.patch(
                f"/api/passengers/{passenger_id}/cancel"
            )
            response.raise_for_status()
            p = response.json()
            
            print()
            print(f"✅ Passenger {p['passenger_id']} cancelled")
            print(f"   Status: {p['status']} | State: {p['computed_state']}")
            print()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e))
            print(f"❌ Error: {error_detail}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_delete(self, args):
        """
        Delete passengers with flexible filters
        
        Usage:
            delete help                                    - Show detailed help
            delete route=<route>                          - Delete all passengers for a route
            delete route=<route> day=<day>                - Delete for specific day
            delete route=<route> date=<YYYY-MM-DD>        - Delete for specific date
            delete route=<route> status=<status>          - Delete by status
            delete route=<route> hours=<start>-<end>      - Delete for hour range
            delete all                                     - Delete ALL passengers (dangerous!)
        
        Examples:
            delete route=1 day=monday                     - Delete all Monday passengers on route 1
            delete route=1 date=2024-11-04 hours=7-9      - Delete passengers between 7-9 AM
            delete route=1 status=WAITING                 - Delete all waiting passengers
            delete all                                     - Delete everything (requires confirmation)
        """
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        # Show help
        if not args or (len(args) == 1 and args[0] == 'help'):
            print()
            print("="*80)
            print("DELETE COMMAND HELP")
            print("="*80)
            print()
            print("Delete passengers with flexible filtering options:")
            print()
            print("BASIC USAGE:")
            print("  delete route=<route>                  - Delete all passengers for route")
            print("  delete route=<route> day=<day>        - Delete by day (monday-sunday)")
            print("  delete route=<route> date=<date>      - Delete by date (YYYY-MM-DD)")
            print("  delete route=<route> status=<status>  - Delete by status (WAITING, BOARDED, etc.)")
            print()
            print("ADVANCED FILTERS:")
            print("  hours=<start>-<end>                   - Hour range (e.g., hours=7-9)")
            print("  all                                    - Delete ALL passengers (⚠️ DANGEROUS!)")
            print()
            print("EXAMPLES:")
            print("  delete route=1 day=monday             - Delete all Monday route 1 passengers")
            print("  delete route=1 date=2024-11-04        - Delete specific date")
            print("  delete route=1 hours=7-9              - Delete 7 AM - 9 AM passengers")
            print("  delete route=1 status=WAITING         - Delete only waiting passengers")
            print("  delete all                             - Delete everything (⚠️ requires confirmation)")
            print()
            print("="*80)
            return
        
        # Parse arguments
        filters = {}
        delete_all = False
        
        for arg in args:
            if arg.lower() == 'all':
                delete_all = True
                continue
            
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lower().strip()
                value = value.strip()
                
                if key == 'route':
                    filters['route'] = value
                elif key == 'day':
                    filters['day'] = value.lower()
                elif key == 'date':
                    filters['date'] = value
                elif key == 'status':
                    filters['status'] = value.upper()
                elif key == 'hours':
                    if '-' in value:
                        start, end = value.split('-')
                        filters['start_hour'] = int(start)
                        filters['end_hour'] = int(end)
                    else:
                        print(f"❌ Invalid hours format: {value}. Use 'start-end' (e.g., 7-9)")
                        return
                else:
                    print(f"⚠️  Unknown filter: {key}")
        
        # Build description
        if delete_all:
            desc = "ALL PASSENGERS (⚠️ DANGER!)"
        else:
            parts = []
            if 'route' in filters:
                parts.append(f"Route {filters['route']}")
            if 'day' in filters:
                parts.append(f"{filters['day'].capitalize()}")
            if 'date' in filters:
                parts.append(filters['date'])
            if 'status' in filters:
                parts.append(f"status={filters['status']}")
            if 'start_hour' in filters:
                parts.append(f"{filters['start_hour']:02d}:00-{filters['end_hour']:02d}:59")
            
            if not parts:
                print("❌ No filters specified. Use 'delete help' for usage.")
                return
            
            desc = ", ".join(parts)
        
        # Confirm deletion
        print()
        print("="*80)
        print("⚠️  DELETE CONFIRMATION")
        print("="*80)
        print(f"You are about to DELETE passengers matching:")
        print(f"  {desc}")
        print()
        
        # Get count first (dry run)
        try:
            result = await self.connector.delete_passengers(**filters, confirm=False)
            count = result.get('deleted_count', 0)
            print(f"📊 This will delete approximately {count} passengers")
        except Exception as e:
            print(f"⚠️  Could not get count: {e}")
            count = "unknown"
        
        print()
        confirmation = input("Type 'DELETE' (all caps) to confirm: ")
        
        if confirmation != 'DELETE':
            print("❌ Deletion cancelled")
            return
        
        # Execute deletion
        try:
            print()
            print("🗑️  Deleting passengers...")
            
            # Set up WebSocket event handler for delete progress
            if self.connector.is_websocket_connected:
                def on_delete_progress(data):
                    """Handle delete progress events"""
                    deleted = data.get('deleted_so_far', 0)
                    total = data.get('total', 0)
                    percent = data.get('progress_percent', 0)
                    
                    bar_width = int((percent / 100) * 50)
                    bar = "█" * bar_width + "░" * (50 - bar_width)
                    print(f"\r   Progress: [{bar}] {percent:.1f}% ({deleted}/{total})", end='', flush=True)
                
                self.connector.on('delete:progress', on_delete_progress)
            
            result = await self.connector.delete_passengers(**filters, confirm=True)
            deleted = result.get('deleted_count', 0)
            
            # Clear progress line and print newline
            if self.connector.is_websocket_connected:
                print()  # New line after progress bar
            
            print()
            print("="*80)
            print("✅ DELETION COMPLETE")
            print("="*80)
            print(f"Deleted: {deleted} passengers")
            print(f"Message: {result.get('message', 'Success')}")
            print("="*80)
            print()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e))
            print(f"❌ Error: {error_detail}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    async def cmd_monitor_stats(self):
        """Show passenger monitor statistics"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        try:
            response = await self.connector.http_client.get("/api/monitor/stats")
            response.raise_for_status()
            stats = response.json()
            
            print()
            print("=" * 80)
            print("PASSENGER MONITOR STATISTICS")
            print("=" * 80)
            print(f"Running:              {'✅ Yes' if stats.get('running') else '❌ No'}")
            print(f"Monitored Routes:     {stats.get('monitored_routes', 0)}")
            print(f"Cached Passengers:    {stats.get('cached_passengers', 0)}")
            print()
            print(f"State Transitions:    {stats.get('state_transitions', 0)}")
            print(f"External Updates:     {stats.get('external_updates', 0)}")
            print(f"Total Changes:        {stats.get('total_changes_detected', 0)}")
            print()
            print(f"Last Poll:            {stats.get('last_poll', 'N/A')}")
            print("=" * 80)
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    console = CommuterConsole()
    await console.start()


if __name__ == "__main__":
    asyncio.run(main())
