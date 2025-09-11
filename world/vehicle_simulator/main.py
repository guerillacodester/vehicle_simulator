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

import logging
import argparse
import time
from typing import Optional

# Vehicle simulator imports
from world.vehicle_simulator.providers.data_provider import FleetDataProvider
from world.vehicle_simulator.config.config_loader import ConfigLoader
from world.vehicle_simulator.simulators.simulator import VehicleSimulator
from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.standalone_manager import StandaloneFleetManager
from world.vehicle_simulator.providers.config_provider import SelfContainedConfigProvider

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduced default level
    format='%(message)s'     # Simplified format
)
logger = logging.getLogger(__name__)

# Only show INFO for main simulator messages
logging.getLogger('world.vehicle_simulator.main').setLevel(logging.INFO)
logging.getLogger('world.vehicle_simulator.simulators.simulator').setLevel(logging.INFO)


class VehicleSimulatorApp:
    """Main vehicle simulator application"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or str(current_dir / "config" / "config.ini")
        
        # Initialize new architecture components
        self.config_loader = ConfigLoader(self.config_file)
        self.config = self.config_loader.get_all_config()
        
        # Initialize data provider for database access
        try:
            self.data_provider = FleetDataProvider()
            logger.info("Database connection established")
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
            self.data_provider = None
        
        # Initialize config provider and fleet manager for legacy compatibility
        self.config_provider = SelfContainedConfigProvider(self.config_file)
        self.fleet_manager = StandaloneFleetManager(config_provider=self.config_provider)
        
        self.depot = None
        self._active_simulator = None  # Track active simulator for cleanup
        
        # Use debug logging for internal initialization
        logger.debug("Vehicle Simulator initialized with database-driven architecture")
    
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
            logger.error(f"Failed to start simulator: {e}")
            raise
    
    def run_depot_simulator(self, tick_time: float = 1.0):
        """Run the depot-based vehicle simulator with Navigator"""
        try:
            print("🏭 Starting Database-Driven Depot Simulator...")
            print("   �️ Using database for fleet data")
            print("   📍 Navigator provides realistic route following")
            print(f"   ⏱️ Tick time: {tick_time} seconds")
            
            if not self.data_provider:
                print("   ⚠️ Database unavailable - using fallback mode")
                enable_timetable = False
            else:
                enable_timetable = self.config['simulation'].get('enable_timetable', True)
                print(f"   📅 Timetable operations: {'enabled' if enable_timetable else 'disabled'}")
            
            # Create depot manager with new architecture
            self.depot = DepotManager(
                tick_time=tick_time,
                enable_timetable=enable_timetable
            )
            self.depot.start()
            
            # Store reference for cleanup
            self._active_simulator = self.depot
            
            print("✅ Database-Driven Depot Simulator started successfully")
            
            # Show initial detailed status
            print("\n" + "=" * 60)
            print("📊 INITIAL SYSTEM STATUS")
            print("=" * 60)
            if hasattr(self.depot, 'get_detailed_schedule_status'):
                print(self.depot.get_detailed_schedule_status())
            print("=" * 60)
            
            return self.depot
            
        except Exception as e:
            logger.error(f"Failed to start depot simulator: {e}")
            # Fallback to basic simulator for GPS testing
            logger.info("Falling back to basic vehicle simulator with GPS transmission...")
            try:
                print("🚌 Starting Basic Vehicle Simulator (GPS Fallback Mode)...")
                print("   📡 GPS transmission enabled")
                print(f"   ⏱️ Tick time: {tick_time} seconds")
                
                # Create basic simulator with GPS enabled
                from world.vehicle_simulator.simulators.simulator import VehicleSimulator
                simulator = VehicleSimulator(tick_time=tick_time, enable_gps=True)
                simulator.start()
                
                # Store reference for cleanup
                self._active_simulator = simulator
                
                print("✅ Basic Vehicle Simulator started with GPS transmission")
                return simulator
                
            except Exception as fallback_error:
                logger.error(f"Fallback simulator also failed: {fallback_error}")
                raise
    
    def list_available_routes(self):
        """List all available routes"""
        routes = self.fleet_manager.list_available_routes()
        logger.info(f"Available routes: {routes}")
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
        logger.info("Stopping Vehicle Simulator...")
        
        if self.depot:
            self.depot.stop()
        
        # Stop any active simulators
        if hasattr(self, '_active_simulator') and self._active_simulator:
            if hasattr(self._active_simulator, 'stop'):
                self._active_simulator.stop()
                logger.info("Active simulator stopped")
        
        logger.info("Vehicle Simulator stopped")


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
        help='Enable debug logging'
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
    
    # Setup debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        # Restore detailed format for debug mode
        for handler in logging.getLogger().handlers:
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    else:
        # Quiet mode - only show essential messages
        logging.getLogger('world.vehicle_simulator.core').setLevel(logging.WARNING)
        logging.getLogger('world.vehicle_simulator.vehicle').setLevel(logging.WARNING)
        logging.getLogger('world.vehicle_simulator.providers').setLevel(logging.WARNING)
    
    try:
        # Initialize simulator app
        app = VehicleSimulatorApp(args.config)
        
        # Handle utility commands
        if args.list_routes:
            routes = app.list_available_routes()
            if routes:
                print("\nAvailable Routes:")
                for route in routes:
                    info = app.fleet_manager.get_route_info(route)
                    print(f"  - {route}: {info.get('name', 'No description') if info else 'No info'}")
            else:
                print("No routes available")
            return
        
        if args.status:
            status = app.get_simulation_status()
            print("\nVehicle Simulator Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
            return
        
        # Run depot simulator (basic mode deprecated)
        simulator = app.run_depot_simulator(args.tick_time)
        
        # Handle timed simulation
        if simulator:
            if args.duration:
                # Timed simulation mode
                tick_time = args.tick_time or 1.0
                duration = args.duration
                
                print("=" * 60)
                print("🚌 Vehicle Simulator - Timed Mode")
                print("=" * 60)
                print(f"⏱️  Update Interval: {tick_time} seconds")
                print(f"⏰ Duration: {duration} seconds")
                print(f"🚀 Mode: {args.mode}")
                print("-" * 60)
                
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
                            print(f"\n⏰ Time: {current_time:.1f}s")
                            if hasattr(simulator, 'get_detailed_schedule_status'):
                                print(simulator.get_detailed_schedule_status())
                            elif hasattr(simulator, 'get_status'):
                                print(simulator.get_status())
                            else:
                                print("Simulator running")
                            last_status_time = current_time
                        
                        time.sleep(tick_time)
                        
                except KeyboardInterrupt:
                    print("\n🛑 Simulation interrupted by user")
                    
                print("-" * 60)
                print("✅ Timed Simulation Complete")
                
            else:
                # Continuous simulation mode
                try:
                    print(f"🚌 Vehicle Simulator running continuously ({args.mode} mode)")
                    print("Press Ctrl+C to stop...")
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal")
        
        # Clean shutdown
        app.stop()
        
        # Give threads time to properly shutdown
        time.sleep(0.5)
        
    except Exception as e:
        logger.error(f"Vehicle Simulator failed: {e}")
        if 'app' in locals():
            app.stop()
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        if 'app' in locals():
            app.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
