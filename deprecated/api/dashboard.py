#!/usr/bin/env python3
"""
ArkNet Transit Simulator TUI Dashboard
=====================================

Terminal User Interface dashboard that connects to the simulator API
and displays comprehensive real-time status information.

Usage:
    cd api/
    python dashboard.py
    
    # Or with custom API endpoint:
    python dashboard.py --api-url http://127.0.0.1:8090
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import aiohttp
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Label, DataTable, 
    TabbedContent, TabPane, Log, ProgressBar, Pretty
)
from textual.reactive import reactive
from textual.timer import Timer


@dataclass
class SystemStatus:
    """System status data structure"""
    simulator_running: bool = False
    simulator_uptime: Optional[float] = None
    depot_state: str = "unknown"
    total_vehicles: int = 0
    active_vehicles: int = 0
    total_drivers: int = 0
    active_drivers: int = 0
    total_conductors: int = 0
    active_conductors: int = 0
    gps_devices: int = 0
    active_passengers: int = 0
    last_update: Optional[datetime] = None


class StatusCard(Static):
    """Reusable status card widget"""
    
    def __init__(self, title: str, value: str = "---", status: str = "unknown"):
        super().__init__()
        self.title = title
        self.value = value
        self.status = status
    
    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="card-title")
        yield Label(self.value, classes="card-value")
    
    def update_status(self, value: str, status: str = "unknown"):
        self.value = value
        self.status = status
        self.query_one(".card-value", Label).update(value)
        # Update styling based on status
        if status == "active":
            self.add_class("status-active")
            self.remove_class("status-inactive", "status-error")
        elif status == "inactive":
            self.add_class("status-inactive") 
            self.remove_class("status-active", "status-error")
        elif status == "error":
            self.add_class("status-error")
            self.remove_class("status-active", "status-inactive")


class ApiClient:
    """API client for communicating with simulator REST API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8090"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Make GET request to API endpoint"""
        if not self.session:
            raise RuntimeError("ApiClient not initialized - use async context manager")
        
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}", "detail": await response.text()}
        except aiohttp.ClientError as e:
            return {"error": "Connection failed", "detail": str(e)}
        except asyncio.TimeoutError:
            return {"error": "Request timeout", "detail": "API request took too long"}
    
    async def post(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make POST request to API endpoint"""
        if not self.session:
            raise RuntimeError("ApiClient not initialized - use async context manager")
        
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}", "detail": await response.text()}
        except aiohttp.ClientError as e:
            return {"error": "Connection failed", "detail": str(e)}
        except asyncio.TimeoutError:
            return {"error": "Request timeout", "detail": "API request took too long"}


class SimulatorDashboard(App):
    """Main TUI dashboard application"""
    
    CSS = """
    .card-title {
        text-style: bold;
        color: $accent;
    }
    
    .card-value {
        text-style: bold;
        padding: 1;
    }
    
    .status-active .card-value {
        color: $success;
    }
    
    .status-inactive .card-value {
        color: $warning;
    }
    
    .status-error .card-value {
        color: $error;
    }
    
    .status-grid {
        grid-size: 4;
        grid-gutter: 1;
        padding: 1;
    }
    
    .control-bar {
        height: 3;
        padding: 1;
    }
    
    .data-panel {
        height: 1fr;
        padding: 1;
    }
    
    .log-panel {
        height: 30%;
        border: solid $primary;
    }
    """
    
    TITLE = "ArkNet Transit Simulator Dashboard"
    SUB_TITLE = "Real-time monitoring and control"
    
    def __init__(self, api_url: str = "http://127.0.0.1:8090"):
        super().__init__()
        self.api_url = api_url
        self.api_client: Optional[ApiClient] = None
        self.system_status = SystemStatus()
        self.update_timer: Optional[Timer] = None
        self.connected = False
    
    def compose(self) -> ComposeResult:
        """Compose the dashboard layout"""
        yield Header()
        
        # Control bar
        with Horizontal(classes="control-bar"):
            yield Button("Start Simulator", variant="success", id="start-sim")
            yield Button("Stop Simulator", variant="error", id="stop-sim")
            yield Button("Refresh", variant="primary", id="refresh")
            yield Label(f"API: {self.api_url}", id="api-status")
        
        # Main content with tabs
        with TabbedContent(initial="overview"):
            # Overview tab
            with TabPane("Overview", id="overview"):
                with Container(classes="status-grid"):
                    yield StatusCard("Simulator", "Stopped", "inactive")
                    yield StatusCard("Depot", "Closed", "inactive") 
                    yield StatusCard("Vehicles", "0", "inactive")
                    yield StatusCard("Drivers", "0/0", "inactive")
                    yield StatusCard("Conductors", "0", "inactive")
                    yield StatusCard("GPS Devices", "0", "inactive")
                    yield StatusCard("Passengers", "0", "inactive")
                    yield StatusCard("Last Update", "Never", "inactive")
                
                # System details
                with ScrollableContainer(classes="data-panel"):
                    yield Pretty({}, id="system-details")
            
            # Vehicles tab
            with TabPane("Vehicles", id="vehicles"):
                yield DataTable(id="vehicles-table")
            
            # Drivers tab  
            with TabPane("Drivers", id="drivers"):
                yield DataTable(id="drivers-table")
            
            # Conductors tab
            with TabPane("Conductors", id="conductors"):
                yield DataTable(id="conductors-table")
            
            # GPS tab
            with TabPane("GPS/Telemetry", id="gps"):
                yield DataTable(id="gps-table")
            
            # Passengers tab
            with TabPane("Passengers", id="passengers"):
                with Vertical():
                    yield Pretty({}, id="passenger-stats")
                    yield DataTable(id="passengers-table")
            
            # Routes tab
            with TabPane("Routes", id="routes"):
                yield DataTable(id="routes-table")
            
            # API Log tab
            with TabPane("API Log", id="log"):
                yield Log(id="api-log")
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize the dashboard"""
        # Initialize API client
        self.api_client = ApiClient(self.api_url)
        await self.api_client.__aenter__()
        
        # Setup tables
        self._setup_tables()
        
        # Start periodic updates
        self.update_timer = self.set_interval(2.0, self._update_data)
        
        # Initial data load
        await self._update_data()
        
        self.log_message("Dashboard initialized", "INFO")
    
    def _setup_tables(self):
        """Setup data table columns"""
        # Vehicles table
        vehicles_table = self.query_one("#vehicles-table", DataTable)
        vehicles_table.add_columns("Vehicle ID", "Driver", "Route", "Status", "Engine", "GPS", "Position")
        
        # Drivers table
        drivers_table = self.query_one("#drivers-table", DataTable) 
        drivers_table.add_columns("Driver ID", "Name", "State", "Vehicle", "Route", "Position")
        
        # Conductors table
        conductors_table = self.query_one("#conductors-table", DataTable)
        conductors_table.add_columns("Conductor ID", "Name", "State", "Vehicle", "Route", "Passengers", "Capacity")
        
        # GPS table
        gps_table = self.query_one("#gps-table", DataTable)
        gps_table.add_columns("Device ID", "Vehicle", "State", "Position", "Last Update", "Transmitting")
        
        # Passengers table
        passengers_table = self.query_one("#passengers-table", DataTable)
        passengers_table.add_columns("Passenger ID", "Status", "Origin", "Destination", "Spawn Time")
        
        # Routes table
        routes_table = self.query_one("#routes-table", DataTable)
        routes_table.add_columns("Route ID", "Name", "Vehicles", "GPS Points", "Length", "Status")
    
    async def _update_data(self):
        """Update all dashboard data from API"""
        if not self.api_client:
            return
        
        try:
            # Get simulator status
            sim_status = await self.api_client.get("/simulator/status")
            
            # Get comprehensive system data
            depot_status = await self.api_client.get("/depot/status")
            vehicles_data = await self.api_client.get("/vehicles")
            drivers_data = await self.api_client.get("/drivers")
            conductors_data = await self.api_client.get("/conductors")
            gps_data = await self.api_client.get("/gps/devices")
            passengers_data = await self.api_client.get("/passengers/stats")
            passengers_active = await self.api_client.get("/passengers/active")
            routes_data = await self.api_client.get("/routes")
            
            # Update system status
            if "error" not in sim_status:
                self.system_status.simulator_running = sim_status.get("status") == "running"
                self.system_status.simulator_uptime = sim_status.get("uptime_seconds")
            
            self.system_status.depot_state = depot_status.get("depot_state", "unknown")
            self.system_status.total_vehicles = vehicles_data.get("total_vehicles", 0)
            self.system_status.active_vehicles = vehicles_data.get("active_vehicles", 0)
            self.system_status.total_drivers = drivers_data.get("total_drivers", 0)
            self.system_status.active_drivers = drivers_data.get("active_drivers", 0)
            self.system_status.total_conductors = conductors_data.get("total_conductors", 0)
            self.system_status.active_conductors = conductors_data.get("active_conductors", 0)
            self.system_status.gps_devices = gps_data.get("total_devices", 0)
            self.system_status.active_passengers = passengers_active.get("count", 0)
            self.system_status.last_update = datetime.now()
            
            # Update UI
            self._update_status_cards()
            self._update_tables(vehicles_data, drivers_data, conductors_data, gps_data, passengers_active, routes_data)
            self._update_system_details(depot_status, passengers_data)
            
            self.connected = True
            self.query_one("#api-status", Label).update(f"API: {self.api_url} ✅")
            
        except Exception as e:
            self.connected = False
            self.query_one("#api-status", Label).update(f"API: {self.api_url} ❌")
            self.log_message(f"Update failed: {str(e)}", "ERROR")
    
    def _update_status_cards(self):
        """Update status cards with current system status"""
        cards = self.query("StatusCard")
        
        if len(cards) >= 8:
            # Simulator status
            sim_status = "Running" if self.system_status.simulator_running else "Stopped"
            sim_state = "active" if self.system_status.simulator_running else "inactive"
            if self.system_status.simulator_uptime:
                sim_status += f" ({self.system_status.simulator_uptime:.0f}s)"
            cards[0].update_status(sim_status, sim_state)
            
            # Depot status
            depot_status = self.system_status.depot_state.title()
            depot_state = "active" if self.system_status.depot_state == "open" else "inactive"
            cards[1].update_status(depot_status, depot_state)
            
            # Vehicles
            vehicle_status = f"{self.system_status.active_vehicles}/{self.system_status.total_vehicles}"
            vehicle_state = "active" if self.system_status.active_vehicles > 0 else "inactive"
            cards[2].update_status(vehicle_status, vehicle_state)
            
            # Drivers
            driver_status = f"{self.system_status.active_drivers}/{self.system_status.total_drivers}"
            driver_state = "active" if self.system_status.active_drivers > 0 else "inactive"
            cards[3].update_status(driver_status, driver_state)
            
            # Conductors
            conductor_status = str(self.system_status.active_conductors)
            conductor_state = "active" if self.system_status.active_conductors > 0 else "inactive"
            cards[4].update_status(conductor_status, conductor_state)
            
            # GPS Devices
            gps_status = str(self.system_status.gps_devices)
            gps_state = "active" if self.system_status.gps_devices > 0 else "inactive"
            cards[5].update_status(gps_status, gps_state)
            
            # Passengers
            passenger_status = str(self.system_status.active_passengers)
            passenger_state = "active" if self.system_status.active_passengers > 0 else "inactive"
            cards[6].update_status(passenger_status, passenger_state)
            
            # Last update
            if self.system_status.last_update:
                update_time = self.system_status.last_update.strftime("%H:%M:%S")
                cards[7].update_status(update_time, "active")
    
    def _update_tables(self, vehicles_data, drivers_data, conductors_data, gps_data, passengers_data, routes_data):
        """Update data tables with fresh data"""
        try:
            # Update vehicles table
            vehicles_table = self.query_one("#vehicles-table", DataTable)
            vehicles_table.clear()
            for vehicle in vehicles_data.get("vehicles", []):
                vehicles_table.add_row(
                    vehicle.get("vehicle_id", "---"),
                    vehicle.get("driver_name", "---"),
                    vehicle.get("route_id", "---"),
                    vehicle.get("driver_status", "---"),
                    vehicle.get("engine_status", "---"),
                    vehicle.get("gps_status", "---"),
                    f"{vehicle.get('gps_position', {}).get('lat', '---'):.4f}, {vehicle.get('gps_position', {}).get('lon', '---'):.4f}" if vehicle.get('gps_position') else "---"
                )
            
            # Update drivers table
            drivers_table = self.query_one("#drivers-table", DataTable)
            drivers_table.clear()
            for driver in drivers_data.get("drivers", []):
                drivers_table.add_row(
                    driver.get("driver_id", "---"),
                    driver.get("driver_name", "---"),
                    driver.get("current_state", "---"),
                    driver.get("vehicle_id", "---"),
                    driver.get("route_name", "---"),
                    f"{driver.get('gps_position', {}).get('lat', '---'):.4f}, {driver.get('gps_position', {}).get('lon', '---'):.4f}" if driver.get('gps_position') else "---"
                )
            
            # Update conductors table
            conductors_table = self.query_one("#conductors-table", DataTable)
            conductors_table.clear()
            for conductor in conductors_data.get("conductors", []):
                conductors_table.add_row(
                    conductor.get("conductor_id", "---"),
                    conductor.get("conductor_name", "---"),
                    conductor.get("conductor_state", "---"),
                    conductor.get("vehicle_id", "---"),
                    conductor.get("assigned_route_id", "---"),
                    str(conductor.get("passengers_on_board", "---")),
                    str(conductor.get("capacity", "---"))
                )
            
            # Update GPS table
            gps_table = self.query_one("#gps-table", DataTable)
            gps_table.clear()
            for device in gps_data.get("devices", []):
                gps_table.add_row(
                    device.get("device_id", "---"),
                    device.get("vehicle_id", "---"),
                    device.get("current_state", "---"),
                    f"{device.get('last_position', {}).get('lat', '---'):.4f}, {device.get('last_position', {}).get('lon', '---'):.4f}" if device.get('last_position') else "---",
                    device.get("last_transmission", "---"),
                    "Yes" if device.get("transmitter_connected") else "No"
                )
            
            # Update passengers table
            passengers_table = self.query_one("#passengers-table", DataTable)
            passengers_table.clear()
            for passenger in passengers_data.get("passengers", []):
                passengers_table.add_row(
                    passenger.get("passenger_id", "---"),
                    passenger.get("status", "---"),
                    passenger.get("origin", "---"),
                    passenger.get("destination", "---"),
                    passenger.get("spawn_time", "---")
                )
            
            # Update routes table
            routes_table = self.query_one("#routes-table", DataTable)
            routes_table.clear()
            for route in routes_data.get("routes", []):
                routes_table.add_row(
                    route.get("route_id", "---"),
                    route.get("route_name", "---"),
                    str(route.get("assigned_vehicles", "---")),
                    str(route.get("total_gps_points", "---")),
                    f"{route.get('route_length_km', '---')} km" if route.get('route_length_km') else "---",
                    route.get("status", "---")
                )
        except Exception as e:
            self.log_message(f"Table update error: {str(e)}", "ERROR")
    
    def _update_system_details(self, depot_data, passenger_data):
        """Update system details panel"""
        try:
            details = {
                "depot_status": depot_data,
                "passenger_statistics": passenger_data,
                "connection_status": {
                    "api_url": self.api_url,
                    "connected": self.connected,
                    "last_update": self.system_status.last_update.isoformat() if self.system_status.last_update else None
                }
            }
            
            self.query_one("#system-details", Pretty).update(details)
            self.query_one("#passenger-stats", Pretty).update(passenger_data)
        except Exception as e:
            self.log_message(f"Details update error: {str(e)}", "ERROR")
    
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to API log"""
        try:
            log_widget = self.query_one("#api-log", Log)
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_widget.write(f"[{timestamp}] {level}: {message}")
        except:
            pass  # Fail silently if log widget not available
    
    @on(Button.Pressed, "#start-sim")
    async def start_simulator(self):
        """Start the simulator via API"""
        if not self.api_client:
            return
        
        self.log_message("Starting simulator...", "INFO")
        
        result = await self.api_client.post("/simulator/start", {
            "mode": "depot",
            "duration": 120,
            "debug": True
        })
        
        if "error" in result:
            self.log_message(f"Failed to start simulator: {result['error']}", "ERROR")
        else:
            self.log_message(f"Simulator started: {result.get('message', 'Success')}", "SUCCESS")
    
    @on(Button.Pressed, "#stop-sim")
    async def stop_simulator(self):
        """Stop the simulator via API"""
        if not self.api_client:
            return
        
        self.log_message("Stopping simulator...", "INFO")
        
        result = await self.api_client.post("/simulator/stop")
        
        if "error" in result:
            self.log_message(f"Failed to stop simulator: {result['error']}", "ERROR")
        else:
            self.log_message(f"Simulator stopped: {result.get('message', 'Success')}", "SUCCESS")
    
    @on(Button.Pressed, "#refresh")
    async def refresh_data(self):
        """Manually refresh all data"""
        self.log_message("Refreshing data...", "INFO")
        await self._update_data()
    
    async def on_unmount(self) -> None:
        """Cleanup when shutting down"""
        if self.update_timer:
            self.update_timer.stop()
        
        if self.api_client:
            await self.api_client.__aexit__(None, None, None)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArkNet Transit Simulator TUI Dashboard")
    parser.add_argument("--api-url", default="http://127.0.0.1:8090", help="API server URL")
    parser.add_argument("--update-interval", type=float, default=2.0, help="Update interval in seconds")
    
    args = parser.parse_args()
    
    # Create and run the dashboard app
    app = SimulatorDashboard(api_url=args.api_url)
    app.run()


if __name__ == "__main__":
    main()