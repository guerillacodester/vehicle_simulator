#!/usr/bin/env python3
"""
Simulator Command Line Client
============================

Command line client for interacting with the ArkNet Transit Simulator API.
Provides comprehensive commands to get detailed information about all simulator components.

Usage:
    cd api/
    python cli.py --help
    
    # System status
    python cli.py status
    python cli.py depot
    python cli.py dispatcher
    
    # Component information
    python cli.py vehicles
    python cli.py drivers 
    python cli.py conductors
    python cli.py gps
    python cli.py passengers
    python cli.py routes
    
    # Simulator control
    python cli.py start --mode depot --duration 60 --debug
    python cli.py stop
    
    # Real-time monitoring
    python cli.py monitor --interval 2
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp


class SimulatorCLI:
    """Command line interface for the simulator API"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:8090"):
        self.api_url = api_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Make GET request to API"""
        if not self.session:
            raise RuntimeError("CLI not initialized")
        
        url = f"{self.api_url}{endpoint}"
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}", "detail": await response.text()}
        except Exception as e:
            return {"error": "Connection failed", "detail": str(e)}
    
    async def post(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make POST request to API"""
        if not self.session:
            raise RuntimeError("CLI not initialized")
        
        url = f"{self.api_url}{endpoint}"
        try:
            async with self.session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}", "detail": await response.text()}
        except Exception as e:
            return {"error": "Connection failed", "detail": str(e)}
    
    def print_json(self, data: Dict[str, Any], title: str = None):
        """Print JSON data with nice formatting"""
        if title:
            print(f"\n🔍 {title}")
            print("=" * (len(title) + 4))
        
        if "error" in data:
            print(f"❌ Error: {data['error']}")
            if "detail" in data:
                print(f"   Detail: {data['detail']}")
        else:
            print(json.dumps(data, indent=2, default=str))
    
    def print_table(self, data: list, headers: list, title: str = None):
        """Print data in table format"""
        if title:
            print(f"\n📊 {title}")
            print("=" * (len(title) + 4))
        
        if not data:
            print("No data available")
            return
        
        # Calculate column widths
        widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in data:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            widths.append(min(max_width, 30))  # Cap at 30 chars
        
        # Print header
        header_row = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_row)
        print("-" * len(header_row))
        
        # Print data rows
        for row in data:
            row_data = []
            for i, cell in enumerate(row):
                if i < len(widths):
                    cell_str = str(cell)[:widths[i]]  # Truncate if too long
                    row_data.append(cell_str.ljust(widths[i]))
            print(" | ".join(row_data))
    
    async def cmd_status(self):
        """Get overall system status"""
        print("🚀 ArkNet Transit Simulator - System Status")
        print("=" * 50)
        
        # Simulator status
        sim_status = await self.get("/simulator/status")
        print(f"\n📡 Simulator Status:")
        if "error" not in sim_status:
            status = sim_status.get("status", "unknown")
            print(f"   Status: {status}")
            if sim_status.get("uptime_seconds"):
                uptime = sim_status["uptime_seconds"]
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                seconds = int(uptime % 60)
                print(f"   Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            if sim_status.get("mode"):
                print(f"   Mode: {sim_status['mode']}")
            if sim_status.get("pid"):
                print(f"   PID: {sim_status['pid']}")
        else:
            print(f"   ❌ {sim_status['error']}")
        
        # Health check
        health = await self.get("/health")
        print(f"\n🏥 Health Check:")
        if "error" not in health:
            print(f"   Status: {health.get('status', 'unknown')}")
            print(f"   Timestamp: {health.get('timestamp', 'unknown')}")
        else:
            print(f"   ❌ {health['error']}")
    
    async def cmd_depot(self):
        """Get depot status"""
        depot_status = await self.get("/depot/status")
        self.print_json(depot_status, "Depot Status")
        
        # Also get depot manager
        manager_status = await self.get("/depot/manager")
        self.print_json(manager_status, "Depot Manager")
    
    async def cmd_dispatcher(self):
        """Get dispatcher status"""
        dispatcher_status = await self.get("/dispatcher/status")
        self.print_json(dispatcher_status, "Dispatcher Status")
    
    async def cmd_vehicles(self):
        """Get vehicles information"""
        vehicles_data = await self.get("/vehicles")
        self.print_json(vehicles_data, "All Vehicles")
        
        # Print summary table if data exists
        if vehicles_data.get("vehicles"):
            table_data = []
            for vehicle in vehicles_data["vehicles"]:
                row = [
                    vehicle.get("vehicle_id", "---"),
                    vehicle.get("driver_name", "---"),
                    vehicle.get("route_id", "---"),
                    vehicle.get("driver_status", "---"),
                    vehicle.get("engine_status", "---"),
                    vehicle.get("gps_status", "---")
                ]
                table_data.append(row)
            
            self.print_table(
                table_data,
                ["Vehicle ID", "Driver", "Route", "Status", "Engine", "GPS"],
                "Vehicles Summary"
            )
    
    async def cmd_drivers(self):
        """Get drivers information"""
        drivers_data = await self.get("/drivers")
        self.print_json(drivers_data, "All Drivers")
        
        # Print summary table if data exists
        if drivers_data.get("drivers"):
            table_data = []
            for driver in drivers_data["drivers"]:
                row = [
                    driver.get("driver_id", "---"),
                    driver.get("driver_name", "---"),
                    driver.get("current_state", "---"),
                    driver.get("vehicle_id", "---"),
                    driver.get("route_name", "---")
                ]
                table_data.append(row)
            
            self.print_table(
                table_data,
                ["Driver ID", "Name", "State", "Vehicle", "Route"],
                "Drivers Summary"
            )
    
    async def cmd_conductors(self):
        """Get conductors information"""
        conductors_data = await self.get("/conductors")
        self.print_json(conductors_data, "All Conductors")
        
        # Print summary table if data exists
        if conductors_data.get("conductors"):
            table_data = []
            for conductor in conductors_data["conductors"]:
                row = [
                    conductor.get("conductor_id", "---"),
                    conductor.get("conductor_name", "---"),
                    conductor.get("conductor_state", "---"),
                    conductor.get("vehicle_id", "---"),
                    f"{conductor.get('passengers_on_board', 0)}/{conductor.get('capacity', 0)}"
                ]
                table_data.append(row)
            
            self.print_table(
                table_data,
                ["Conductor ID", "Name", "State", "Vehicle", "Passengers"],
                "Conductors Summary"
            )
    
    async def cmd_gps(self):
        """Get GPS devices and telemetry"""
        gps_devices = await self.get("/gps/devices")
        self.print_json(gps_devices, "GPS Devices")
        
        telemetry = await self.get("/gps/telemetry")
        self.print_json(telemetry, "GPS Telemetry")
        
        # Print devices summary table if data exists
        if gps_devices.get("devices"):
            table_data = []
            for device in gps_devices["devices"]:
                row = [
                    device.get("device_id", "---"),
                    device.get("vehicle_id", "---"),
                    device.get("current_state", "---"),
                    "Yes" if device.get("transmitter_connected") else "No",
                    device.get("last_transmission", "---")[:19] if device.get("last_transmission") else "---"
                ]
                table_data.append(row)
            
            self.print_table(
                table_data,
                ["Device ID", "Vehicle", "State", "Connected", "Last Update"],
                "GPS Devices Summary"
            )
    
    async def cmd_passengers(self):
        """Get passenger information"""
        passenger_stats = await self.get("/passengers/stats")
        self.print_json(passenger_stats, "Passenger Statistics")
        
        active_passengers = await self.get("/passengers/active")
        self.print_json(active_passengers, "Active Passengers")
        
        # Print passengers summary table if data exists
        if active_passengers.get("passengers"):
            table_data = []
            for passenger in active_passengers["passengers"]:
                row = [
                    passenger.get("passenger_id", "---"),
                    passenger.get("status", "---"),
                    passenger.get("origin", "---")[:20] if passenger.get("origin") else "---",
                    passenger.get("destination", "---")[:20] if passenger.get("destination") else "---",
                    passenger.get("spawn_time", "---")[:19] if passenger.get("spawn_time") else "---"
                ]
                table_data.append(row)
            
            self.print_table(
                table_data,
                ["Passenger ID", "Status", "Origin", "Destination", "Spawn Time"],
                "Active Passengers Summary"
            )
    
    async def cmd_routes(self):
        """Get routes information"""
        routes_data = await self.get("/routes")
        self.print_json(routes_data, "All Routes")
        
        # Print routes summary table if data exists
        if routes_data.get("routes"):
            table_data = []
            for route in routes_data["routes"]:
                row = [
                    route.get("route_id", "---"),
                    route.get("route_name", "---"),
                    str(route.get("assigned_vehicles", "---")),
                    str(route.get("total_gps_points", "---")),
                    f"{route.get('route_length_km', '---')} km" if route.get('route_length_km') else "---",
                    route.get("status", "---")
                ]
                table_data.append(row)
            
            self.print_table(
                table_data,
                ["Route ID", "Name", "Vehicles", "GPS Points", "Length", "Status"],
                "Routes Summary"
            )
    
    async def cmd_start(self, mode: str = "depot", duration: int = 60, debug: bool = False):
        """Start the simulator"""
        print(f"🚀 Starting simulator (mode={mode}, duration={duration}s, debug={debug})")
        
        result = await self.post("/simulator/start", {
            "mode": mode,
            "duration": duration,
            "debug": debug
        })
        
        if "error" in result:
            print(f"❌ Failed to start: {result['error']}")
            if "detail" in result:
                print(f"   Detail: {result['detail']}")
        else:
            print(f"✅ {result.get('message', 'Simulator started successfully')}")
            if result.get('data'):
                print(f"   PID: {result['data'].get('pid')}")
                print(f"   Mode: {result['data'].get('mode')}")
                print(f"   Duration: {result['data'].get('duration')}s")
    
    async def cmd_stop(self):
        """Stop the simulator"""
        print("🛑 Stopping simulator...")
        
        result = await self.post("/simulator/stop")
        
        if "error" in result:
            print(f"❌ Failed to stop: {result['error']}")
            if "detail" in result:
                print(f"   Detail: {result['detail']}")
        else:
            print(f"✅ {result.get('message', 'Simulator stopped successfully')}")
    
    async def cmd_monitor(self, interval: float = 2.0):
        """Monitor system status in real-time"""
        print(f"📊 Monitoring system status (refresh every {interval}s)")
        print("Press Ctrl+C to stop monitoring")
        print("=" * 60)
        
        try:
            while True:
                # Clear screen and show timestamp
                print("\033[2J\033[H")  # Clear screen
                print(f"📊 ArkNet Transit Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 60)
                
                # Get key metrics
                sim_status = await self.get("/simulator/status")
                vehicles = await self.get("/vehicles")
                drivers = await self.get("/drivers")
                passengers = await self.get("/passengers/stats")
                
                # Display compact status
                print(f"Simulator: {sim_status.get('status', 'unknown').upper()}")
                if sim_status.get('uptime_seconds'):
                    uptime = sim_status['uptime_seconds']
                    hours = int(uptime // 3600)
                    minutes = int((uptime % 3600) // 60)
                    seconds = int(uptime % 60)
                    print(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
                print(f"Vehicles: {vehicles.get('active_vehicles', 0)}/{vehicles.get('total_vehicles', 0)}")
                print(f"Drivers: {drivers.get('active_drivers', 0)}/{drivers.get('total_drivers', 0)}")
                print(f"Passengers: {passengers.get('total_spawned', 0)} spawned, {passengers.get('active_passengers', 0)} active")
                
                print(f"\nNext update in {interval}s... (Ctrl+C to stop)")
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ArkNet Transit Simulator Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  status       Get overall system status
  depot        Get depot and depot manager status
  dispatcher   Get dispatcher status
  vehicles     Get all vehicles information
  drivers      Get all drivers information
  conductors   Get all conductors information
  gps          Get GPS devices and telemetry
  passengers   Get passenger statistics and active passengers
  routes       Get routes information
  start        Start the simulator
  stop         Stop the simulator
  monitor      Monitor system status in real-time

Examples:
  python cli.py status
  python cli.py start --mode depot --duration 120 --debug
  python cli.py vehicles
  python cli.py monitor --interval 1
        """
    )
    
    parser.add_argument("command", 
                       choices=["status", "depot", "dispatcher", "vehicles", "drivers", 
                               "conductors", "gps", "passengers", "routes", "start", "stop", "monitor"],
                       help="Command to execute")
    parser.add_argument("--api-url", default="http://127.0.0.1:8090", help="API server URL")
    
    # Start command options
    parser.add_argument("--mode", default="depot", help="Simulator mode (for start command)")
    parser.add_argument("--duration", type=int, default=60, help="Simulation duration in seconds (for start command)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (for start command)")
    
    # Monitor command options
    parser.add_argument("--interval", type=float, default=2.0, help="Update interval for monitoring (seconds)")
    
    args = parser.parse_args()
    
    # Execute command
    async with SimulatorCLI(args.api_url) as cli:
        if args.command == "status":
            await cli.cmd_status()
        elif args.command == "depot":
            await cli.cmd_depot()
        elif args.command == "dispatcher":
            await cli.cmd_dispatcher()
        elif args.command == "vehicles":
            await cli.cmd_vehicles()
        elif args.command == "drivers":
            await cli.cmd_drivers()
        elif args.command == "conductors":
            await cli.cmd_conductors()
        elif args.command == "gps":
            await cli.cmd_gps()
        elif args.command == "passengers":
            await cli.cmd_passengers()
        elif args.command == "routes":
            await cli.cmd_routes()
        elif args.command == "start":
            await cli.cmd_start(args.mode, args.duration, args.debug)
        elif args.command == "stop":
            await cli.cmd_stop()
        elif args.command == "monitor":
            await cli.cmd_monitor(args.interval)


if __name__ == "__main__":
    asyncio.run(main())