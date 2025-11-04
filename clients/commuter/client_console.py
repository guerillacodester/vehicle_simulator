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
sys.path.insert(0, str(Path(__file__).parent.parent))

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
            await self.cmd_manifest(route, date)
        
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
        print("  manifest <route> <date>     - Get manifest table (e.g., manifest 1 2024-11-04)")
        print("  json <route> <date>         - Get raw JSON manifest data")
        print("  barchart <route> <date>     - Get barchart for route")
        print("  list [filters]              - List passengers (see 'list help' for filters)")
        print("  get <passenger_id>          - Get single passenger details")
        print()
        print("PASSENGER MANAGEMENT:")
        print("  board <id> <vehicle_id>     - Board passenger onto vehicle")
        print("  alight <id>                 - Alight passenger from vehicle")
        print("  cancel <id>                 - Cancel passenger")
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
    
    async def cmd_manifest(self, route: str, date: Optional[str] = None):
        """Get manifest for route - displays all passengers in table format"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        date_str = f" on {date}" if date else " (all dates)"
        print(f"Fetching manifest for Route {route}{date_str}...")
        
        try:
            # Fetch ALL passengers (limit=1000)
            manifest = await self.connector.get_manifest(route=route, date=date, limit=1000)
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
            data = await self.connector.get_barchart(route=route, date=date)
            hours = data.get('hours', [])
            counts = data.get('counts', [])
            total = data.get('total', 0)
            peak_hour = data.get('peak_hour', 0)
            
            print()
            print("=" * 80)
            print(f"BARCHART - Route {route}{date_str}")
            print("=" * 80)
            print(f"Total: {total} | Peak Hour: {peak_hour}:00")
            print("=" * 80)
            
            max_count = max(counts) if counts else 1
            for hour, count in zip(hours, counts):
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
            print("📡 Subscribing to real-time events...")
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
            print(f"Success:          {result['success']}")
            print(f"Route:            {result['route']}")
            print(f"Date:             {result['date']}")
            print(f"Spawn Type:       {result['spawn_type']}")
            print(f"Route Passengers: {result['route_passengers']}")
            print(f"Depot Passengers: {result['depot_passengers']}")
            print(f"Total Created:    {result['total_created']}")
            if self.connector.is_websocket_connected:
                print(f"Events Received:  {self.event_count}")
            print("=" * 80)
            print()
            
        except Exception as e:
            print(f"❌ Seeding failed: {e}")
    
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
