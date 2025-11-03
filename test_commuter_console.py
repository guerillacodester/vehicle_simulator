#!/usr/bin/env python3
"""
Commuter Service Test Console Client

Interactive console client to test real-time streaming and commands.

Usage:
    python test_commuter_console.py
    
    # Commands:
    connect              - Connect to commuter service
    disconnect           - Disconnect from service
    manifest <route>     - Get manifest for route
    barchart <route>     - Get barchart for route
    stream <route>       - Stream real-time events for route
    seed <route> <hrs>   - Watch seeding in real-time
    stats                - Show connection statistics
    help                 - Show this help
    exit                 - Exit console
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from clients.commuter.connector import CommuterConnector, EventType


class CommuterConsole:
    """Interactive console for commuter service testing"""
    
    def __init__(self):
        self.connector: Optional[CommuterConnector] = None
        self.running = False
        self.event_count = 0
        self.hourly_counts = {}
        self.streaming = False
        
    async def start(self):
        """Start the console"""
        print("=" * 80)
        print("COMMUTER SERVICE TEST CONSOLE")
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
            await self.cmd_connect()
        
        elif cmd == "disconnect":
            await self.cmd_disconnect()
        
        elif cmd == "manifest":
            route = args[0] if args else "1"
            day = args[1] if len(args) > 1 else "monday"
            await self.cmd_manifest(route, day)
        
        elif cmd == "barchart":
            route = args[0] if args else "1"
            day = args[1] if len(args) > 1 else "monday"
            await self.cmd_barchart(route, day)
        
        elif cmd == "stream":
            route = args[0] if args else "1"
            await self.cmd_stream(route)
        
        elif cmd == "seed":
            route = args[0] if args else "1"
            hours = args[1] if len(args) > 1 else "7-9"
            await self.cmd_seed(route, hours)
        
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
        print("connect                     - Connect to commuter service")
        print("disconnect                  - Disconnect from service")
        print("manifest <route> [day]      - Get manifest for route (default: route 1, monday)")
        print("barchart <route> [day]      - Get barchart for route")
        print("stream <route>              - Stream real-time events for route")
        print("seed <route> <start-end>    - Watch seeding in real-time (e.g., seed 1 7-9)")
        print("stats                       - Show connection statistics")
        print("help                        - Show this help")
        print("exit                        - Exit console")
        print("=" * 80)
        print()
    
    async def cmd_connect(self):
        """Connect to commuter service"""
        print("Connecting to Commuter Service...")
        
        try:
            self.connector = CommuterConnector(
                base_url="http://localhost:4000",
                socketio_url=None  # Socket.IO optional for now
            )
            
            # Subscribe to events
            self.connector.on('connected', self.on_connected)
            self.connector.on('disconnected', self.on_disconnected)
            self.connector.on('passenger_spawned', self.on_passenger_spawned)
            self.connector.on('passenger_boarded', self.on_passenger_boarded)
            self.connector.on('passenger_alighted', self.on_passenger_alighted)
            
            await self.connector.connect()
            
            print("✅ Connected successfully!")
            print(f"   HTTP API: http://localhost:4000")
            
            if self.connector.is_socketio_connected:
                print(f"   Socket.IO: ✅ Connected")
            else:
                print(f"   Socket.IO: ⚠️ Not available (real-time streaming disabled)")
                print(f"   Note: HTTP queries still work (manifest, barchart)")
            
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
    
    async def cmd_manifest(self, route: str, day: str):
        """Get manifest for route"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        print(f"Fetching manifest for Route {route}, {day.title()}...")
        
        try:
            manifest = await self.connector.get_manifest(route=route, day=day)
            passengers = manifest.get('passengers', [])
            total = manifest.get('total', 0)
            
            print()
            print("=" * 80)
            print(f"MANIFEST - Route {route} - {day.title()}")
            print("=" * 80)
            print(f"Total Passengers: {total}")
            print()
            
            if passengers:
                print("First 10 passengers:")
                for i, p in enumerate(passengers[:10], 1):
                    spawn_time = p.get('spawn_time', 'N/A')
                    if spawn_time != 'N/A':
                        dt = datetime.fromisoformat(spawn_time.replace('Z', '+00:00'))
                        spawn_time = dt.strftime('%H:%M')
                    print(f"  {i:>2}. {p.get('passenger_id', 'N/A')[:8]}... | {spawn_time} | Status: {p.get('status', 'N/A')}")
            
            print("=" * 80)
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_barchart(self, route: str, day: str):
        """Get barchart for route"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        print(f"Fetching barchart for Route {route}, {day.title()}...")
        
        try:
            data = await self.connector.get_barchart(route=route, day=day)
            hours = data.get('hours', [])
            counts = data.get('counts', [])
            total = data.get('total', 0)
            peak_hour = data.get('peak_hour', 0)
            
            print()
            print("=" * 80)
            print(f"BARCHART - Route {route} - {day.title()}")
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
        
        if not self.connector.is_socketio_connected:
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
    
    async def cmd_seed(self, route: str, hours: str):
        """Watch seeding in real-time"""
        if not self.connector:
            print("❌ Not connected. Use 'connect' first.")
            return
        
        if not self.connector.is_socketio_connected:
            print("❌ Socket.IO not connected. Real-time streaming unavailable.")
            return
        
        # Parse hours (e.g., "7-9")
        try:
            start_hour, end_hour = map(int, hours.split('-'))
        except:
            print("❌ Invalid hours format. Use: seed <route> <start-end> (e.g., seed 1 7-9)")
            return
        
        print()
        print("=" * 80)
        print(f"🔴 WATCHING SEEDING - Route {route} - Hours {start_hour}:00 to {end_hour}:00")
        print("=" * 80)
        print()
        print("Now run seeding in another terminal:")
        print(f"  python commuter_service/seed.py --day monday --route {route} \\")
        print(f"    --type route --start-hour {start_hour} --end-hour {end_hour}")
        print()
        print("Press Ctrl+C to stop watching")
        print()
        
        self.streaming = True
        self.event_count = 0
        self.hourly_counts = {}
        
        try:
            async for event in self.connector.stream_events(route=route, event_types=[EventType.SPAWNED]):
                if not self.streaming:
                    break
                
                self.event_count += 1
                hour = event.timestamp.hour
                self.hourly_counts[hour] = self.hourly_counts.get(hour, 0) + 1
                
                print(f"🚶 #{self.event_count:>4} | Hour {hour:>2}:00 | This hour: {self.hourly_counts[hour]:>3} | Total: {self.event_count:>3}")
        
        except KeyboardInterrupt:
            print("\n⏹️  Stopped watching")
            self.streaming = False
            
            # Show summary
            print()
            print("=" * 80)
            print("SEEDING SUMMARY")
            print("=" * 80)
            print(f"Total passengers spawned: {self.event_count}")
            print()
            print("Hourly breakdown:")
            for hour in sorted(self.hourly_counts.keys()):
                count = self.hourly_counts[hour]
                bar = "█" * (count // 2)
                print(f"  {hour:>2}:00 │ {bar:<30} {count:>3}")
            print("=" * 80)
            print()
    
    def cmd_stats(self):
        """Show connection statistics"""
        if not self.connector:
            print("Not connected")
            return
        
        print()
        print("=" * 80)
        print("CONNECTION STATISTICS")
        print("=" * 80)
        print(f"Connected:           {'✅ Yes' if self.connector.is_connected else '❌ No'}")
        print(f"Socket.IO:           {'✅ Connected' if self.connector.is_socketio_connected else '❌ Not connected'}")
        print(f"Events received:     {self.event_count}")
        print(f"Buffered events:     {len(self.connector.get_buffered_events())}")
        print("=" * 80)
        print()
    
    def on_connected(self, data):
        """Handle connected event"""
        if not self.streaming:
            print("✅ Socket.IO connected")
    
    def on_disconnected(self, data):
        """Handle disconnected event"""
        if not self.streaming:
            print("⚠️ Socket.IO disconnected")
    
    def on_passenger_spawned(self, event):
        """Handle passenger spawned event"""
        # Only show if not in streaming mode
        pass
    
    def on_passenger_boarded(self, event):
        """Handle passenger boarded event"""
        pass
    
    def on_passenger_alighted(self, event):
        """Handle passenger alighted event"""
        pass


async def main():
    console = CommuterConsole()
    await console.start()


if __name__ == "__main__":
    asyncio.run(main())
