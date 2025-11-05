"""
Fleet Management Console
=========================

Interactive CLI for managing the ArkNet transit fleet.

Features:
- Real-time vehicle status display
- Engine control (start/stop)
- Boarding control (enable/disable/trigger)
- Live event streaming
- Color-coded output
- Tab completion

Usage:
    python -m clients.fleet.fleet_console
    
    # Or with custom API URL:
    python -m clients.fleet.fleet_console --url http://localhost:5001

Commands:
    status              - Show API health and connection status
    vehicles            - List all vehicles with current state
    vehicle <id>        - Show detailed state for specific vehicle
    conductors          - List all conductors
    conductor <id>      - Show conductor for specific vehicle
    start <id>          - Start engine for vehicle
    stop <id>           - Stop engine for vehicle
    enable <id>         - Enable boarding for vehicle
    disable <id>        - Disable boarding for vehicle
    trigger <id>        - Trigger manual boarding check
    stream              - Start live event streaming
    help                - Show this help message
    exit                - Exit console
"""

import asyncio
import argparse
import logging
from typing import Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.layout import Layout
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Install 'rich' for better output: pip install rich")

from .connector import FleetConnector
from .models import VehicleState, ConductorState


logger = logging.getLogger(__name__)


class FleetConsole:
    """Interactive console for fleet management"""
    
    def __init__(self, api_url: str = "http://localhost:5001"):
        """
        Initialize console
        
        Args:
            api_url: Fleet Management API base URL
        """
        self.api_url = api_url
        self.connector = FleetConnector(base_url=api_url)
        self.console = Console() if RICH_AVAILABLE else None
        self.streaming = False
        self.event_count = 0
        
    def print(self, *args, **kwargs):
        """Print with or without Rich"""
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)
    
    # ========================================================================
    # COMMANDS
    # ========================================================================
    
    async def cmd_status(self):
        """Show API health and connection status"""
        try:
            health = await self.connector.get_health()
            ws_status = await self.connector.get_websocket_status()
            
            if self.console:
                # Rich formatted output
                table = Table(title="🚌 Fleet Management System Status", box=box.ROUNDED)
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("API Status", health.status)
                table.add_row("Timestamp", health.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                table.add_row("Simulator Running", "✅ Yes" if health.simulator_running else "❌ No")
                table.add_row("Active Vehicles", str(health.active_vehicles))
                table.add_row("Event Bus Subscribers", str(health.event_bus_stats.get("subscribers", 0)))
                table.add_row("Events Emitted", str(health.event_bus_stats.get("total_events_emitted", 0)))
                table.add_row("WebSocket Connections", str(ws_status.get("active_connections", 0)))
                
                self.console.print(table)
            else:
                # Plain text output
                print("\n" + "="*60)
                print("🚌 FLEET MANAGEMENT SYSTEM STATUS")
                print("="*60)
                print(f"API Status:         {health.status}")
                print(f"Timestamp:          {health.timestamp}")
                print(f"Simulator Running:  {'Yes' if health.simulator_running else 'No'}")
                print(f"Active Vehicles:    {health.active_vehicles}")
                print(f"Event Subscribers:  {health.event_bus_stats.get('subscribers', 0)}")
                print(f"Events Emitted:     {health.event_bus_stats.get('total_events_emitted', 0)}")
                print(f"WS Connections:     {ws_status.get('active_connections', 0)}")
                print("="*60 + "\n")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to get status: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_vehicles(self):
        """List all vehicles"""
        try:
            vehicles = await self.connector.get_vehicles()
            
            if not vehicles:
                self.print("[yellow]No vehicles found[/yellow]" if self.console else "No vehicles found")
                return
            
            if self.console:
                # Rich table
                table = Table(title=f"🚗 Fleet Vehicles ({len(vehicles)})", box=box.ROUNDED)
                table.add_column("Vehicle ID", style="cyan", no_wrap=True)
                table.add_column("Driver", style="white")
                table.add_column("Route", style="blue")
                table.add_column("Position", style="magenta")
                table.add_column("State", style="yellow")
                table.add_column("Engine", style="green")
                table.add_column("GPS", style="green")
                table.add_column("Passengers", style="white")
                table.add_column("Boarding", style="yellow")
                
                for v in vehicles:
                    position = f"{v.current_position.latitude:.4f}, {v.current_position.longitude:.4f}" if v.current_position else "N/A"
                    engine = "🟢 ON" if v.engine_running else "🔴 OFF"
                    gps = "🟢 ON" if v.gps_running else "🔴 OFF"
                    boarding = "✅ Active" if v.boarding_active else "⏸️  Inactive"
                    passengers = f"{v.passenger_count}/{v.capacity}"
                    
                    table.add_row(
                        v.vehicle_id,
                        v.driver_name or "N/A",
                        str(v.route_id) if v.route_id else "N/A",
                        position,
                        v.driver_state or "N/A",
                        engine,
                        gps,
                        passengers,
                        boarding
                    )
                
                self.console.print(table)
            else:
                # Plain text
                print("\n" + "="*100)
                print(f"🚗 FLEET VEHICLES ({len(vehicles)})")
                print("="*100)
                print(f"{'ID':<10} {'Driver':<20} {'Route':<6} {'State':<15} {'Engine':<8} {'GPS':<8} {'Passengers':<12} {'Boarding':<10}")
                print("-"*100)
                for v in vehicles:
                    engine = "ON" if v.engine_running else "OFF"
                    gps = "ON" if v.gps_running else "OFF"
                    boarding = "Active" if v.boarding_active else "Inactive"
                    passengers = f"{v.passenger_count}/{v.capacity}"
                    
                    print(f"{v.vehicle_id:<10} {(v.driver_name or 'N/A'):<20} {(str(v.route_id) if v.route_id else 'N/A'):<6} {(v.driver_state or 'N/A'):<15} {engine:<8} {gps:<8} {passengers:<12} {boarding:<10}")
                print("="*100 + "\n")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to get vehicles: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_vehicle(self, vehicle_id: str):
        """Show detailed vehicle state"""
        try:
            vehicle = await self.connector.get_vehicle(vehicle_id)
            
            if self.console:
                # Rich panel
                details = f"""
[cyan]Vehicle ID:[/cyan] {vehicle.vehicle_id}
[cyan]Driver:[/cyan] {vehicle.driver_name or 'N/A'}
[cyan]Route:[/cyan] {vehicle.route_id if vehicle.route_id else 'N/A'}
[cyan]State:[/cyan] {vehicle.driver_state or 'N/A'}

[yellow]Position:[/yellow]
  Latitude:  {vehicle.current_position.latitude if vehicle.current_position else 'N/A'}
  Longitude: {vehicle.current_position.longitude if vehicle.current_position else 'N/A'}

[green]Devices:[/green]
  Engine: {'🟢 RUNNING' if vehicle.engine_running else '🔴 STOPPED'}
  GPS:    {'🟢 ACTIVE' if vehicle.gps_running else '🔴 OFFLINE'}

[blue]Passengers:[/blue]
  On Board: {vehicle.passenger_count}/{vehicle.capacity}
  Boarding: {'✅ ENABLED' if vehicle.boarding_active else '⏸️  DISABLED'}
                """.strip()
                
                self.console.print(Panel(details, title=f"🚗 Vehicle: {vehicle_id}", border_style="cyan"))
            else:
                print("\n" + "="*60)
                print(f"🚗 VEHICLE: {vehicle_id}")
                print("="*60)
                print(f"Driver:       {vehicle.driver_name or 'N/A'}")
                print(f"Route:        {vehicle.route_id if vehicle.route_id else 'N/A'}")
                print(f"State:        {vehicle.driver_state or 'N/A'}")
                print(f"Position:     {vehicle.current_position.latitude if vehicle.current_position else 'N/A'}, {vehicle.current_position.longitude if vehicle.current_position else 'N/A'}")
                print(f"Engine:       {'ON' if vehicle.engine_running else 'OFF'}")
                print(f"GPS:          {'ON' if vehicle.gps_running else 'OFF'}")
                print(f"Passengers:   {vehicle.passenger_count}/{vehicle.capacity}")
                print(f"Boarding:     {'ENABLED' if vehicle.boarding_active else 'DISABLED'}")
                print("="*60 + "\n")
                
        except Exception as e:
            self.print(f"[red]❌ Vehicle not found: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_conductors(self):
        """List all conductors"""
        try:
            conductors = await self.connector.get_conductors()
            
            if not conductors:
                self.print("[yellow]No conductors found[/yellow]" if self.console else "No conductors found")
                return
            
            if self.console:
                table = Table(title=f"👔 Conductors ({len(conductors)})", box=box.ROUNDED)
                table.add_column("Vehicle ID", style="cyan")
                table.add_column("Conductor", style="white")
                table.add_column("State", style="yellow")
                table.add_column("Passengers", style="white")
                table.add_column("Boarding", style="green")
                table.add_column("Depot Boarding", style="blue")
                
                for c in conductors:
                    boarding = "✅ Active" if c.boarding_active else "⏸️  Inactive"
                    depot = "✅ Active" if c.depot_boarding_active else "⏸️  Inactive"
                    passengers = f"{c.passengers_on_board}/{c.capacity}"
                    
                    table.add_row(
                        c.vehicle_id,
                        c.conductor_name or "N/A",
                        c.conductor_state or "N/A",
                        passengers,
                        boarding,
                        depot
                    )
                
                self.console.print(table)
            else:
                print("\n" + "="*90)
                print(f"👔 CONDUCTORS ({len(conductors)})")
                print("="*90)
                print(f"{'Vehicle':<10} {'Conductor':<20} {'State':<15} {'Passengers':<12} {'Boarding':<12} {'Depot':<10}")
                print("-"*90)
                for c in conductors:
                    boarding = "Active" if c.boarding_active else "Inactive"
                    depot = "Active" if c.depot_boarding_active else "Inactive"
                    passengers = f"{c.passengers_on_board}/{c.capacity}"
                    
                    print(f"{c.vehicle_id:<10} {(c.conductor_name or 'N/A'):<20} {(c.conductor_state or 'N/A'):<15} {passengers:<12} {boarding:<12} {depot:<10}")
                print("="*90 + "\n")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to get conductors: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_start(self, vehicle_id: str):
        """Start vehicle engine"""
        try:
            result = await self.connector.start_engine(vehicle_id)
            
            if result.success:
                self.print(f"[green]✅ {result.message}[/green]" if self.console else f"✅ {result.message}")
            else:
                self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to start engine: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_stop(self, vehicle_id: str):
        """Stop vehicle engine"""
        try:
            result = await self.connector.stop_engine(vehicle_id)
            
            if result.success:
                self.print(f"[green]✅ {result.message}[/green]" if self.console else f"✅ {result.message}")
            else:
                self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to stop engine: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_enable(self, vehicle_id: str):
        """Enable boarding"""
        try:
            result = await self.connector.enable_boarding(vehicle_id)
            
            if result.success:
                self.print(f"[green]✅ {result.message}[/green]" if self.console else f"✅ {result.message}")
            else:
                self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to enable boarding: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_disable(self, vehicle_id: str):
        """Disable boarding"""
        try:
            result = await self.connector.disable_boarding(vehicle_id)
            
            if result.success:
                self.print(f"[green]✅ {result.message}[/green]" if self.console else f"✅ {result.message}")
            else:
                self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to disable boarding: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_trigger(self, vehicle_id: str):
        """Trigger manual boarding"""
        try:
            result = await self.connector.trigger_boarding(vehicle_id)
            
            if result.success:
                boarded = result.data.get("passengers_boarded", 0) if result.data else 0
                self.print(f"[green]✅ {result.message} - Boarded: {boarded} passengers[/green]" if self.console else f"✅ {result.message} - Boarded: {boarded}")
            else:
                self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to trigger boarding: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_stream(self):
        """Start live event streaming"""
        self.print("[cyan]📡 Starting event stream... (Ctrl+C to stop)[/cyan]" if self.console else "📡 Starting event stream...")
        
        # Subscribe to all events
        def on_event(data):
            event_type = data.get("event_type", "unknown")
            vehicle_id = data.get("vehicle_id", "N/A")
            timestamp = data.get("timestamp", "N/A")
            
            self.event_count += 1
            
            if self.console:
                color = "green" if "started" in event_type or "enabled" in event_type else "yellow"
                self.console.print(f"[{color}]#{self.event_count} [{timestamp}] {event_type} - {vehicle_id}[/{color}]")
            else:
                print(f"#{self.event_count} [{timestamp}] {event_type} - {vehicle_id}")
        
        # Subscribe to common event types
        for event_type in ["engine_started", "engine_stopped", "position_update", "passenger_boarded", "passenger_alighted", "boarding_enabled", "boarding_disabled"]:
            self.connector.on(event_type, on_event)
        
        # Connect WebSocket
        await self.connector.connect_websocket()
        
        # Wait for Ctrl+C
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.print("\n[yellow]⏸️  Stream stopped[/yellow]" if self.console else "\n⏸️  Stream stopped")
            await self.connector.disconnect_websocket()
    
    async def cmd_sim_status(self):
        """Show simulator status"""
        try:
            status = await self.connector.get_sim_status()
            
            if self.console:
                details = f"""
[cyan]Running:[/cyan] {'✅ Yes' if status['running'] else '❌ No'}
[cyan]Simulation Time:[/cyan] {status.get('sim_time', 'Not set')}
[cyan]Active Vehicles:[/cyan] {status['active_vehicles']}
[cyan]Idle Vehicles:[/cyan] {status['idle_vehicles']}
                """.strip()
                
                self.console.print(Panel(details, title="🎮 Simulator Status", border_style="cyan"))
            else:
                print("\n" + "="*60)
                print("🎮 SIMULATOR STATUS")
                print("="*60)
                print(f"Running:         {'Yes' if status['running'] else 'No'}")
                print(f"Simulation Time: {status.get('sim_time', 'Not set')}")
                print(f"Active Vehicles: {status['active_vehicles']}")
                print(f"Idle Vehicles:   {status['idle_vehicles']}")
                print("="*60 + "\n")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to get simulator status: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_pause(self):
        """Pause simulator"""
        try:
            result = await self.connector.pause_sim()
            
            if result.success:
                self.print(f"[yellow]⏸️  {result.message}[/yellow]" if self.console else f"⏸️  {result.message}")
            else:
                self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to pause: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_resume(self):
        """Resume simulator"""
        try:
            result = await self.connector.resume_sim()
            
            if result.success:
                self.print(f"[green]▶️  {result.message}[/green]" if self.console else f"▶️  {result.message}")
            else:
                self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to resume: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_stop_sim(self):
        """Stop simulator"""
        try:
            result = await self.connector.stop_sim()
            
            if result.success:
                self.print(f"[red]⏹️  {result.message}[/red]" if self.console else f"⏹️  {result.message}")
            else:
                self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to stop: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_set_time(self, time_str: str):
        """Set simulation time"""
        try:
            # Parse time string (ISO format or HH:MM)
            from dateutil import parser as date_parser
            try:
                sim_time = date_parser.parse(time_str)
            except:
                # Try HH:MM format
                from datetime import datetime
                now = datetime.now()
                parts = time_str.split(":")
                if len(parts) == 2:
                    hour, minute = int(parts[0]), int(parts[1])
                    sim_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    raise ValueError("Invalid time format. Use ISO (2025-11-05T14:30:00) or HH:MM")
            
            result = await self.connector.set_sim_time(sim_time)
            
            if result.success:
                self.print(f"[green]🕐 {result.message}[/green]" if self.console else f"🕐 {result.message}")
            else:
                self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to set time: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_stream(self):
        """Start live event streaming"""
        self.print("[cyan]📡 Starting event stream... (Ctrl+C to stop)[/cyan]" if self.console else "📡 Starting event stream...")
        
        # Subscribe to all events
        def on_event(data):
            event_type = data.get("event_type", "unknown")
            vehicle_id = data.get("vehicle_id", "N/A")
            timestamp = data.get("timestamp", "N/A")
            
            self.event_count += 1
            
            if self.console:
                color = "green" if "started" in event_type or "enabled" in event_type else "yellow"
                self.console.print(f"[{color}]#{self.event_count} [{timestamp}] {event_type} - {vehicle_id}[/{color}]")
            else:
                print(f"#{self.event_count} [{timestamp}] {event_type} - {vehicle_id}")
        
        # Subscribe to common event types
        for event_type in ["engine_started", "engine_stopped", "position_update", "passenger_boarded", "passenger_alighted", "boarding_enabled", "boarding_disabled"]:
            self.connector.on(event_type, on_event)
        
        # Connect WebSocket
        await self.connector.connect_websocket()
        
        # Wait for Ctrl+C
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.print("\n[yellow]⏸️  Stream stopped[/yellow]" if self.console else "\n⏸️  Stream stopped")
            await self.connector.disconnect_websocket()
    
    def cmd_help(self):
        """Show help message"""
        help_text = """
🚌 FLEET MANAGEMENT CONSOLE - COMMANDS

STATUS & MONITORING:
  status              - Show API health and connection status
  sim                 - Show simulator status (running, time, vehicles)
  vehicles            - List all vehicles with current state
  vehicle <id>        - Show detailed state for specific vehicle
  conductors          - List all conductors
  conductor <id>      - Show conductor for specific vehicle

SIMULATOR CONTROL:
  pause               - Pause the simulator
  resume              - Resume the simulator
  stop-sim            - Stop the simulator (shutdown)
  set-time <time>     - Set simulation time (ISO or HH:MM format)

ENGINE CONTROL:
  start <id>          - Start engine for vehicle
  stop <id>           - Stop engine for vehicle

BOARDING CONTROL:
  enable <id>         - Enable boarding for vehicle
  disable <id>        - Disable boarding for vehicle
  trigger <id>        - Trigger manual boarding check

REAL-TIME:
  stream              - Start live event streaming (Ctrl+C to stop)

GENERAL:
  help                - Show this help message
  exit / quit         - Exit console

EXAMPLES:
  sim                       # Show simulator status
  pause                     # Pause simulation
  set-time 14:30            # Set time to 2:30 PM
  set-time 2025-11-05T14:30 # Set specific date/time
  vehicles                  # List all vehicles
  vehicle ZR102             # Show details for ZR102
  start ZR102               # Start engine
  enable ZR102              # Enable boarding
  trigger ZR102             # Manually trigger boarding
  stream                    # Watch live events
        """.strip()
        
        self.print(help_text)
    
    # ========================================================================
    # REPL
    # ========================================================================
    
    async def run(self):
        """Run interactive console"""
        # Show banner
        if self.console:
            banner = Panel(
                "[bold cyan]ArkNet Fleet Management Console[/bold cyan]\n"
                f"[white]Connected to: {self.api_url}[/white]\n"
                "[dim]Type 'help' for commands, 'exit' to quit[/dim]",
                border_style="blue",
                box=box.DOUBLE
            )
            self.console.print(banner)
        else:
            print("\n" + "="*60)
            print("🚌 ARKNET FLEET MANAGEMENT CONSOLE")
            print(f"Connected to: {self.api_url}")
            print("Type 'help' for commands, 'exit' to quit")
            print("="*60 + "\n")
        
        # Check connection
        try:
            await self.connector.get_health()
            self.print("[green]✅ Connected to Fleet API[/green]" if self.console else "✅ Connected")
        except Exception as e:
            self.print(f"[red]❌ Failed to connect: {e}[/red]" if self.console else f"❌ Error: {e}")
            self.print("[yellow]Make sure the simulator is running with --mode depot[/yellow]" if self.console else "Make sure simulator is running")
            return
        
        # REPL loop
        while True:
            try:
                # Get command
                if self.console:
                    command = self.console.input("\n[bold cyan]fleet>[/bold cyan] ").strip()
                else:
                    command = input("\nfleet> ").strip()
                
                if not command:
                    continue
                
                # Parse command
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                # Execute command
                if cmd in ["exit", "quit", "q"]:
                    break
                elif cmd == "status":
                    await self.cmd_status()
                elif cmd == "sim":
                    await self.cmd_sim_status()
                elif cmd == "pause":
                    await self.cmd_pause()
                elif cmd == "resume":
                    await self.cmd_resume()
                elif cmd == "stop-sim":
                    await self.cmd_stop_sim()
                elif cmd == "set-time":
                    if not args:
                        self.print("[red]Usage: set-time <time> (ISO or HH:MM)[/red]" if self.console else "Usage: set-time <time>")
                    else:
                        await self.cmd_set_time(args)
                elif cmd == "vehicles":
                    await self.cmd_vehicles()
                elif cmd == "vehicle":
                    if not args:
                        self.print("[red]Usage: vehicle <vehicle_id>[/red]" if self.console else "Usage: vehicle <vehicle_id>")
                    else:
                        await self.cmd_vehicle(args)
                elif cmd == "conductors":
                    await self.cmd_conductors()
                elif cmd == "conductor":
                    if not args:
                        self.print("[red]Usage: conductor <vehicle_id>[/red]" if self.console else "Usage: conductor <vehicle_id>")
                    else:
                        await self.cmd_vehicle(args)  # Same as vehicle for now
                elif cmd == "start":
                    if not args:
                        self.print("[red]Usage: start <vehicle_id>[/red]" if self.console else "Usage: start <vehicle_id>")
                    else:
                        await self.cmd_start(args)
                elif cmd == "stop":
                    if not args:
                        self.print("[red]Usage: stop <vehicle_id>[/red]" if self.console else "Usage: stop <vehicle_id>")
                    else:
                        await self.cmd_stop(args)
                elif cmd == "enable":
                    if not args:
                        self.print("[red]Usage: enable <vehicle_id>[/red]" if self.console else "Usage: enable <vehicle_id>")
                    else:
                        await self.cmd_enable(args)
                elif cmd == "disable":
                    if not args:
                        self.print("[red]Usage: disable <vehicle_id>[/red]" if self.console else "Usage: disable <vehicle_id>")
                    else:
                        await self.cmd_disable(args)
                elif cmd == "trigger":
                    if not args:
                        self.print("[red]Usage: trigger <vehicle_id>[/red]" if self.console else "Usage: trigger <vehicle_id>")
                    else:
                        await self.cmd_trigger(args)
                elif cmd == "stream":
                    await self.cmd_stream()
                elif cmd == "help":
                    self.cmd_help()
                else:
                    self.print(f"[red]Unknown command: {cmd}. Type 'help' for available commands.[/red]" if self.console else f"Unknown command: {cmd}")
                
            except KeyboardInterrupt:
                self.print("\n[yellow]Use 'exit' to quit[/yellow]" if self.console else "\nUse 'exit' to quit")
            except Exception as e:
                self.print(f"[red]Error: {e}[/red]" if self.console else f"Error: {e}")
                logger.exception("Command error")
        
        # Cleanup
        await self.connector.close()
        self.print("[cyan]👋 Goodbye![/cyan]" if self.console else "👋 Goodbye!")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Fleet Management Console")
    parser.add_argument("--url", default="http://localhost:5001", help="Fleet API URL")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    # Run console
    console = FleetConsole(api_url=args.url)
    await console.run()


if __name__ == "__main__":
    asyncio.run(main())
