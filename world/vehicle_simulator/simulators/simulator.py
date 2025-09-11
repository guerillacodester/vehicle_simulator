#!/usr/bin/env python3
"""
Enhanced Vehicle Simulator with GPS Transmission
------------------------------------------------
Combines database-backed vehicle simulation with real-time GPS data transmission
to the WebSocket server for complete telemetry pipeline testing.
"""

import sys
import os
import time
import random
import logging
import configparser
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import GPS device
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import make_packet

# Get logger (don't configure it here - let main.py handle it)
logger = logging.getLogger(__name__)


@dataclass
class VehicleState:
    vehicle_id: str
    route_id: str
    status: str
    lat: float = 0.0
    lng: float = 0.0
    heading: float = 0.0
    speed: float = 0.0
    last_update: datetime = None
    gps_device: Optional[GPSDevice] = None

class VehicleSimulator:
    def __init__(self, tick_time: float = 1.0, enable_gps: bool = True, vehicle_data: List[Dict] = None):
        self.tick_time = tick_time
        self.enable_gps = enable_gps
        self.vehicles: Dict[str, VehicleState] = {}
        self.running = False
        
        # Load GPS server configuration
        self.gps_config = self._load_gps_config()
        
        # Load vehicles from provided data or fail
        if vehicle_data:
            self._load_provided_vehicles(vehicle_data)
        else:
            logger.error("❌ NO VEHICLE DATA PROVIDED TO SIMULATOR")
            raise Exception("VehicleSimulator requires vehicle data to be provided")
        
        # Initialize GPS devices if enabled
        if self.enable_gps:
            self._initialize_gps_devices()
        
    def _load_gps_config(self):
        """Load GPS server configuration from config.ini"""
        config = configparser.ConfigParser()
        config.read("config.ini")
        
        server_url = config.get("server", "ws_url", fallback="ws://localhost:5000/")
        auth_token = os.getenv("AUTH_TOKEN", "supersecrettoken")
        
        return {
            "server_url": server_url,
            "auth_token": auth_token
        }
        
    def _initialize_gps_devices(self):
        """Initialize GPS devices for each vehicle"""
        print("📡 Initializing GPS devices...")
        
        for vehicle_id, vehicle in self.vehicles.items():
            try:
                # Create WebSocket transmitter
                from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
                from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
                
                transmitter = WebSocketTransmitter(
                    server_url=self.gps_config["server_url"],
                    token=self.gps_config["auth_token"],
                    device_id=vehicle_id,
                    codec=PacketCodec()
                )
                
                # Configure simulation plugin
                plugin_config = {
                    "type": "simulation",
                    "update_interval": self.tick_time,
                    "device_id": vehicle_id
                }
                
                # Create GPS device with plugin system
                gps_device = GPSDevice(
                    device_id=vehicle_id,
                    ws_transmitter=transmitter,
                    plugin_config=plugin_config
                )
                
                # Start the GPS device
                gps_device.on()
                vehicle.gps_device = gps_device
                
                # Set the vehicle state for the plugin
                gps_device.set_vehicle_state(vehicle)
                
                print(f"   📡 {vehicle_id}: GPS device ready")
                
            except Exception as e:
                logger.warning(f"   ⚠️ {vehicle_id}: GPS device failed - {e}")
                
    def _load_provided_vehicles(self, vehicle_data: List[Dict]):
        """Load vehicles from provided data (no database connections)"""
        logger.info(f"Loading {len(vehicle_data)} vehicles from provided data")
        
        for vehicle in vehicle_data:
            vehicle_id = vehicle.get('id') or vehicle.get('license_plate', f"VEHICLE_{len(self.vehicles)}")
            
            # Create vehicle state from provided data
            state = VehicleState(
                vehicle_id=vehicle_id,
                route_id=vehicle.get('route_id', 'UNKNOWN'),
                lat=vehicle.get('lat', 13.28),  # Default Barbados coordinates
                lng=vehicle.get('lon', -59.64),
                speed=0.0,
                heading=0.0,
                status=vehicle.get('status', 'active')
            )
            
            self.vehicles[vehicle_id] = state
            logger.info(f"   🚌 {vehicle_id}: {state.status} on route {state.route_id}")
        
        logger.info(f"✅ Loaded {len(self.vehicles)} vehicles successfully")
            
    def _load_from_database(self):
        """Load vehicles from the database"""
        try:
            # Try to import database configuration (from fleet_manager)
            try:
                from world.fleet_manager.scripts.config_loader import load_config
                config = load_config()
                # Extract database and SSH configuration from fleet_manager config
                ssh_config = config.get('SSH', {})
                db_config = config.get('DATABASE', {})
            except ImportError:
                raise Exception("Fleet manager database configuration not available")
            
            import psycopg2
            import sshtunnel
            
            # Create SSH tunnel if configured
            if ssh_config:
                tunnel = sshtunnel.SSHTunnelForwarder(
                    (ssh_config.get('host'), int(ssh_config.get('port', 22))),
                    ssh_username=ssh_config.get('username'),
                    ssh_password=ssh_config.get('password'),  # or use ssh_pkey for key-based auth
                    remote_bind_address=(db_config.get('host', 'localhost'), int(db_config.get('port', 5432)))
                )
                tunnel.start()
                local_port = tunnel.local_bind_port
            else:
                tunnel = None
                local_port = int(db_config.get('port', 5432))
            
            # Wait for tunnel
            if tunnel:
                time.sleep(2)
            
            # Connect to database
            connection_params = {
                'host': 'localhost' if tunnel else db_config.get('host', 'localhost'),
                'port': local_port,
                'database': db_config.get('database'),
                'user': db_config.get('user'),
                'password': db_config.get('password')
            }
            conn = psycopg2.connect(**connection_params)
            cursor = conn.cursor()
            
            # Load vehicles with route information
            cursor.execute("""
                SELECT v.id, v.route_id, v.status, 
                       COALESCE(v.current_lat, 40.730610) as lat,
                       COALESCE(v.current_lng, -73.935242) as lng
                FROM vehicles v 
                WHERE v.status = 'active' 
                LIMIT 10
            """)
            
            vehicles_data = cursor.fetchall()
            
            for vehicle_data in vehicles_data:
                vehicle_id, route_id, status, lat, lng = vehicle_data
                
                self.vehicles[vehicle_id] = VehicleState(
                    vehicle_id=vehicle_id,
                    route_id=route_id,
                    status=status,
                    lat=float(lat) + random.uniform(-0.01, 0.01),  # Add some variation
                    lng=float(lng) + random.uniform(-0.01, 0.01),
                    heading=random.uniform(0, 360),
                    speed=random.uniform(20, 50),  # Start with some speed
                    last_update=datetime.now()
                )
                    
            logger.info(f"✅ Loaded {len(self.vehicles)} vehicles from database")
            
            cursor.close()
            conn.close()
            
        finally:
            if 'tunnel' in locals():
                tunnel.stop()
                
    def _load_dummy_data(self):
        """Create dummy vehicle data for testing"""
        dummy_vehicles = [
            {"id": "BUS001", "route": "R001", "lat": 13.2810, "lng": -59.6463},  # Barbados coordinates
            {"id": "BUS002", "route": "R002", "lat": 13.2820, "lng": -59.6470},
            {"id": "BUS003", "route": "R003", "lat": 13.2830, "lng": -59.6480},
            {"id": "ZR1001", "route": "R001", "lat": 13.2840, "lng": -59.6490},
        ]
        
        for vehicle in dummy_vehicles:
            self.vehicles[vehicle["id"]] = VehicleState(
                vehicle_id=vehicle["id"],
                route_id=vehicle["route"],
                status="active",
                lat=vehicle["lat"] + random.uniform(-0.001, 0.001),
                lng=vehicle["lng"] + random.uniform(-0.001, 0.001),
                heading=random.uniform(0, 360),
                speed=random.uniform(25, 55),
                last_update=datetime.now()
            )
            
        logger.info(f"🎭 Created {len(self.vehicles)} dummy vehicles")
        
    def start(self):
        """Start the simulation"""
        self.running = True
        print("🚌 Vehicle simulation started")
        print(f"📡 GPS transmission: {'enabled' if self.enable_gps else 'disabled'}")
        
        for vehicle_id, vehicle in self.vehicles.items():
            gps_status = "📡" if vehicle.gps_device else "🔒"
            print(f"   {gps_status} {vehicle_id}: Route {vehicle.route_id} at ({vehicle.lat:.6f}, {vehicle.lng:.6f})")
            
    def update(self):
        """Update all vehicle positions and transmit GPS data"""
        if not self.running:
            return
            
        for vehicle_id, vehicle in self.vehicles.items():
            # Update vehicle position (same logic as before)
            if vehicle.speed < 10:
                vehicle.speed = random.uniform(20, 60)  # km/h
                vehicle.heading = random.uniform(0, 360)
                
            # Move vehicle slightly
            speed_ms = vehicle.speed * 1000 / 3600  # Convert km/h to m/s
            distance = speed_ms * self.tick_time  # Distance in meters
            
            # Convert to lat/lng (rough approximation)
            lat_change = (distance * 0.000009) * random.uniform(-1, 1)
            lng_change = (distance * 0.000009) * random.uniform(-1, 1)
            
            vehicle.lat += lat_change
            vehicle.lng += lng_change
            vehicle.last_update = datetime.now()
            
            # Vary speed slightly
            vehicle.speed += random.uniform(-3, 3)
            vehicle.speed = max(15, min(75, vehicle.speed))  # Keep speed reasonable
            
            # GPS data transmission is now handled by the plugin system automatically
                
    def stop(self):
        """Stop the simulation and GPS devices"""
        self.running = False
        print("🛑 Stopping simulation...")
        
        # Stop all GPS devices
        if self.enable_gps:
            for vehicle_id, vehicle in self.vehicles.items():
                # Stop GPS device
                if vehicle.gps_device:
                    try:
                        vehicle.gps_device.off()
                        print(f"   📡 {vehicle_id}: GPS device stopped")
                    except Exception as e:
                        logger.warning(f"   ⚠️ {vehicle_id}: GPS stop failed - {e}")
                        
        print("✅ Simulation stopped")
        
    def get_status(self) -> str:
        """Get current simulation status"""
        active_vehicles = len([v for v in self.vehicles.values() if v.status == "active"])
        gps_active = len([v for v in self.vehicles.values() if v.gps_device]) if self.enable_gps else 0
        
        status_lines = []
        for vehicle_id, vehicle in self.vehicles.items():
            gps_indicator = "📡" if (self.enable_gps and vehicle.gps_device) else "🔒"
            status_lines.append(
                f"   {gps_indicator} {vehicle_id}: {vehicle.status} on {vehicle.route_id} "
                f"at ({vehicle.lat:.6f}, {vehicle.lng:.6f}) speed: {vehicle.speed:.1f} km/h"
            )
            
        return f"🚌 {active_vehicles} vehicles active:\n" + "\n".join(status_lines)

