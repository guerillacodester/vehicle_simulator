#!/usr/bin/env python3
"""
Database-driven Vehicles Depot
------------------------------
Manages fleet vehicles loaded from PostgreSQL database instead of JSON files.
"""

import logging
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Vehicle, Route, Stop, Timetable
from config.database import get_ssh_tunnel, get_db_config
from world.fleet_manager.manager import FleetManager
from world.fleet_dispatcher.dispatcher import FleetDispatcher

logger = logging.getLogger(__name__)

class DatabaseVehiclesDepot:
    def __init__(self, tick_time: float = 0.1):
        self.tick_time = tick_time
        self.vehicles = {}
        self.running = False
        self.tunnel = None
        self.session = None
        
        # Setup database connection
        self._setup_database()
        
        # Load vehicles from database
        self._load_vehicles_from_db()
        
        # Initialize fleet dispatcher (skip fleet manager for now)
        self.fleet_dispatcher = None
        
        logger.info(f"Database depot initialized with {len(self.vehicles)} vehicles")
    
    def _setup_database(self):
        """Setup database connection with SSH tunnel"""
        try:
            logger.info("Connecting to database...")
            
            # Add timeout for SSH tunnel
            self.tunnel = get_ssh_tunnel()
            logger.info("Starting SSH tunnel...")
            self.tunnel.start()
            
            # Wait a moment for tunnel to establish
            time.sleep(2)
            
            logger.info("Getting database config...")
            db_config = get_db_config(self.tunnel)
            
            connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
            logger.info(f"Connecting to: postgresql://{db_config['user']}:***@{db_config['host']}:{db_config['port']}/{db_config['dbname']}")
            
            engine = create_engine(connection_string, connect_args={'connect_timeout': 10})
            
            Session = sessionmaker(bind=engine)
            self.session = Session()
            
            # Test the connection
            self.session.execute("SELECT 1")
            
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            if self.tunnel:
                try:
                    self.tunnel.stop()
                except:
                    pass
            sys.exit(1)
    
    def _load_vehicles_from_db(self):
        """Load active vehicles from the database"""
        try:
            # Query all active vehicles with their routes
            vehicles_query = self.session.query(Vehicle).filter_by(status='active').all()
            
            for vehicle in vehicles_query:
                # Get route information if assigned
                route_info = None
                if vehicle.route_id:
                    route = self.session.query(Route).filter_by(route_id=vehicle.route_id).first()
                    if route:
                        route_info = {
                            'route_id': route.route_id,
                            'name': route.name,
                            'shape': route.shape
                        }
                
                # Create vehicle configuration
                self.vehicles[vehicle.vehicle_id] = {
                    'active': True,
                    'status': vehicle.status,
                    'route_info': route_info,
                    'database_id': vehicle.id,
                    # Add simulation-specific defaults
                    'speed_model': 'kinematic',
                    'speed': 60,  # km/h
                    'accel_limit': 3,
                    'decel_limit': 4,
                    'corner_slowdown': 1,
                    'release_ticks': 3,
                    'initial_state': 'AT_TERMINAL',
                    'current_position': {'lat': 0, 'lng': 0},
                    'heading': 0,
                    'passengers': 0,
                    'capacity': 40
                }
                
            logger.info(f"Loaded {len(self.vehicles)} active vehicles from database")
            
        except Exception as e:
            logger.error(f"Failed to load vehicles from database: {e}")
            self.vehicles = {}
    
    def start(self):
        """Start all active vehicles"""
        logger.info("Starting database depot operations")
        print("[INFO] FleetDispatcher ONSITE (Database Mode)")
        print("[INFO] Depot OPERATIONAL...")
        
        self.running = True
        
        for vid, cfg in self.vehicles.items():
            if cfg.get("active", False):
                logger.info(f"Starting vehicle {vid}")
                
                # Initialize vehicle simulation components
                self._initialize_vehicle(vid, cfg)
                
                # Start vehicle simulation
                self._start_vehicle_simulation(vid, cfg)
        
        # Start main simulation loop
        self._simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._simulation_thread.start()
        
        logger.info("All vehicles started")
    
    def _initialize_vehicle(self, vehicle_id: str, config: Dict[str, Any]):
        """Initialize simulation components for a vehicle"""
        # Create fleet dispatcher for this vehicle
        dispatcher = FleetDispatcher(vehicle_id=vehicle_id, config=config)
        config['_dispatcher'] = dispatcher
        
        # Set initial position based on route or default
        if config.get('route_info') and config['route_info'].get('shape'):
            # Extract starting position from route geometry
            # For now, use a default position
            config['current_position'] = {'lat': 40.730610, 'lng': -73.935242}
        
        logger.debug(f"Vehicle {vehicle_id} initialized")
    
    def _start_vehicle_simulation(self, vehicle_id: str, config: Dict[str, Any]):
        """Start simulation for a specific vehicle"""
        dispatcher = config.get('_dispatcher')
        if dispatcher:
            dispatcher.start()
        
        logger.debug(f"Vehicle {vehicle_id} simulation started")
    
    def _simulation_loop(self):
        """Main simulation loop"""
        while self.running:
            try:
                # Update vehicle positions
                self._update_vehicles()
                
                # Sleep for tick time
                time.sleep(self.tick_time)
                
            except Exception as e:
                logger.error(f"Simulation loop error: {e}")
                break
    
    def _update_vehicles(self):
        """Update all vehicle positions and states"""
        for vid, cfg in self.vehicles.items():
            if cfg.get("active", False):
                # Simple position update simulation
                dispatcher = cfg.get('_dispatcher')
                if dispatcher:
                    # Update vehicle state based on speed model
                    self._update_vehicle_position(vid, cfg)
    
    def _update_vehicle_position(self, vehicle_id: str, config: Dict[str, Any]):
        """Update position for a specific vehicle"""
        # Simple simulation - move vehicle slightly
        current_pos = config.get('current_position', {'lat': 0, 'lng': 0})
        speed_kmh = config.get('speed', 60)
        
        # Convert speed to degrees per second (rough approximation)
        speed_deg_per_sec = (speed_kmh / 3600) * (1/111)  # 1 degree ≈ 111 km
        
        # Move vehicle forward (simple linear movement)
        heading = config.get('heading', 0)
        if heading == 0:  # North
            current_pos['lat'] += speed_deg_per_sec * self.tick_time
        elif heading == 90:  # East
            current_pos['lng'] += speed_deg_per_sec * self.tick_time
        elif heading == 180:  # South
            current_pos['lat'] -= speed_deg_per_sec * self.tick_time
        elif heading == 270:  # West
            current_pos['lng'] -= speed_deg_per_sec * self.tick_time
        
        config['current_position'] = current_pos
        
        # Log position update
        logger.debug(f"Vehicle {vehicle_id} position: {current_pos['lat']:.6f}, {current_pos['lng']:.6f}")
    
    def stop(self):
        """Stop all active vehicles"""
        logger.info("Stopping database depot operations")
        self.running = False
        
        for vid, cfg in self.vehicles.items():
            if cfg.get("active", False):
                logger.debug(f"Vehicle {vid} state: STOPPED")
                
                dispatcher = cfg.get("_dispatcher")
                if dispatcher:
                    dispatcher.stop()
        
        # Cleanup database connection
        if self.session:
            self.session.close()
        if self.tunnel:
            self.tunnel.stop()
        
        logger.info("All vehicles stopped")
    
    def get_vehicle_status(self) -> Dict[str, Any]:
        """Get current status of all vehicles"""
        status = {}
        for vid, cfg in self.vehicles.items():
            status[vid] = {
                'active': cfg.get('active', False),
                'position': cfg.get('current_position', {}),
                'heading': cfg.get('heading', 0),
                'speed': cfg.get('speed', 0),
                'passengers': cfg.get('passengers', 0),
                'route': cfg.get('route_info', {}).get('route_id', 'N/A')
            }
        return status
