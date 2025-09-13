"""Package entrypoint for clean vehicle simulator.

Usage examples:
  python -m world.vehicle_simulator --mode display
  python -m world.vehicle_simulator --mode depot --duration 60
  python -m world.vehicle_simulator --mode status
"""
from __future__ import annotations
import argparse
import asyncio
import logging
import sys

from .simulator import CleanVehicleSimulator

log = logging.getLogger("vehicle_simulator.entry")


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="python -m world.vehicle_simulator",
                                description="Clean Vehicle Simulator (depot + dispatcher only)")
    p.add_argument('--mode', choices=['display', 'depot', 'status'], default='display', help='Mode to run')
    p.add_argument('--duration', type=float, default=None, help='Duration in seconds (depot mode)')
    p.add_argument('--api-url', type=str, default='http://localhost:8000', help='Fleet Manager API base URL')
    p.add_argument('--debug', action='store_true', help='Enable debug logging')
    return p.parse_args(argv)


async def run_display(sim: CleanVehicleSimulator):
    print("=" * 72)
    print("VEHICLE-DRIVER-ROUTE ASSIGNMENT EVIDENCE")
    print("=" * 72)
    assignments = await sim.get_vehicle_assignments()
    if not assignments:
        print("No assignments available (API may be down or empty).")
        return
    print(f"Found {len(assignments)} assignments:\n")
    for idx, a in enumerate(assignments, 1):
        print(f"Assignment {idx}:")
        print(f"  Vehicle: {a.vehicle_reg_code}")
        print(f"  Driver : {a.driver_name}")
        print(f"  Route  : {a.route_name}")
        route = await sim.get_route_info(a.route_id)
        if route and route.geometry:
            count = route.coordinate_count or (len(route.geometry.get('coordinates', [])) if isinstance(route.geometry, dict) else 'Unknown')
            print(f"  GPS Points: {count}")
        else:
            print("  GPS Points: (none)")
        print()


