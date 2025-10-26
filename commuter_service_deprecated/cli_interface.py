"""
Commuter Service CLI Interface

Rich terminal interface for monitoring the commuter service in real-time.
Displays spawn events, statistics, zone loading, and service health.

Usage:
    python -m commuter_service.cli_interface
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box
from collections import deque


class CommuterServiceCLI:
    """
    Rich CLI interface for commuter service monitoring.
    
    Features:
    - Live spawn event feed
    - Real-time statistics dashboard
    - Zone loading progress
    - Service health monitoring
    - Reservoir status
    """
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        
        # Event tracking
        self.spawn_events = deque(maxlen=15)  # Last 15 spawn events
        self.zone_loading_status = "⏳ Initializing..."
        self.service_status = "🚀 Starting..."
        
        # Statistics
        self.stats = {
            'depot_reservoir': {
                'total_spawns': 0,
                'active_commuters': 0,
                'zones_loaded': 0
            },
            'route_reservoir': {
                'total_spawns': 0,
                'active_commuters': 0,
                'zones_loaded': 0
            },
            'spatial_cache': {
                'population_zones': 0,
                'amenity_zones': 0,
                'buffer_km': 5.0,
                'loading_complete': False
            }
        }
        
        # Timing
        self.start_time = datetime.now()
        self.last_spawn_time: Optional[datetime] = None
        
        # Layout configuration
        self._setup_layout()
    
    def _setup_layout(self):
        """Configure the terminal layout"""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        self.layout["left"].split_column(
            Layout(name="spawn_feed", ratio=2),
            Layout(name="statistics", ratio=1)
        )
        
        self.layout["right"].split_column(
            Layout(name="zones", ratio=1),
            Layout(name="health", ratio=1)
        )
    
    def _make_header(self) -> Panel:
        """Create header panel"""
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        header_text = Text()
        header_text.append("🚍 ", style="bold yellow")
        header_text.append("ArkNet Commuter Service", style="bold cyan")
        header_text.append(f" | Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}", style="dim")
        header_text.append(f" | {self.service_status}", style="bold green")
        
        return Panel(header_text, border_style="cyan", box=box.ROUNDED)
    
    def _make_spawn_feed(self) -> Panel:
        """Create spawn event feed panel"""
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.SIMPLE,
            expand=True
        )
        
        table.add_column("Time", style="cyan", width=8)
        table.add_column("Type", width=8)
        table.add_column("Zone", style="yellow")
        table.add_column("Count", justify="right", width=6)
        
        # Add recent spawn events
        for event in reversed(list(self.spawn_events)):
            table.add_row(
                event['time'],
                event['type'],
                event['zone'][:30],  # Truncate long zone names
                str(event['count'])
            )
        
        return Panel(
            table,
            title="📊 Recent Spawn Events",
            border_style="magenta",
            box=box.ROUNDED
        )
    
    def _make_statistics(self) -> Panel:
        """Create statistics panel"""
        depot_stats = self.stats['depot_reservoir']
        route_stats = self.stats['route_reservoir']
        
        stats_text = Text()
        stats_text.append("🏢 Depot Reservoir\n", style="bold cyan")
        stats_text.append(f"  Total Spawns: {depot_stats['total_spawns']}\n")
        stats_text.append(f"  Active: {depot_stats['active_commuters']}\n")
        stats_text.append(f"  Zones: {depot_stats['zones_loaded']}\n\n")
        
        stats_text.append("🛣️  Route Reservoir\n", style="bold cyan")
        stats_text.append(f"  Total Spawns: {route_stats['total_spawns']}\n")
        stats_text.append(f"  Active: {route_stats['active_commuters']}\n")
        stats_text.append(f"  Zones: {route_stats['zones_loaded']}\n")
        
        if self.last_spawn_time:
            time_since = (datetime.now() - self.last_spawn_time).total_seconds()
            stats_text.append(f"\n⏱️  Last spawn: {time_since:.0f}s ago", style="dim")
        
        return Panel(
            stats_text,
            title="📈 Statistics",
            border_style="blue",
            box=box.ROUNDED
        )
    
    def _make_zones_panel(self) -> Panel:
        """Create zone loading status panel"""
        cache_stats = self.stats['spatial_cache']
        
        zones_text = Text()
        zones_text.append(f"{self.zone_loading_status}\n\n", style="bold")
        
        if cache_stats['loading_complete']:
            zones_text.append(f"✅ Population: {cache_stats['population_zones']}\n", style="green")
            zones_text.append(f"✅ Amenity: {cache_stats['amenity_zones']}\n", style="green")
            zones_text.append(f"📍 Buffer: ±{cache_stats['buffer_km']}km\n", style="cyan")
        else:
            zones_text.append("⏳ Loading zones...\n", style="yellow")
        
        return Panel(
            zones_text,
            title="🗺️  Spatial Cache",
            border_style="green",
            box=box.ROUNDED
        )
    
    def _make_health_panel(self) -> Panel:
        """Create service health panel"""
        health_text = Text()
        
        # Check if zones are loaded
        zones_ok = self.stats['spatial_cache']['loading_complete']
        
        # Check if spawns are happening
        spawns_ok = (
            self.stats['depot_reservoir']['total_spawns'] > 0 or
            self.stats['route_reservoir']['total_spawns'] > 0
        )
        
        health_text.append("Spatial Cache: ", style="bold")
        health_text.append("✅ Ready\n" if zones_ok else "⏳ Loading\n", 
                          style="green" if zones_ok else "yellow")
        
        health_text.append("Depot Spawns: ", style="bold")
        health_text.append("✅ Active\n" if spawns_ok else "⏳ Pending\n",
                          style="green" if spawns_ok else "yellow")
        
        health_text.append("Route Spawns: ", style="bold")
        health_text.append("✅ Active\n" if spawns_ok else "⏳ Pending\n",
                          style="green" if spawns_ok else "yellow")
        
        return Panel(
            health_text,
            title="💚 Health",
            border_style="green" if zones_ok and spawns_ok else "yellow",
            box=box.ROUNDED
        )
    
    def _make_footer(self) -> Panel:
        """Create footer panel"""
        footer_text = Text()
        footer_text.append("Press ", style="dim")
        footer_text.append("Ctrl+C", style="bold red")
        footer_text.append(" to stop | ", style="dim")
        footer_text.append("API: http://localhost:1337", style="cyan")
        footer_text.append(" | ", style="dim")
        footer_text.append(f"Updated: {datetime.now().strftime('%H:%M:%S')}", style="dim")
        
        return Panel(footer_text, border_style="dim", box=box.ROUNDED)
    
    def render(self) -> Layout:
        """Render the complete layout"""
        self.layout["header"].update(self._make_header())
        self.layout["spawn_feed"].update(self._make_spawn_feed())
        self.layout["statistics"].update(self._make_statistics())
        self.layout["zones"].update(self._make_zones_panel())
        self.layout["health"].update(self._make_health_panel())
        self.layout["footer"].update(self._make_footer())
        
        return self.layout
    
    # Event handlers for service updates
    
    def on_spawn_event(self, spawn_type: str, zone_type: str, count: int):
        """Record a spawn event"""
        self.spawn_events.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': spawn_type,
            'zone': zone_type,
            'count': count
        })
        self.last_spawn_time = datetime.now()
        
        # Update statistics
        if spawn_type.lower() == 'depot':
            self.stats['depot_reservoir']['total_spawns'] += count
        elif spawn_type.lower() == 'route':
            self.stats['route_reservoir']['total_spawns'] += count
    
    def on_zone_loading_start(self, total_zones: int):
        """Zone loading started"""
        self.zone_loading_status = f"⏳ Loading {total_zones} zones..."
    
    def on_zone_loading_complete(self, population: int, amenity: int):
        """Zone loading completed"""
        self.zone_loading_status = "✅ Zones Loaded"
        self.stats['spatial_cache']['population_zones'] = population
        self.stats['spatial_cache']['amenity_zones'] = amenity
        self.stats['spatial_cache']['loading_complete'] = True
        
        # Update reservoir zone counts
        self.stats['depot_reservoir']['zones_loaded'] = population + amenity
        self.stats['route_reservoir']['zones_loaded'] = population + amenity
    
    def on_service_ready(self):
        """Service is ready"""
        self.service_status = "✅ Running"
    
    def update_active_commuters(self, depot_count: int, route_count: int):
        """Update active commuter counts"""
        self.stats['depot_reservoir']['active_commuters'] = depot_count
        self.stats['route_reservoir']['active_commuters'] = route_count
    
    def set_buffer_distance(self, buffer_km: float):
        """Set spatial cache buffer distance"""
        self.stats['spatial_cache']['buffer_km'] = buffer_km


class CLILogger(logging.Handler):
    """
    Custom logging handler that feeds events to the CLI interface.
    Intercepts log messages and updates the CLI display.
    """
    
    def __init__(self, cli: CommuterServiceCLI):
        super().__init__()
        self.cli = cli
    
    def emit(self, record: logging.LogRecord):
        """Process log records and update CLI"""
        msg = record.getMessage()
        
        # Parse spawn events
        if '🎲' in msg and 'spawn requests' in msg.lower():
            # Extract spawn count from message
            import re
            match = re.search(r'Generated (\d+) spawn requests', msg)
            if match:
                count = int(match.group(1))
                spawn_type = 'DEPOT' if 'DEPOT' in msg else 'ROUTE'
                self.cli.on_spawn_event(spawn_type, 'Various zones', count)
        
        # Parse zone loading
        if '✅ Background zone loading complete' in msg:
            # Get stats from CLI (already updated by other messages)
            pop = self.cli.stats['spatial_cache']['population_zones']
            amenity = self.cli.stats['spatial_cache']['amenity_zones']
            self.cli.on_zone_loading_complete(pop, amenity)
        
        if '🎯 Spatial filter' in msg:
            # Extract zone counts
            import re
            match = re.search(r'(\d+) population zones, (\d+) amenity zones', msg)
            if match:
                pop = int(match.group(1))
                amenity = int(match.group(2))
                self.cli.stats['spatial_cache']['population_zones'] = pop
                self.cli.stats['spatial_cache']['amenity_zones'] = amenity
        
        # Service ready
        if 'successfully with automatic spawning' in msg:
            self.cli.on_service_ready()


async def run_cli_interface():
    """
    Run the CLI interface with live updates.
    This is the main entry point for the CLI.
    """
    cli = CommuterServiceCLI()
    
    # Setup logging to feed CLI
    cli_logger = CLILogger(cli)
    cli_logger.setLevel(logging.INFO)
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(cli_logger)
    
    # Start live display
    with Live(cli.render(), console=cli.console, refresh_per_second=2) as live:
        try:
            # Import and start the actual commuter service
            from commuter_service.depot_reservoir import DepotReservoir
            from commuter_service.route_reservoir import RouteReservoir
            
            cli.console.print("\n[bold cyan]🚀 Starting ArkNet Commuter Service...[/bold cyan]\n")
            
            # Create reservoirs
            depot_reservoir = DepotReservoir(
                socketio_url="http://localhost:1337",
                strapi_url="http://localhost:1337"
            )
            
            route_reservoir = RouteReservoir(
                socketio_url="http://localhost:1337",
                strapi_url="http://localhost:1337"
            )
            
            # Start both reservoirs
            await depot_reservoir.start()
            await route_reservoir.start()
            
            cli.on_service_ready()
            
            # Keep running and updating display
            update_counter = 0
            while True:
                await asyncio.sleep(0.5)  # Update twice per second
                
                # Update active commuter counts every 5 seconds
                if update_counter % 10 == 0:
                    depot_active = len(depot_reservoir.active_commuters)
                    route_active = len(route_reservoir.active_commuters)
                    cli.update_active_commuters(depot_active, route_active)
                
                # Refresh the display
                live.update(cli.render())
                update_counter += 1
                
        except KeyboardInterrupt:
            cli.console.print("\n[bold yellow]🛑 Shutting down gracefully...[/bold yellow]\n")
            
            # Stop reservoirs
            if 'depot_reservoir' in locals():
                await depot_reservoir.stop()
            if 'route_reservoir' in locals():
                await route_reservoir.stop()
            
            cli.console.print("[bold green]✅ Service stopped successfully[/bold green]\n")
        
        except Exception as e:
            cli.console.print(f"\n[bold red]❌ Error: {e}[/bold red]\n")
            raise


def main():
    """Entry point for CLI"""
    try:
        asyncio.run(run_cli_interface())
    except KeyboardInterrupt:
        pass  # Handled in run_cli_interface


if __name__ == "__main__":
    main()
