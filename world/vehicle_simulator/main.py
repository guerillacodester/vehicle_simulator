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
from world.vehicle_simulator.core.standalone_manager import StandaloneFleetManager
from world.vehicle_simulator.providers.config_provider import SelfContainedConfigProvider
from world.vehicle_simulator.simulators.simulator import VehicleSimulator
from world.vehicle_simulator.core.vehicles_depot import VehiclesDepot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VehicleSimulatorApp:
    """Main vehicle simulator application"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or str(current_dir / "config" / "config.ini")
        self.config_provider = SelfContainedConfigProvider(self.config_file)
        self.fleet_manager = StandaloneFleetManager(config_provider=self.config_provider)
        self.depot = None
        self._active_simulator = None  # Track active simulator for cleanup
        
        logger.info("Vehicle Simulator initialized in standalone mode")
    
    def run_enhanced_simulator(self):
        """Run the enhanced vehicle simulator"""
        try:
            logger.info("Starting Enhanced Vehicle Simulator...")
            
            # Create enhanced simulator
            simulator = VehicleSimulator()
            simulator.start()
            
            # Store reference for cleanup
            self._active_simulator = simulator
            
            logger.info("Enhanced Vehicle Simulator started successfully")
            return simulator
            
        except Exception as e:
            logger.error(f"Failed to start enhanced simulator: {e}")
            raise
    
    def run_depot_simulator(self):
        """Run the depot-based vehicle simulator"""
        try:
            logger.info("Starting Depot Vehicle Simulator...")
            
            # Create vehicles depot with route provider
            self.depot = VehiclesDepot(route_provider=self.fleet_manager.route_provider)
            self.depot.start()
            
            # Store reference for cleanup
            self._active_simulator = self.depot
            
            logger.info("Depot Vehicle Simulator started successfully")
            return self.depot
            
        except Exception as e:
            logger.error(f"Failed to start depot simulator: {e}")
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
        description="Standalone Vehicle Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode enhanced                         # Run enhanced simulator continuously
  python main.py --mode depot                           # Run depot simulator continuously
  python main.py --mode enhanced --duration 30          # Run enhanced for 30 seconds
  python main.py --duration 30 --tick-time 1.0          # Run for 30 seconds, 1s ticks
  python main.py --list-routes                          # List available routes
  python main.py --status                               # Show simulator status
  python main.py --config custom_config.ini             # Use custom config
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['enhanced', 'depot'], 
        default='enhanced',
        help='Simulation mode to run (default: enhanced)'
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
        
        # Run simulator based on mode
        simulator = None
        if args.mode == 'enhanced':
            simulator = app.run_enhanced_simulator()
        elif args.mode == 'depot':
            simulator = app.run_depot_simulator()
        
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
                        
                        # Show status every 15 seconds
                        current_time = time.time() - start_time
                        if current_time - last_status_time >= 15:
                            print(f"\n⏰ Time: {current_time:.1f}s")
                            if hasattr(simulator, 'get_status'):
                                print(simulator.get_status())
                            else:
                                print(f"Simulator running ({args.mode} mode)")
                            last_status_time = current_time
                        
                        time.sleep(tick_time)
                        
                except KeyboardInterrupt:
                    print("\n🛑 Simulation interrupted by user")
                    
                print("-" * 60)
                print("✅ Timed Simulation Complete")
                
            else:
                # Continuous simulation mode
                try:
                    print(f"🚌 Vehicle Simulator running in {args.mode} mode (continuous)")
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