async def run_status(api_url: str):
    """Fast health check mode - minimal initialization for monitoring."""
    from .core.dispatcher import Dispatcher
    
    # Use simple print for status output (cleaner than complex logging setup)
    # This is appropriate for status mode which is user-facing console output
    def status_print(msg: str):
        print(msg)
    
    def status_header():
        status_print("=" * 72)
        status_print("🚌 ARKNET TRANSIT SYSTEM STATUS")
        status_print("=" * 72)
        status_print("This checks if the vehicle simulation system is ready to operate.")
        status_print("It verifies connections, counts resources, and tests key functions.")
        status_print("")
    
    def status_section(title: str, description: str = ""):
        status_print(f"{title}")
        if description:
            status_print(f"   {description}")
    
    def status_check(result: str, description: str):
        status_print(f"{result}")
        status_print(f"   {description}")
    
    def status_footer(result: str, details: list = None):
        status_print("")
        status_print("=" * 72)
        status_print(result)
        if details:
            for detail in details:
                status_print(f"   {detail}")
        status_print("=" * 72)
    
    status_header()
    
    # Suppress ALL internal logging during status checks for clean output
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    
    # Remove all handlers and set high threshold to suppress internal logs
    for handler in original_handlers:
        root_logger.removeHandler(handler)
    root_logger.setLevel(logging.CRITICAL)
    
    try:
        # Test API connectivity without full initialization
        dispatcher = Dispatcher("StatusChecker", api_url)
        
        # Quick API connection test
        status_section("🔗 Connecting to Fleet Manager...", f"API: {api_url}")
        
        api_available = await dispatcher.initialize()
        
        if not api_available:
            status_check("❌ CONNECTION FAILED", "Fleet Manager database not responding")
            status_print("   • Check that Fleet Manager server is running")
            status_print("   • Verify API URL and network connectivity")
            return 1
        
        status_check("✅ Fleet Manager connected", "Database online and operational")
        status_print("")
        
        # Quick counts without full validation
        status_section("📊 Checking fleet resources...")
        
        try:
            # Get data with minimal logging
            vehicles = await dispatcher.get_vehicle_assignments()
            drivers = await dispatcher.get_driver_assignments()
            
            # Vehicle check
            vehicle_count = len(vehicles) if vehicles else 0
            if vehicle_count > 0:
                status_check(f"✅ Fleet Manager reports {vehicle_count} vehicles available", 
                           "Buses/vans are configured and ready")
            else:
                status_check("❌ No vehicles found in system", 
                           "Fleet needs vehicles to operate routes")
            
            # Driver check
            driver_count = len(drivers) if drivers else 0
            if driver_count > 0:
                available_drivers = len([d for d in drivers if d.status == "available"]) if drivers else 0
                status_check(f"✅ {driver_count} drivers registered, {available_drivers} on duty",
                           "Licensed drivers available for assignments")
                
                if available_drivers == 0:
                    status_print("⚠️  No drivers currently available for service")
            else:
                status_check("❌ No drivers found in system",
                           "Fleet needs licensed drivers to operate")
            
            # Route geometry check
            if vehicles and vehicle_count > 0:
                status_print("")
                status_section("🗺️  Verifying route navigation...")
                
                # Group vehicles by route
                route_assignments = {}
                for vehicle in vehicles:
                    if vehicle.route_id not in route_assignments:
                        route_assignments[vehicle.route_id] = {
                            'vehicles': [],
                            'route_info': None
                        }
                    route_assignments[vehicle.route_id]['vehicles'].append(vehicle)
                
                # Get route info for each route
                for route_id in route_assignments:
                    route_info = await dispatcher.get_route_info(route_id)
                    route_assignments[route_id]['route_info'] = route_info
                
                if route_assignments:
                    for route_id, data in route_assignments.items():
                        route_info = data['route_info']
                        vehicles_on_route = data['vehicles']
                        
                        if route_info and route_info.coordinate_count:
                            route_name = getattr(route_info, 'route_name', f'route {route_id}')
                            # Use human-readable vehicle identifiers
                            vehicle_names = []
                            for v in vehicles_on_route:
                                if v.vehicle_reg_code:
                                    vehicle_names.append(v.vehicle_reg_code)
                                else:
                                    # Fallback to short UUID if reg code not available
                                    short_id = v.vehicle_id[:8] if v.vehicle_id else "unknown"
                                    vehicle_names.append(f"#{short_id}")
                            vehicles_str = ", ".join(vehicle_names)
                            
                            status_check(f"✅ Route <{route_name}> • Vehicles: {vehicles_str}",
                                       f"GPS waypoints loaded • {len(vehicles_on_route)} vehicle(s) assigned")
                        else:
                            route_name = getattr(route_info, 'route_name', f'route {route_id}') if route_info else f'route {route_id}'
                            status_check(f"❌ Route <{route_name}> missing navigation data",
                                       f"{len(vehicles_on_route)} vehicle(s) assigned but no GPS coordinates")
                else:
                    status_check("❌ Route navigation data missing",
                               "Routes need GPS coordinates for vehicle guidance")
            else:
                status_print("")
                status_section("🗺️  Route check skipped (no vehicles to test)")
                
        except Exception as e:
            status_check(f"❌ Fleet resource check failed", 
                        "Unable to verify system configuration")
            return 1
        
        # Final assessment
        if vehicle_count > 0 and driver_count > 0:
            available_drivers = len([d for d in drivers if d.status == "available"]) if drivers else 0
            if available_drivers > 0:
                status_footer("🎉 ARKNET TRANSIT: READY FOR OPERATIONS", [
                    f"• {vehicle_count} vehicles configured",
                    f"• {available_drivers} drivers on duty", 
                    "• Route navigation systems operational",
                    "",
                    "✅ Vehicle simulation system ready to launch!"
                ])
            else:
                status_footer("⚠️  ARKNET TRANSIT: SETUP INCOMPLETE", [
                    "• Fleet and routes are configured",
                    "• No drivers currently assigned to duty",
                    "",
                    "📋 Action required: Schedule drivers before operations"
                ])
        else:
            status_footer("❌ ARKNET TRANSIT: SYSTEM NOT READY", [
                "• Essential fleet resources missing",
                "",
                "📋 Action required: Configure vehicles and drivers"
            ])
        
        return 0
        
    except Exception as e:
        status_print(f"❌ ARKNET TRANSIT: STATUS CHECK FAILED")
        status_print(f"   System error occurred during verification")
        status_print("   Please check system configuration and try again")
        return 1
    finally:
        # Restore original logging configuration
        for handler in original_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(original_level)
        
        try:
            # Suppress shutdown messages completely
            root_logger.setLevel(logging.CRITICAL)
            await dispatcher.shutdown()
        except:
            pass  # Ignore cleanup errors in status mode


