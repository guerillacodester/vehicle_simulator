#!/usr/bin/env python3
"""
VehiclesDepot
---------------
Database-driven fleet depot that manages real-time vehicle operations.
Uses FleetDataProvider to get all fleet data from database and TimetableScheduler
for schedule-driven vehicle dispatch. Eliminates vehicles.json dependency.
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any

# Vehicle simulation components
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.engine.engine_block import Engine
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle_simulator.vehicle.engine.sim_speed_model import load_speed_model
from world.vehicle_simulator.vehicle.gps_device.rxtx_buffer import RxTxBuffer
from world.vehicle_simulator.vehicle.driver.navigation.navigator import Navigator
from world.vehicle_simulator.vehicle.vahicle_object import VehicleState

# New architecture components
from world.vehicle_simulator.providers.data_provider import FleetDataProvider
from world.vehicle_simulator.core.timetable_scheduler import TimetableScheduler
from world.vehicle_simulator.config.config_loader import ConfigLoader

# Create logger for this module
logger = logging.getLogger(__name__)

class VehiclesDepot:
    def __init__(self, tick_time: float = 1.0, 
                 route_provider=None,  # Legacy compatibility - will be replaced
                 enable_timetable: bool = True):
        """
        Initialize database-driven vehicles depot.
        
        Args:
            tick_time: Time interval for vehicle updates
            route_provider: Legacy parameter - ignored in new architecture
            enable_timetable: Whether to use timetable-driven operations
        """
        # Initialize core properties
        self.tick_time = tick_time
        self.enable_timetable = enable_timetable
        self.vehicles = {}
        self.running = False
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize new architecture components
        try:
            # Load configuration
            self.config_loader = ConfigLoader()
            self.config = self.config_loader.get_all_config()
            
            # Initialize data provider (connects to database with Socket.IO monitoring)
            server_url = self.config.get('fleet', {}).get('api_url', 'http://localhost:8000')
            self.data_provider = FleetDataProvider(server_url)
            
            # Add API status callback
            self.data_provider.api_monitor.add_status_callback(self._on_api_status_change)
            
            # Initialize timetable scheduler if enabled
            if self.enable_timetable:
                precision = self.config['simulation'].get('schedule_precision_seconds', 30)
                # Default to capacity-based scheduling (ZR van style)
                schedule_mode = self.config['simulation'].get('schedule_mode', 'capacity')
                default_capacity = self.config['simulation'].get('default_vehicle_capacity', 11)
                
                self.scheduler = TimetableScheduler(
                    self.data_provider, 
                    precision, 
                    default_mode=schedule_mode,
                    default_capacity=default_capacity
                )
            else:
                self.scheduler = None
            
            # Load fleet data from database (will wait for API availability)
            self._load_fleet_data()
            
            # Create vehicle instances
            self._create_vehicle_instances()
            
            # Load schedule if timetable is enabled
            if self.scheduler:
                self._setup_timetable_operations()
            
            logger.info("✅ VehiclesDepot initialized with database-driven architecture")
            
        except Exception as e:
            logger.error(f"Failed to initialize VehiclesDepot: {e}")
            raise

    def _on_api_status_change(self, status):
        """Handle API status changes"""
        if status.is_connected:
            logger.info(f"🔌 Fleet Manager API connected (response: {status.response_time:.3f}s)")
        else:
            logger.warning(f"⚠️ Fleet Manager API disconnected: {status.error}")

    # ==================== NEW DATABASE-DRIVEN METHODS ====================

    def _load_fleet_data(self):
        """Load complete fleet data from database"""
        try:
            logger.info("Loading fleet data from database...")
            
            # Wait for API connection (up to 10 seconds)
            max_wait = 10
            wait_time = 0
            while not self.data_provider.is_api_available() and wait_time < max_wait:
                logger.info(f"Waiting for API connection... ({wait_time}s/{max_wait}s)")
                time.sleep(1)
                wait_time += 1
            
            # Check API availability after waiting
            if not self.data_provider.is_api_available():
                logger.warning("Fleet Manager API not available after waiting - using empty fleet data")
                # Create empty fleet data structure
                self.fleet_data = {
                    'vehicles': [],
                    'routes': {},
                    'schedules': [],
                    'timetables': [],
                    'drivers': [],
                    'services': [],
                    'depots': []
                }
                self.routes = {}
                return
            
            logger.info("✅ API connected! Loading fleet data...")
            self.fleet_data = self.data_provider.get_all_fleet_data()
            
            # Log what we loaded
            vehicles_count = len(self.fleet_data['vehicles'])
            routes_count = len(self.fleet_data['routes'])
            schedules_count = len(self.fleet_data['schedules'])
            
            logger.info(f"Loaded {vehicles_count} vehicles, {routes_count} routes, {schedules_count} schedules")
            
            # Store routes for easy access
            self.routes = self.fleet_data['routes']
            
        except Exception as e:
            logger.error(f"Failed to load fleet data: {e}")
            # Create fallback empty structure
            self.fleet_data = {
                'vehicles': [],
                'routes': {},
                'schedules': [],
                'timetables': [],
                'drivers': [],
                'services': [],
                'depots': []
            }
            self.routes = {}

    def _create_vehicle_instances(self):
        """Create vehicle instances from database data"""
        try:
            logger.info("Creating vehicle instances from database data...")
            
            for vehicle_data in self.fleet_data['vehicles']:
                vehicle_id = vehicle_data['id']
                
                # For simulation purposes, activate all vehicles regardless of database status
                # In production, this would respect the database active status
                if not vehicle_data.get('active', False):
                    logger.info(f"Vehicle {vehicle_id} is inactive in database, activating for simulation")
                    vehicle_data['active'] = True  # Force activate for simulation
                
                # Create vehicle configuration from database data
                vehicle_config = self._create_vehicle_config(vehicle_data)
                
                # Create vehicle components
                vehicle_components = self._create_vehicle_components(vehicle_id, vehicle_config)
                
                # Store vehicle
                self.vehicles[vehicle_id] = vehicle_components
                
                logger.info(f"✅ Created vehicle instance: {vehicle_id}")
            
            logger.info(f"Created {len(self.vehicles)} vehicle instances")
            
        except Exception as e:
            logger.error(f"Failed to create vehicle instances: {e}")
            raise

    def _create_vehicle_config(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database vehicle data to configuration format"""
        assignment = vehicle_data.get('current_assignment', {})
        
        config = {
            'active': vehicle_data.get('active', True),
            'route': assignment.get('route_id', ''),
            'speed_model': 'kinematic',  # Default speed model
            'speed': 60,  # Default speed
            'accel_limit': 3,
            'decel_limit': 4,
            'corner_slowdown': 1,
            'release_ticks': 3,
            'capacity': vehicle_data.get('capacity', 40),
            'passengers': 0,
            'license_plate': vehicle_data.get('license_plate', ''),
            'depot_id': vehicle_data.get('depot_id', ''),
            'assignment': assignment
        }
        
        return config

    def _create_vehicle_components(self, vehicle_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Navigator, Engine, and GPSDevice for a vehicle"""
        try:
            # Create components
            engine_buffer = EngineBuffer()
            
            # Load speed model
            speed_model = load_speed_model(
                config['speed_model'],
                speed=config['speed'],
                accel_limit=config['accel_limit'],
                decel_limit=config['decel_limit'],
                corner_slowdown=config['corner_slowdown'],
                release_ticks=config['release_ticks']
            )
            
            # Create Engine
            engine = Engine(vehicle_id, speed_model, engine_buffer, tick_time=self.tick_time)
            
            # Create Navigator with route if assigned
            navigator = None
            route_id = config.get('route')
            if route_id and route_id in self.routes:
                route_coords = self.routes[route_id].get('coordinates', [])
                if route_coords:
                    navigator = Navigator(
                        vehicle_id=vehicle_id,
                        route_coordinates=route_coords,
                        engine_buffer=engine_buffer,
                        tick_time=self.tick_time,
                        mode="geodesic",
                        direction="outbound"
                    )
                    logger.debug(f"Navigator created for {vehicle_id} with route {route_id}")
                else:
                    logger.warning(f"No coordinates found for route {route_id}")
            else:
                logger.info(f"No route assigned to vehicle {vehicle_id}")
            
            # Create GPSDevice with navigator_telemetry plugin
            gps_device = GPSDevice(
                vehicle_id=vehicle_id,
                device_config={'plugin': 'navigator_telemetry'},
                navigator_instance=navigator
            )
            
            return {
                '_engine': engine,
                '_navigator': navigator,
                '_gps': gps_device,
                'config': config,
                'vehicle_id': vehicle_id
            }
            
        except Exception as e:
            logger.error(f"Failed to create components for vehicle {vehicle_id}: {e}")
            raise

    def _setup_timetable_operations(self):
        """Setup timetable scheduler with vehicle handlers"""
        try:
            logger.info("Setting up timetable operations...")
            
            # Register vehicle handlers with scheduler
            for vehicle_id, vehicle_handler in self.vehicles.items():
                self.scheduler.register_vehicle_handler(vehicle_id, vehicle_handler)
            
            # Load today's schedule
            self.scheduler.load_today_schedule()
            
            logger.info("✅ Timetable operations setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup timetable operations: {e}")
            raise

    # ==================== DEPOT OPERATIONS ====================

    def start(self):
        """Start depot operations - either manual or timetable-driven"""
        try:
            logger.info("Starting depot operations")
            print("[INFO] Depot OPERATIONAL...")
            
            self.running = True
            
            if self.enable_timetable and self.scheduler:
                # Start timetable-driven operations
                logger.info("Starting timetable-driven fleet operations")
                self.scheduler.start()
                print("[INFO] Timetable scheduler started - vehicles will start per schedule")
            else:
                # Start all vehicles manually (legacy mode)
                logger.info("Starting all vehicles manually (legacy mode)")
                self._start_all_vehicles_manually()
            
        except Exception as e:
            logger.error(f"Failed to start depot operations: {e}")
            raise

    def _start_all_vehicles_manually(self):
        """Start all active vehicles manually (legacy behavior)"""
        for vehicle_id, vehicle_handler in self.vehicles.items():
            try:
                config = vehicle_handler['config']
                
                if not config.get('active', False):
                    print(f"[INFO] Vehicle {vehicle_id} inactive.")
                    continue
                
                print(f"[INFO] Navigator boarded for {vehicle_id}")
                
                # Create and start GPSDevice
                gps_device = vehicle_handler['_gps']
                gps_device.on()
                print(f"[INFO] GPSDevice ON for {vehicle_id}")
                
                # Start Engine
                engine = vehicle_handler['_engine']
                engine.on()
                print(f"[INFO] Engine started for {vehicle_id}")
                
                # Start Navigator if available
                navigator = vehicle_handler['_navigator']
                if navigator:
                    navigator.on()
                    print(f"[INFO] Navigator for {vehicle_id} turned ON (mode=geodesic, direction=outbound)")
                else:
                    print(f"[INFO] No navigator available for {vehicle_id}")
                
            except Exception as e:
                logger.error(f"Failed to start vehicle {vehicle_id}: {e}")

    def stop(self):
        """Stop all depot operations"""
        try:
            logger.info("Stopping depot operations")
            
            self.running = False
            
            # Stop scheduler if running
            if self.scheduler:
                self.scheduler.stop()
            
            # Stop all vehicles
            for vehicle_id, vehicle_handler in self.vehicles.items():
                try:
                    # Stop Navigator
                    navigator = vehicle_handler.get('_navigator')
                    if navigator:
                        navigator.off()
                    
                    # Stop Engine
                    engine = vehicle_handler.get('_engine')
                    if engine:
                        engine.off()
                    
                    # Stop GPSDevice
                    gps_device = vehicle_handler.get('_gps')
                    if gps_device:
                        gps_device.off()
                    
                    logger.debug(f"Stopped vehicle {vehicle_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to stop vehicle {vehicle_id}: {e}")
            
            print("[INFO] Depot operations stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop depot operations: {e}")

    def get_vehicle_status(self, vehicle_id: str) -> Dict[str, Any]:
        """Get current status of a vehicle"""
        if vehicle_id not in self.vehicles:
            return {'error': f'Vehicle {vehicle_id} not found'}
        
        vehicle_handler = self.vehicles[vehicle_id]
        
        try:
            navigator = vehicle_handler.get('_navigator')
            engine = vehicle_handler.get('_engine')
            gps_device = vehicle_handler.get('_gps')
            
            status = {
                'vehicle_id': vehicle_id,
                'active': vehicle_handler['config'].get('active', False),
                'navigator': {
                    'running': navigator._running if navigator else False,
                    'position': navigator.last_position if navigator else None,
                    'route': vehicle_handler['config'].get('route', '')
                },
                'engine': {
                    'running': engine._running if engine else False
                },
                'gps': {
                    'active': hasattr(gps_device, '_running') and gps_device._running if gps_device else False
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get status for vehicle {vehicle_id}: {e}")
            return {'error': str(e)}

    def get_fleet_status(self) -> Dict[str, Any]:
        """Get comprehensive status of entire fleet including timetable and countdown information"""
        try:
            api_status = self.data_provider.get_api_status()
            
            # Get timetable and resource information
            schedule_status = None
            resource_availability = None
            
            if self.scheduler:
                schedule_status = self.scheduler.get_schedule_status()
                resource_availability = self.scheduler.get_resource_availability()
            
            fleet_status = {
                'depot_running': self.running,
                'timetable_enabled': self.enable_timetable,
                'scheduler_running': self.scheduler.running if self.scheduler else False,
                'api_status': api_status,
                'api_available': self.data_provider.is_api_available(),
                'total_vehicles': len(self.vehicles),
                'active_vehicles': 0,
                'vehicles': {},
                # Enhanced timetable information
                'schedule_status': schedule_status,
                'resource_availability': resource_availability,
                'countdown_info': self._get_countdown_display(schedule_status) if schedule_status else None
            }
            
            for vehicle_id in self.vehicles:
                vehicle_status = self.get_vehicle_status(vehicle_id)
                fleet_status['vehicles'][vehicle_id] = vehicle_status
                
                if vehicle_status.get('navigator', {}).get('running', False):
                    fleet_status['active_vehicles'] += 1
            
            return fleet_status
            
        except Exception as e:
            logger.error(f"Failed to get fleet status: {e}")
            return {'error': str(e)}
    
    def _get_countdown_display(self, schedule_status: Dict[str, Any]) -> Optional[str]:
        """Generate human-readable countdown display for both operation modes"""
        if not schedule_status or not schedule_status.get('next_departure'):
            return "No scheduled departures"
        
        next_dep = schedule_status['next_departure']
        mode = schedule_status.get('mode', 'time')
        
        if mode == 'capacity':
            if next_dep.get('ready_to_depart'):
                return (f"🚐 Vehicle {next_dep['vehicle_id']} ready to depart: "
                       f"{next_dep['departure_reason']}")
            else:
                return (f"🚌 Vehicle {next_dep['vehicle_id']} boarding "
                       f"({next_dep['passengers']}) - "
                       f"Max wait: {next_dep['max_wait_remaining']}")
        else:
            # Time-based display
            if not next_dep.get('countdown_display'):
                return "No upcoming departures"
            return (f"Next departure: Vehicle {next_dep['vehicle_id']} "
                   f"on Route {next_dep['route_id']} "
                   f"at {next_dep['scheduled_time']} "
                   f"(in {next_dep['countdown_display']})")
    
    def get_detailed_schedule_status(self) -> str:
        """Get formatted schedule status for console display"""
        try:
            status = self.get_fleet_status()
            
            lines = []
            lines.append("📅 TIMETABLE & SCHEDULE STATUS")
            lines.append("=" * 50)
            
            # API and resource status
            if status.get('api_available'):
                lines.append("✅ Fleet Manager API: Connected")
            else:
                lines.append("❌ Fleet Manager API: Disconnected")
            
            resource_avail = status.get('resource_availability', {})
            lines.append(f"🚌 Vehicles Available: {resource_avail.get('vehicles_available', 0)}")
            lines.append(f"🛣️  Routes Available: {resource_avail.get('routes_available', 0)}")
            lines.append(f"👨‍✈️ Drivers Available: {resource_avail.get('drivers_available', 0)}")
            
            # Schedule status
            schedule = status.get('schedule_status', {})
            mode = schedule.get('mode', 'time')
            
            if schedule and schedule.get('timetable_loaded'):
                lines.append(f"📋 Schedule Mode: {mode.upper()}")
                lines.append(f"📋 Schedule Operations: {schedule['total_operations']} total, {schedule['pending_operations']} pending")
                
                if mode == 'capacity':
                    lines.append(f"� Boarding Vehicles: {schedule.get('boarding_vehicles', 0)}")
                else:
                    lines.append(f"�🚦 Active Vehicles: {schedule.get('active_vehicles', 0)}")
                
                # Next departure info
                if status.get('countdown_info'):
                    lines.append(f"⏰ {status['countdown_info']}")
                else:
                    lines.append("⏰ No upcoming departures")
                
                # Show operations based on mode
                if mode == 'capacity':
                    capacity_ops = schedule.get('capacity_operations', [])
                    if capacity_ops:
                        lines.append("\n🚐 CAPACITY-BASED OPERATIONS:")
                        for i, op in enumerate(capacity_ops[:3]):
                            status_emoji = "✅" if op['executed'] else ("🚌" if op['boarding'] else "⏳")
                            boarding_status = "BOARDING" if op['boarding'] else "WAITING"
                            ready_status = "READY!" if op['ready'] else ""
                            lines.append(f"   {i+1}. {status_emoji} Vehicle {op['vehicle_id']} - "
                                       f"{op['passengers']} passengers - {boarding_status} {ready_status}")
                else:
                    upcoming = schedule.get('upcoming_operations', [])
                    if upcoming:
                        lines.append("\n📍 UPCOMING OPERATIONS:")
                        for i, op in enumerate(upcoming[:3]):
                            countdown = op.get('countdown_seconds', 0)
                            if countdown >= 0:
                                lines.append(f"   {i+1}. Vehicle {op['vehicle_id']} - {op['operation']} at {op['scheduled_time']} (in {self._format_countdown_simple(countdown)})")
                            else:
                                lines.append(f"   {i+1}. Vehicle {op['vehicle_id']} - {op['operation']} at {op['scheduled_time']} (OVERDUE)")
            else:
                lines.append("❌ No timetable loaded or no scheduled operations")
                
            # Resource validation
            if resource_avail.get('resource_status') == 'insufficient_resources':
                lines.append("\n📋 SYSTEM STATUS:")
                if resource_avail.get('vehicles_available', 0) == 0:
                    lines.append("   - No vehicles designated")
                if resource_avail.get('routes_available', 0) == 0:
                    lines.append("   - No routes designated")
                if not schedule.get('timetable_loaded'):
                    lines.append("   - No timetable set")
            elif resource_avail.get('resource_status') == 'ready':
                lines.append("\n✅ All resources available for operations")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"❌ Failed to get schedule status: {e}"
    
    def _format_countdown_simple(self, seconds: int) -> str:
        """Simple countdown formatter"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds//60}m {seconds%60}s"
        else:
            return f"{seconds//3600}h {(seconds%3600)//60}m"
    
    def simulate_passenger_arrival(self, vehicle_id: str = None, passenger_count: int = None):
        """Manually simulate passenger arrival for testing capacity-based operations"""
        if not self.scheduler:
            logger.warning("No scheduler available for passenger simulation")
            return
        
        if vehicle_id:
            self.scheduler.simulate_passenger_arrival(vehicle_id, passenger_count)
        else:
            # Simulate for a random vehicle
            capacity_ops = [op for op in self.scheduler.capacity_operations if not op.executed]
            if capacity_ops:
                import random
                random_op = random.choice(capacity_ops)
                self.scheduler.simulate_passenger_arrival(random_op.vehicle_id, passenger_count)
                logger.info(f"Simulated passenger arrival for vehicle {random_op.vehicle_id}")
            else:
                logger.info("No capacity-based operations available for passenger simulation")

    def get_api_status(self) -> Dict[str, Any]:
        """Get current API connection status"""
        try:
            return self.data_provider.get_api_status()
        except Exception as e:
            return {'error': str(e), 'is_connected': False}

    def force_api_reconnect(self):
        """Force API reconnection attempt"""
        try:
            self.data_provider.force_reconnect()
            logger.info("API reconnection attempt initiated")
        except Exception as e:
            logger.error(f"Failed to force API reconnection: {e}")
            raise

    def force_start_vehicle(self, vehicle_id: str, route_id: str = None):
        """Manually force start a vehicle (for testing/debugging)"""
        if self.scheduler:
            try:
                # Use scheduler to force operation
                self.scheduler.force_execute_operation(
                    vehicle_id=vehicle_id,
                    operation_type='start_service',
                    route_id=route_id
                )
                logger.info(f"Force started vehicle {vehicle_id}")
            except Exception as e:
                logger.error(f"Failed to force start vehicle {vehicle_id}: {e}")
                raise
        else:
            logger.warning("No scheduler available for force start operation")

    def force_stop_vehicle(self, vehicle_id: str):
        """Manually force stop a vehicle (for testing/debugging)"""
        if self.scheduler:
            try:
                # Use scheduler to force operation
                self.scheduler.force_execute_operation(
                    vehicle_id=vehicle_id,
                    operation_type='end_service'
                )
                logger.info(f"Force stopped vehicle {vehicle_id}")
            except Exception as e:
                logger.error(f"Failed to force stop vehicle {vehicle_id}: {e}")
                raise
        else:
            logger.warning("No scheduler available for force stop operation")


# ---------------------------
# Manual test support
# ---------------------------
if __name__ == "__main__":
    depot = VehiclesDepot()
    depot.start()
    time.sleep(5)
    depot.stop()