def main():
    """Main simulation loop"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Vehicle Simulator with GPS")
    parser.add_argument("--interval", type=float, default=1.0, help="Update interval in seconds")
    parser.add_argument("--duration", type=int, default=60, help="Simulation duration in seconds")
    parser.add_argument("--no-gps", action="store_true", help="Disable GPS transmission")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    print("=" * 50)
    print("🚌 Enhanced Vehicle Simulator with GPS")
    print("=" * 50)
    print(f"⏱️  Update Interval: {args.interval} seconds")
    print(f"⏰ Duration: {args.duration} seconds")
    print(f"📡 GPS Transmission: {'disabled' if args.no_gps else 'enabled'}")
    print(f"🐛 Debug: {'On' if args.debug else 'Off'}")
    print("-" * 50)
    
    # Create and start simulator
    simulator = VehicleSimulator(
        tick_time=args.interval,
        enable_gps=not args.no_gps
    )
    
    try:
        simulator.start()
        
        start_time = time.time()
        last_status_time = 0
        
        while time.time() - start_time < args.duration:
            simulator.update()
            
            # Show status every 10 seconds
            current_time = time.time() - start_time
            if current_time - last_status_time >= 10:
                print(f"\n⏰ Time: {current_time:.1f}s")
                print(simulator.get_status())
                last_status_time = current_time
            
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted by user")
    finally:
        simulator.stop()
        
    print("✅ Simulation completed")

if __name__ == "__main__":
    main()
