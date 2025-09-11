#!/usr/bin/env python3
"""
Vehicle Simulator Main Entry Point
---------------------------------
Standalone vehicle simulation system completely decoupled from fleet_manager.
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent.parent))  # For root level imports

import argparse
import time
from typing import Optional

# Vehicle simulator imports
from world.vehicle_simulator.providers.data_provider import FleetDataProvider
from world.vehicle_simulator.config.config_loader import ConfigLoader
from world.vehicle_simulator.simulators.simulator import VehicleSimulator
from world.vehicle_simulator.core.depot_manager import DepotManager

# New logging system
from world.vehicle_simulator.utils.logging_system import (
    get_logger, configure_logging, LogLevel, LogComponent, get_logging_system, LoggingMode
)
from world.vehicle_simulator.config.logging_config import LoggingConfig


class VehicleSimulatorApp:
    """Main vehicle simulator application"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or str(current_dir / "config" / "config.ini")
        
        # Initialize logging system first
        self._setup_logging()
        self.logger = get_logger(LogComponent.MAIN)
        
        # Initialize new architecture components
        self.config_loader = ConfigLoader(self.config_file)
        self.config = self.config_loader.get_all_config()
        
        # Initialize data provider for database access
        try:
            self.data_provider = FleetDataProvider()
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.warning(f"Database connection failed: {e}")
            self.data_provider = None
        
        # Note: Legacy standalone manager removed - using depot manager only
        
        self.depot = None
        self._active_simulator = None  # Track active simulator for cleanup
        
        # Use debug logging for internal initialization
        self.logger.debug("Vehicle Simulator initialized with database-driven architecture")
    
    def _setup_logging(self):
        """Setup the logging system based on configuration."""
        try:
            # Load logging configuration
            logging_config = LoggingConfig()
            
            # Configure the logging system
            configure_logging(
                level=logging_config.get_log_level(),
                verbose=logging_config.is_verbose(),
                console=logging_config.is_console_enabled(),
                file_logging=logging_config.is_file_enabled(),
                structured=logging_config.is_structured_enabled(),
                log_dir=logging_config.get_log_directory()
            )
            
            # Log system initialization
            get_logging_system().log_system_info()
            
        except Exception as e:
            # Fallback to basic logging if configuration fails
            configure_logging(level=LogLevel.INFO, verbose=False)
            print(f"Warning: Failed to configure logging system, using defaults: {e}")
    
    def run_simulator(self):
        """Run the vehicle simulator"""
        try:
            # Create simulator
            simulator = VehicleSimulator()
            simulator.start()
            
            # Store reference for cleanup
            self._active_simulator = simulator
            
            # Success message handled by simulator
            return simulator
            
        except Exception as e:
            self.logger.error(f"Failed to start simulator: {e}")
            raise
    
    def run_depot_simulator(self, tick_time: float = 1.0):
        """Run the depot-based vehicle simulator with Navigator"""
        try:
            self.logger.info("Starting Database-Driven Depot Simulator...")
            self.logger.info("   Using database for fleet data")
            self.logger.info("   Navigator provides realistic route following")
            self.logger.info(f"   Tick time: {tick_time} seconds")
            
            if not self.data_provider:
                self.logger.warning("   Database unavailable - using fallback mode")
                enable_timetable = False
            else:
                enable_timetable = self.config['simulation'].get('enable_timetable', True)
                self.logger.info(f"   Timetable operations: {'enabled' if enable_timetable else 'disabled'}")
            
            # Create depot manager with new architecture
            self.depot = DepotManager(
                tick_time=tick_time,
                enable_timetable=enable_timetable
            )
            self.depot.start()
            
            # Store reference for cleanup
            self._active_simulator = self.depot
            
            self.logger.info("✅ Database-Driven Depot Simulator started successfully")
            
            # Show initial detailed status
            self.logger.info("=" * 60)
            self.logger.info("📊 INITIAL SYSTEM STATUS")
            self.logger.info("=" * 60)
            if hasattr(self.depot, 'get_detailed_schedule_status'):
                status = self.depot.get_detailed_schedule_status()
                for line in status.split('\n'):
                    if line.strip():
                        self.logger.info(line)
            self.logger.info("=" * 60)
            
            return self.depot
            
        except Exception as e:
            self.logger.error(f"Failed to start depot simulator: {e}")
            # Fallback to basic simulator for GPS testing
            self.logger.info("Falling back to basic vehicle simulator with GPS transmission...")
            try:
                self.logger.info("🚌 Starting Basic Vehicle Simulator (GPS Fallback Mode)...")
                self.logger.info("   📡 GPS transmission enabled")
                self.logger.info(f"   ⏱️ Tick time: {tick_time} seconds")
                
                # Load vehicle data first, then create simulator
                from world.vehicle_simulator.simulators.simulator import VehicleSimulator
                
                # Try to get vehicle data from data provider
                vehicle_data = []
                if hasattr(self, 'data_provider') and self.data_provider.is_api_available():
                    try:
                        vehicles = self.data_provider.get_vehicles()
                        vehicle_data = vehicles[:4]  # Limit to 4 vehicles for basic simulation
                        self.logger.info(f"   📊 Using {len(vehicle_data)} vehicles from API")
                    except Exception as e:
                        self.logger.warning(f"Could not get vehicles from API: {e}")
                
                # NO FAKE DATA - fail if no real API data
                if not vehicle_data:
                    self.logger.error("❌ NO VEHICLE DATA AVAILABLE FROM API")
                    self.logger.error("❌ Cannot run simulator without real vehicle data")
                    raise Exception("No vehicle data available - API connection failed")
                
                simulator = VehicleSimulator(tick_time=tick_time, enable_gps=True, vehicle_data=vehicle_data)
                simulator.start()
                
                # Store reference for cleanup
                self._active_simulator = simulator
                
                self.logger.info("✅ Basic Vehicle Simulator started with GPS transmission")
                return simulator
                
            except Exception as fallback_error:
                self.logger.error(f"Fallback simulator also failed: {fallback_error}")
                raise
    
    def list_available_routes(self):
        """List all available routes"""
        routes = self.fleet_manager.list_available_routes()
        self.logger.info(f"Available routes: {routes}")
        return routes
    
    def get_simulation_status(self):
        """Get current simulation status"""
        config = self.config_provider.get_simulation_config()
        gps_config = self.config_provider.get_gps_config()
        
        status = {
            'mode': 'standalone',
            'routes_available': len(self.fleet_manager.list_available_routes()),
            'tick_time': config.get('tick_time', 1.0),
            'gps_enabled': gps_config.get('enable_transmission', True),
            'gps_server': gps_config.get('server_url', 'ws://localhost:5000/')
        }
        
        return status
    
    def stop(self):
        """Stop all simulation components"""
        self.logger.info("Stopping Vehicle Simulator...")
        
        if self.depot:
            self.depot.stop()
        
        # Stop any active simulators
        if hasattr(self, '_active_simulator') and self._active_simulator:
            if hasattr(self._active_simulator, 'stop'):
                self._active_simulator.stop()
                self.logger.info("Active simulator stopped")
        
        self.logger.info("Vehicle Simulator stopped")


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Vehicle Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                 # Run basic simulator continuously
  python main.py --mode depot                   # Run depot with Navigator
  python main.py --duration 30                  # Run for 30 seconds
  python main.py --mode depot --duration 60     # Run depot mode for 60s
  python main.py --duration 60 --tick-time 0.5  # Run 60s with 0.5s updates
  python main.py --list-routes                  # List available routes
  python main.py --status                       # Show simulator status
  python main.py --config custom_config.ini     # Use custom config
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['depot'], 
        default='depot',
        help='Simulation mode: depot=Navigator route following with database-driven operations (basic mode deprecated)'
    )
    
    parser.add_argument(
        '--config',
        help='Configuration file path (default: config/config.ini)'
    )
    
    parser.add_argument(
        '--list-routes',
        action='store_true',
        help='List available routes and exit'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show simulator status and exit'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging with simplified status output'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging with detailed output (implies --debug)'
    )
    
    parser.add_argument(
        '--fleet-status',
        action='store_true',
        help='Show detailed fleet status from Fleet Manager API and exit'
    )
    
    parser.add_argument(
        '--duration',
        type=float,
        help='Simulation duration in seconds (default: run continuously until Ctrl+C)'
    )
    
    parser.add_argument(
        '--tick-time',
        type=float,
        default=1.0,
        help='Time between simulation ticks in seconds (default: 1.0)'
    )
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging modes
    if args.verbose:
        # Verbose mode: enable all detailed output
        get_logging_system().set_logging_mode(LoggingMode.VERBOSE)
    elif args.debug:
        # Debug mode: clean simplified status output
        get_logging_system().set_logging_mode(LoggingMode.DEBUG)
    else:
        # Normal mode: basic info only
        get_logging_system().set_logging_mode(LoggingMode.NORMAL)
    
    try:
        # Initialize simulator app
        app = VehicleSimulatorApp(args.config)
        
        # Handle utility commands
        main_logger = get_logger(LogComponent.MAIN)
        if args.list_routes:
            routes = app.list_available_routes()
            if routes:
                main_logger.info("Available Routes:")
                for route in routes:
                    info = app.fleet_manager.get_route_info(route)
                    main_logger.info(f"  - {route}: {info.get('name', 'No description') if info else 'No info'}")
            else:
                main_logger.info("No routes available")
            return
        
        if args.status:
            status = app.get_simulation_status()
            main_logger.info("Vehicle Simulator Status:")
            for key, value in status.items():
                main_logger.info(f"  {key}: {value}")
            return
        
        if args.fleet_status:
            main_logger.info("Fleet Status feature requires Fleet Manager API to be running")
            main_logger.info("Start the Fleet Manager API first:")
            main_logger.info("  python world/fleet_manager/api/start_fleet_manager.py")
            main_logger.info("Then access: http://localhost:8000/api/v1/fleet/detailed_status")
            return
        
        # Run depot simulator (basic mode deprecated)
        simulator = app.run_depot_simulator(args.tick_time)
        
        # Handle timed simulation
        if simulator:
            if args.duration:
                # Timed simulation mode
                tick_time = args.tick_time or 1.0
                duration = args.duration
                
                main_logger.info("=" * 60)
                main_logger.info("🚌 Vehicle Simulator - Timed Mode")
                main_logger.info("=" * 60)
                main_logger.info(f"⏱️  Update Interval: {tick_time} seconds")
                main_logger.info(f"⏰ Duration: {duration} seconds")
                main_logger.info(f"🚀 Mode: {args.mode}")
                main_logger.info("-" * 60)
                
                start_time = time.time()
                last_status_time = 0
                
                try:
                    while time.time() - start_time < duration:
                        # Update simulator if it has an update method
                        if hasattr(simulator, 'update'):
                            simulator.update()
                        
                        # Show detailed status every 15 seconds
                        current_time = time.time() - start_time
                        if current_time - last_status_time >= 15:
                            main_logger.info(f"⏰ Time: {current_time:.1f}s")
                            if hasattr(simulator, 'get_detailed_schedule_status'):
                                status = simulator.get_detailed_schedule_status()
                                for line in status.split('\n'):
                                    if line.strip():
                                        main_logger.info(line)
                            elif hasattr(simulator, 'get_status'):
                                status = simulator.get_status()
                                for line in status.split('\n'):
                                    if line.strip():
                                        main_logger.info(line)
                            else:
                                main_logger.info("Simulator running")
                            last_status_time = current_time
                        
                        time.sleep(tick_time)
                        
                except KeyboardInterrupt:
                    main_logger.info("🛑 Simulation interrupted by user")
                    
                main_logger.info("-" * 60)
                main_logger.info("✅ Timed Simulation Complete")
                
            else:
                # Continuous simulation mode
                try:
                    main_logger.info(f"🚌 Vehicle Simulator running continuously ({args.mode} mode)")
                    main_logger.info("Press Ctrl+C to stop...")
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    get_logger(LogComponent.MAIN).info("Received interrupt signal")
        
        # Clean shutdown
        app.stop()
        
        # Give threads time to properly shutdown
        time.sleep(0.5)
        
    except Exception as e:
        get_logger(LogComponent.MAIN).error(f"Vehicle Simulator failed: {e}")
        if 'app' in locals():
            app.stop()
        sys.exit(1)
    except KeyboardInterrupt:
        get_logger(LogComponent.MAIN).info("Received interrupt signal")
        if 'app' in locals():
            app.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