class StatusOnlyFilter(logging.Filter):
    """Filter to show only essential status information."""
    def filter(self, record):
        # Only show these specific essential status messages
        essential_patterns = [
            # Section headers
            '═══ DEPOT INVENTORY ═══',
            '═══ VEHICLE STATUS REPORT ═══',
            # Depot status
            'Depot initialization complete',
            'Complete Depot Inventory:',
            '• Total vehicles in depot:',
            '• Active vehicles:',
            '• Inactive vehicles',
            '• Active:',
            '- ZR',  # Vehicle identifiers
            # Vehicle status sections
            '� ACTIVE VEHICLES:',
            '� INACTIVE VEHICLES:',
            '� VEHICLE:',
            '⏸️ VEHICLE:',
            '� Driver:',
            '� Engine:',
            '� GPS:',
            '� FLEET SUMMARY:',
            '� Operational:',
            '� Non-operational:',
            '� Total drivers:',
            'GPS-only mode',
            'DISABLED',
            'ERROR',
            'NO DEVICE',
            'NO ENGINE',
            # Driver status
            '👤 DRIVER STATUS:',
            '� Active:',
            '🔴 Idle:',
            '📊 Total:',
            '� VEHICLE-DRIVER ASSIGNMENTS:',
            '🗺️ Distributing routes',
            '📍',  # Starting coordinates display
            'Starting driver:',
            'boarding vehicle',
            'is ONBOARD',
            'is IDLE',
            'started successfully',
            'stopped successfully', 
            'Driver present but IDLE:',
            'Idle driver',
            'Cannot connect to telemetry server',
            # GPS device status
            'GPSDevice for',
            'started successfully',
            'stopped successfully',
            # Engine status
            'starting engine',
            'stopping engine',
            # System status
            'Shutting down',
            'Shutdown complete'
        ]
        
        # Always allow ERROR and WARNING messages
        if record.levelno >= logging.WARNING:
            return True
            
        # Check if message contains essential status patterns
        message = record.getMessage()
        return any(pattern in message for pattern in essential_patterns)

async def main_async(argv=None):
    args = parse_args(argv)
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(message)s')
    else:
        # Set up colored logging for clean status output
        class ColoredFormatter(logging.Formatter):
            """Custom formatter adding colors to log levels."""
            
            # ANSI color codes
            COLORS = {
                'DEBUG': '\033[36m',    # Cyan
                'INFO': '\033[34m',     # Blue
                'WARNING': '\033[33m',  # Yellow
                'ERROR': '\033[31m',    # Red
                'CRITICAL': '\033[35m', # Magenta
                'RESET': '\033[0m'      # Reset
            }
            
            def format(self, record):
                log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
                reset_color = self.COLORS['RESET']
                
                # Color the levelname
                original_levelname = record.levelname
                record.levelname = f"{log_color}{record.levelname}{reset_color}"
                
                # Format the message
                formatted = super().format(record)
                
                # Restore original levelname
                record.levelname = original_levelname
                
                return formatted
        
        # Create a custom handler with colored formatter
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter('%(asctime)s | %(levelname)s | %(message)s'))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        
        # Apply filter to root logger to show only essential status
        root_logger = logging.getLogger()
        status_filter = StatusOnlyFilter()
        for handler in root_logger.handlers:
            handler.addFilter(status_filter)

    # Status mode doesn't need full simulator initialization
    if args.mode == 'status':
        return await run_status(args.api_url)
    
    # Full initialization for display and depot modes
    sim = CleanVehicleSimulator(api_url=args.api_url)
    if not await sim.initialize():
        print("Initialization failed. Exiting.")
        return 1

    if args.mode == 'display':
        await run_display(sim)
        await sim.shutdown()
        return 0
    else:  # depot mode
        await sim.run(duration=args.duration)
        return 0


def main():  # pragma: no cover
    try:
        exit_code = asyncio.run(main_async())
    except KeyboardInterrupt:
        print("Interrupted by user")
        exit_code = 130
    sys.exit(exit_code)


if __name__ == '__main__':  # pragma: no cover
    main()
