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
    python -m clients.fleet.fleet_console --url http://localhost:6000

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
    
    async def cmd_services(self):
        """Show all services status"""
        try:
            response = await self.connector.get_all_services_status()
            
            # Extract services dict from response (may be nested)
            services = response.get('services', response) if isinstance(response, dict) and 'services' in response else response
            summary = response.get('summary', {}) if isinstance(response, dict) else {}
            
            if self.console:
                table = Table(title="🔧 Services Status", box=box.ROUNDED)
                table.add_column("Service", style="cyan")
                table.add_column("Status", style="white")
                table.add_column("PID", style="yellow")
                table.add_column("Uptime", style="green")
                table.add_column("Details", style="white")
                
                for service_name, service_data in services.items():
                    status_str = service_data.get('status', 'unknown')
                    pid = str(service_data.get('pid', 'N/A'))
                    uptime = service_data.get('uptime')
                    uptime_str = f"{int(uptime)}s" if uptime else "N/A"
                    details = service_data.get('error', '')
                    
                    status_emoji = {
                        'running': '🟢',
                        'stopped': '🔴',
                        'starting': '🟡',
                        'stopping': '🟡',
                        'error': '❌'
                    }.get(status_str, '⚪')
                    
                    table.add_row(
                        service_name,
                        f"{status_emoji} {status_str}",
                        pid,
                        uptime_str,
                        details
                    )
                
                if summary:
                    table.add_row("", "", "", "", "")
                    table.add_row("[bold]Summary[/bold]", f"Running: {summary.get('running', 0)}", f"Stopped: {summary.get('stopped', 0)}", f"Error: {summary.get('error', 0)}", "")
                
                self.console.print(table)
            else:
                print("\n" + "="*80)
                print("🔧 SERVICES STATUS")
                print("="*80)
                for service_name, service_data in services.items():
                    print(f"\n{service_name}:")
                    print(f"  Status:  {service_data.get('status', 'unknown')}")
                    print(f"  PID:     {service_data.get('pid', 'N/A')}")
                    print(f"  Uptime:  {service_data.get('uptime', 'N/A')}s")
                    if service_data.get('error'):
                        print(f"  Error:   {service_data['error']}")
                
                if summary:
                    print(f"\n{'='*80}")
                    print(f"Running: {summary.get('running', 0)}, Stopped: {summary.get('stopped', 0)}, Error: {summary.get('error', 0)}")
                print("="*80 + "\n")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to get services status: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_start_service(self, service_name: str, args_str: str = ""):
        """Start a service"""
        try:
            if service_name == "all":
                # Start all services
                kwargs = {}
                if args_str and "data_api_url=" in args_str:
                    for part in args_str.split():
                        if '=' in part:
                            key, value = part.split('=', 1)
                            if key == "data_api_url":
                                kwargs["data_api_url"] = value
                
                result = await self.connector.start_all_services(**kwargs)
                
                if result.success:
                    self.print(f"[green]✅ {result.message}[/green]" if self.console else f"✅ {result.message}")
                    # Show results for each service
                    if result.data and "services" in result.data:
                        for svc_name, svc_result in result.data["services"].items():
                            status = "✅" if svc_result.get("success") else "❌"
                            self.print(f"   {status} {svc_name}: {svc_result.get('message', 'N/A')}")
                else:
                    self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
                    if result.data and "services" in result.data:
                        for svc_name, svc_result in result.data["services"].items():
                            status = "✅" if svc_result.get("success") else "❌"
                            self.print(f"   {status} {svc_name}: {svc_result.get('message', 'N/A')}")
            
            elif service_name == "simulator":
                # Parse optional arguments
                kwargs = {}
                if args_str:
                    # Simple parsing: key=value key=value
                    for part in args_str.split():
                        if '=' in part:
                            key, value = part.split('=', 1)
                            if key == "api_port":
                                kwargs["api_port"] = int(value)
                            elif key == "sim_time":
                                kwargs["sim_time"] = value
                            elif key == "enable_boarding_after":
                                kwargs["enable_boarding_after"] = float(value)
                            elif key == "data_api_url":
                                kwargs["data_api_url"] = value
                
                result = await self.connector.start_service("simulator", **kwargs)
                
                if result.success:
                    self.print(f"[green]✅ {result.message}[/green]" if self.console else f"✅ {result.message}")
                    if result.data and result.data.get('pid'):
                        self.print(f"   PID: {result.data['pid']}")
                    if result.data and result.data.get('api_url'):
                        self.print(f"   API: {result.data['api_url']}")
                else:
                    self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
            
            elif service_name in ["gpscentcom", "commuter_service", "geospatial"]:
                # Generic service start
                result = await self.connector.start_service(service_name)
                
                if result.success:
                    self.print(f"[green]✅ {result.message}[/green]" if self.console else f"✅ {result.message}")
                    if result.data and result.data.get('pid'):
                        self.print(f"   PID: {result.data['pid']}")
                else:
                    self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
            
            else:
                services = "all, simulator, gpscentcom, commuter_service, geospatial"
                self.print(f"[red]Unknown service: {service_name}. Available: {services}[/red]" if self.console else f"Unknown service: {service_name}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to start service: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_stop_service(self, service_name: str):
        """Stop a service"""
        try:
            if service_name == "all":
                # Stop all services
                result = await self.connector.stop_all_services()
                
                if result.success:
                    self.print(f"[yellow]⏹️  {result.message}[/yellow]" if self.console else f"⏹️  {result.message}")
                    if result.data and "services" in result.data:
                        for svc_name, svc_result in result.data["services"].items():
                            status = "✅" if svc_result.get("success") else "❌"
                            self.print(f"   {status} {svc_name}: {svc_result.get('message', 'N/A')}")
                else:
                    self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
            
            elif service_name in ["simulator", "gpscentcom", "commuter_service", "geospatial"]:
                result = await self.connector.stop_service(service_name)
                
                if result.success:
                    self.print(f"[yellow]⏹️  {result.message}[/yellow]" if self.console else f"⏹️  {result.message}")
                else:
                    self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
            
            else:
                services = "all, simulator, gpscentcom, commuter_service, geospatial"
                self.print(f"[red]Unknown service: {service_name}. Available: {services}[/red]" if self.console else f"Unknown service: {service_name}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to stop service: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_restart_service(self, service_name: str):
        """Restart a service"""
        try:
            if service_name in ["simulator", "gpscentcom", "commuter_service", "geospatial"]:
                result = await self.connector.restart_service(service_name)
                
                if result.success:
                    self.print(f"[green]🔄 {result.message}[/green]" if self.console else f"🔄 {result.message}")
                else:
                    self.print(f"[red]❌ {result.message}[/red]" if self.console else f"❌ {result.message}")
            
            else:
                services = "simulator, gpscentcom, commuter_service, geospatial"
                self.print(f"[red]Unknown service: {service_name}. Available: {services}[/red]" if self.console else f"Unknown service: {service_name}")
                
        except Exception as e:
            self.print(f"[red]❌ Failed to restart service: {e}[/red]" if self.console else f"❌ Error: {e}")
    
    async def cmd_dashboard(self, vehicle_id: str = None):
        """Live vehicle telemetry dashboard (Ctrl+C to stop)"""
        if not vehicle_id:
            # Show all vehicles
            vehicles = await self.connector.get_vehicles()
            if not vehicles:
                self.print("[yellow]No vehicles to monitor[/yellow]")
                return
            vehicle_id = vehicles[0].vehicle_id
        
        self.print(f"[cyan]📊 Live Dashboard for {vehicle_id} (Ctrl+C to stop)[/cyan]" if self.console else f"📊 Live Dashboard for {vehicle_id}")
        
        # Track events
        events = []
        
        def on_boarding(data):
            if data.get("vehicle_id") == vehicle_id:
                events.append({
                    "type": "boarding",
                    "time": datetime.now(),
                    "passengers": data.get("passengers", 0)
                })
        
        def on_alighting(data):
            if data.get("vehicle_id") == vehicle_id:
                events.append({
                    "type": "alighting",
                    "time": datetime.now(),
                    "passengers": data.get("passengers", 0)
                })
        
        def on_engine(data):
            if data.get("vehicle_id") == vehicle_id:
                events.append({
                    "type": "engine_" + ("started" if "started" in data.get("event_type", "") else "stopped"),
                    "time": datetime.now()
                })
        
        self.connector.on("passenger_boarded", on_boarding)
        self.connector.on("passenger_alighted", on_alighting)
        self.connector.on("engine_started", on_engine)
        self.connector.on("engine_stopped", on_engine)
        
        await self.connector.connect_websocket()
        
        try:
            while True:
                # Get current vehicle state
                try:
                    vehicle = await self.connector.get_vehicle(vehicle_id)
                    
                    if self.console:
                        # Rich dashboard
                        dashboard = f"""
[bold cyan]Vehicle:[/bold cyan] {vehicle.vehicle_id}
[cyan]Driver:[/cyan] {vehicle.driver_name or 'N/A'} | [cyan]Route:[/cyan] {vehicle.route_id or 'N/A'} | [cyan]State:[/cyan] {vehicle.driver_state or 'N/A'}

[bold yellow]📍 POSITION:[/bold yellow]
  Lat: {vehicle.current_position.latitude if vehicle.current_position else 'N/A':.6f}
  Lon: {vehicle.current_position.longitude if vehicle.current_position else 'N/A':.6f}

[bold green]⚙️  DEVICES:[/bold green]
  Engine:  {'🟢 RUNNING' if vehicle.engine_running else '🔴 STOPPED'}
  GPS:     {'🟢 ACTIVE' if vehicle.gps_running else '🔴 OFFLINE'}
  Boarding: {'✅ ENABLED' if vehicle.boarding_active else '⏸️  DISABLED'}

[bold blue]👥 PASSENGERS:[/bold blue]
  On Board: {vehicle.passenger_count} / {vehicle.capacity}
  Capacity: {100 * vehicle.passenger_count // max(1, vehicle.capacity)}%

[bold magenta]📊 RECENT EVENTS:[/bold magenta]"""
                        
                        for evt in events[-10:]:
                            if evt["type"] == "boarding":
                                dashboard += f"\n  ✅ Boarded {evt['passengers']} passengers @ {evt['time'].strftime('%H:%M:%S')}"
                            elif evt["type"] == "alighting":
                                dashboard += f"\n  ↩️  Alighted {evt['passengers']} passengers @ {evt['time'].strftime('%H:%M:%S')}"
                            elif evt["type"] == "engine_started":
                                dashboard += f"\n  🔥 Engine started @ {evt['time'].strftime('%H:%M:%S')}"
                            elif evt["type"] == "engine_stopped":
                                dashboard += f"\n  ❄️  Engine stopped @ {evt['time'].strftime('%H:%M:%S')}"
                        
                        if self.console:
                            self.console.clear()
                            self.console.print(Panel(dashboard, title=f"🚌 Live Telemetry: {vehicle_id}", border_style="blue", expand=False))
                    else:
                        # Plain text dashboard
                        print("\033[2J\033[H")  # Clear screen
                        print("="*70)
                        print(f"🚌 LIVE TELEMETRY: {vehicle_id}")
                        print("="*70)
                        print(f"\nVehicle:  {vehicle.vehicle_id}")
                        print(f"Driver:   {vehicle.driver_name or 'N/A'} | Route: {vehicle.route_id or 'N/A'} | State: {vehicle.driver_state or 'N/A'}")
                        print(f"\n📍 POSITION:")
                        print(f"  Latitude:  {vehicle.current_position.latitude if vehicle.current_position else 'N/A'}")
                        print(f"  Longitude: {vehicle.current_position.longitude if vehicle.current_position else 'N/A'}")
                        print(f"\n⚙️  DEVICES:")
                        print(f"  Engine:   {'RUNNING' if vehicle.engine_running else 'STOPPED'}")
                        print(f"  GPS:      {'ACTIVE' if vehicle.gps_running else 'OFFLINE'}")
                        print(f"  Boarding: {'ENABLED' if vehicle.boarding_active else 'DISABLED'}")
                        print(f"\n👥 PASSENGERS: {vehicle.passenger_count} / {vehicle.capacity}")
                        print(f"\n📊 RECENT EVENTS:")
                        for evt in events[-10:]:
                            if evt["type"] == "boarding":
                                print(f"  ✅ Boarded {evt['passengers']} @ {evt['time'].strftime('%H:%M:%S')}")
                            elif evt["type"] == "alighting":
                                print(f"  ↩️  Alighted {evt['passengers']} @ {evt['time'].strftime('%H:%M:%S')}")
                            elif evt["type"] == "engine_started":
                                print(f"  🔥 Engine started @ {evt['time'].strftime('%H:%M:%S')}")
                            elif evt["type"] == "engine_stopped":
                                print(f"  ❄️  Engine stopped @ {evt['time'].strftime('%H:%M:%S')}")
                        print("\n(Ctrl+C to stop)")
                        print("="*70)
                    
                    await asyncio.sleep(2)  # Refresh every 2 seconds
                    
                except Exception as e:
                    self.print(f"[red]Error updating dashboard: {e}[/red]" if self.console else f"Error: {e}")
                    await asyncio.sleep(2)
                    
        except KeyboardInterrupt:
            self.print("\n[yellow]📊 Dashboard closed[/yellow]" if self.console else "\n📊 Dashboard closed")
            await self.connector.disconnect_websocket()
    
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
        """Show comprehensive help with menu system"""
        help_text = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                  ArkNet FLEET MANAGEMENT CONSOLE - HELP                  ║
║                         Professional Grade CLI                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│ 1. SERVICE MANAGEMENT (Start/Stop Infrastructure)                       │
└─────────────────────────────────────────────────────────────────────────┘

  ⚡ QUICK START:
  ├─ start-service all              - ⭐ START ALL SERVICES (gpscentcom, geospatial, 
  │                                       commuter_service, simulator)
  ├─ services                       - ⭐ CHECK ALL SERVICE STATUS
  └─ stop-service all               - ⭐ STOP ALL SERVICES

  START INDIVIDUAL SERVICES:
  ├─ start-service simulator        - Start vehicle transit simulator (port 5001)
  ├─ start-service gpscentcom       - Start GPS/location server (port 5000)
  ├─ start-service geospatial       - Start geospatial query service (port 6000)
  └─ start-service commuter_service - Start passenger management service (port 4000)

  STOP INDIVIDUAL SERVICES:
  ├─ stop-service simulator         - Stop vehicle transit simulator
  ├─ stop-service gpscentcom        - Stop GPS/location server
  ├─ stop-service geospatial        - Stop geospatial query service
  ├─ stop-service commuter_service  - Stop passenger management service
  └─ restart-service <service_name> - Restart any service

  SERVICE STATUS:
  └─ services                       - Show detailed status: status, PID, uptime, errors

  SIMULATOR STARTUP WITH OPTIONS:
  ├─ start-service simulator sim_time=14:30                    - Set start time
  ├─ start-service simulator api_port=5001                    - Custom API port
  ├─ start-service simulator data_api_url=http://localhost:1337 - Custom data API
  ├─ start-service simulator enable_boarding_after=30.0       - Enable boarding delay
  └─ start-service simulator sim_time=14:30 api_port=5001     - Multiple options

┌─────────────────────────────────────────────────────────────────────────┐
│ 2. VEHICLE & FLEET OPERATIONS                                           │
└─────────────────────────────────────────────────────────────────────────┘

  VEHICLE MONITORING:
  ├─ vehicles              - List ALL vehicles with status summary
  ├─ vehicle <vehicle_id>  - Show detailed state for specific vehicle
  ├─ conductors            - List ALL conductors and assignments
  └─ conductor <vehicle_id>- Show conductor details for vehicle

  ENGINE CONTROL:
  ├─ start <vehicle_id>    - Start engine (e.g., start ZR102)
  └─ stop <vehicle_id>     - Stop engine (e.g., stop ZR102)

  BOARDING MANAGEMENT:
  ├─ enable <vehicle_id>   - Enable passenger boarding
  ├─ disable <vehicle_id>  - Disable passenger boarding
  └─ trigger <vehicle_id>  - Manual boarding check cycle

┌─────────────────────────────────────────────────────────────────────────┐
│ 3. SIMULATOR CONTROL                                                    │
└─────────────────────────────────────────────────────────────────────────┘

  SIMULATOR STATE:
  ├─ sim                   - Show simulator status (time, vehicles, events)
  ├─ pause                 - Pause simulation (vehicles halt, time stops)
  ├─ resume                - Resume simulation from pause
  └─ stop-sim              - SHUTDOWN simulator (full stop)

  TIME CONTROL:
  ├─ set-time 14:30        - Set simulation time (HH:MM format)
  └─ set-time 2025-11-06T14:30 - Set specific date/time (ISO format)

┌─────────────────────────────────────────────────────────────────────────┐
│ 4. DIAGNOSTICS & MONITORING                                             │
└─────────────────────────────────────────────────────────────────────────┘

  STATUS & HEALTH:
  ├─ status                - Show API connection & system health
  ├─ services              - Service status with PID, uptime, error details
  └─ stream                - LIVE EVENT STREAMING (real-time events)

┌─────────────────────────────────────────────────────────────────────────┐
│ 5. COMMAND EXAMPLES & WORKFLOWS                                         │
└─────────────────────────────────────────────────────────────────────────┘

  QUICK START WORKFLOW:
    fleet> start-service all              # Start all services
    fleet> services                       # Check all services running
    fleet> vehicles                       # List all vehicles
    fleet> vehicle ZR102                  # Check specific vehicle
    fleet> start ZR102                    # Start engine
    fleet> enable ZR102                   # Enable boarding
    fleet> stream                         # Watch live events

  INDIVIDUAL SERVICE TESTS:
    fleet> stop-service simulator
    fleet> start-service simulator sim_time=09:00
    fleet> services
    fleet> vehicles

  SIMULATION CONTROL:
    fleet> pause                          # Pause all vehicles
    fleet> set-time 16:45                 # Jump to 4:45 PM
    fleet> resume                         # Continue simulation
    fleet> stop-sim                       # End simulation session

  TROUBLESHOOTING:
    fleet> services                       # Check for service errors (❌ status)
    fleet> vehicle ZR102                  # Verify vehicle state
    fleet> status                         # Check connection health
    fleet> stream                         # Monitor real-time errors

┌─────────────────────────────────────────────────────────────────────────┐
│ 6. COMMAND REFERENCE                                                    │
└─────────────────────────────────────────────────────────────────────────┘

  GENERAL:
  ├─ help                  - Show this help message
  ├─ help <topic>          - Show help for specific topic
  ├─ exit / quit           - Exit console cleanly
  └─ Ctrl+C                - Interrupt command (use 'exit' to quit)

  TIPS & NOTES:
  • All service names: simulator, gpscentcom, geospatial, commuter_service
  • Vehicle IDs: ZR102, ZR103, etc. (from database)
  • Times: Use HH:MM (24-hour) or ISO format YYYY-MM-DDTHH:MM
  • Options: Multiple options separated by spaces (key=value format)
  • Live Streaming: Ctrl+C to stop, then type next command
  • Colors: 🟢 running, 🔴 stopped, 🟡 starting, ❌ error, ⚪ unknown

═══════════════════════════════════════════════════════════════════════════
Type a command (e.g., 'services' or 'vehicles') and press Enter to begin.
═══════════════════════════════════════════════════════════════════════════
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
                elif cmd == "services":
                    await self.cmd_services()
                elif cmd == "start-service":
                    if not args:
                        self.print("[red]Usage: start-service <service_name> [args][/red]" if self.console else "Usage: start-service <service_name>")
                    else:
                        parts = args.split(maxsplit=1)
                        service_name = parts[0]
                        service_args = parts[1] if len(parts) > 1 else ""
                        await self.cmd_start_service(service_name, service_args)
                elif cmd == "stop-service":
                    if not args:
                        self.print("[red]Usage: stop-service <service_name>[/red]" if self.console else "Usage: stop-service <service_name>")
                    else:
                        await self.cmd_stop_service(args)
                elif cmd == "restart-service":
                    if not args:
                        self.print("[red]Usage: restart-service <service_name>[/red]" if self.console else "Usage: restart-service <service_name>")
                    else:
                        await self.cmd_restart_service(args)
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
    parser.add_argument("--url", default="http://localhost:6000", help="Fleet API URL")
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
