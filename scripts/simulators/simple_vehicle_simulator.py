#!/usr/bin/env python3
"""
Simple Vehicle Simulator
------------------------
A simplified version that works with or without database connection.
Falls back to dummy data if database is unavailable.
"""

import sys
import os
import time
import random
import logging
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

class SimpleVehicleSimulator:
    def __init__(self, tick_time: float = 1.0):
        self.tick_time = tick_time
        self.vehicles: Dict[str, VehicleState] = {}
        self.running = False
        
        # Try to load from database, fallback to dummy data
        self._load_vehicles()
        
    def _load_vehicles(self):
        """Load vehicles from database or create dummy data"""
        try:
            # Try database first
            self._load_from_database()
        except Exception as e:
            logger.warning(f"Database unavailable ({e}), using dummy data")
            self._load_dummy_data()
            
    def _load_from_database(self):
        """Attempt to load from database"""
        # Add project root to path
        sys.path.insert(0, os.path.dirname(__file__))
        
        from config.database import get_ssh_tunnel, get_db_config
        from sqlalchemy import create_engine, text
        
        tunnel = None
        try:
            tunnel = get_ssh_tunnel()
            tunnel.start()
            time.sleep(1)  # Brief wait for tunnel
            
            db_config = get_db_config(tunnel)
            connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
            
            engine = create_engine(connection_string, connect_args={'connect_timeout': 5})
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT vehicle_id, route_id, status FROM vehicles WHERE status = 'active'"))
                rows = result.fetchall()
                
                for row in rows:
                    vehicle_id, route_id, status = row
                    self.vehicles[vehicle_id] = VehicleState(
                        vehicle_id=vehicle_id,
                        route_id=route_id or "R001",
                        status=status,
                        lat=40.730610 + random.uniform(-0.01, 0.01),  # Random start position
                        lng=-73.935242 + random.uniform(-0.01, 0.01),
                        heading=random.uniform(0, 360),
                        speed=0.0,
                        last_update=datetime.now()
                    )
                    
            logger.info(f"✅ Loaded {len(self.vehicles)} vehicles from database")
            
        finally:
            if tunnel:
                tunnel.stop()
                
    def _load_dummy_data(self):
        """Create dummy vehicle data for testing"""
        dummy_vehicles = [
            {"id": "BUS001", "route": "R001", "lat": 40.730610, "lng": -73.935242},
            {"id": "BUS002", "route": "R002", "lat": 40.730610, "lng": -73.935242},
            {"id": "BUS003", "route": "R003", "lat": 40.730610, "lng": -73.935242},
            {"id": "ZR1001", "route": "R001", "lat": 40.730610, "lng": -73.935242},
        ]
        
        for vehicle in dummy_vehicles:
            self.vehicles[vehicle["id"]] = VehicleState(
                vehicle_id=vehicle["id"],
                route_id=vehicle["route"],
                status="active",
                lat=vehicle["lat"] + random.uniform(-0.01, 0.01),
                lng=vehicle["lng"] + random.uniform(-0.01, 0.01),
                heading=random.uniform(0, 360),
                speed=0.0,
                last_update=datetime.now()
            )
            
        logger.info(f"🎭 Created {len(self.vehicles)} dummy vehicles")
        
    def start(self):
        """Start the simulation"""
        self.running = True
        logger.info("🚌 Vehicle simulation started")
        
        for vehicle_id, vehicle in self.vehicles.items():
            logger.info(f"   {vehicle_id}: Route {vehicle.route_id} at ({vehicle.lat:.6f}, {vehicle.lng:.6f})")
            
    def update(self):
        """Update all vehicle positions"""
        if not self.running:
            return
            
        for vehicle_id, vehicle in self.vehicles.items():
            # Simple movement simulation
            if vehicle.speed == 0:
                # Start moving
                vehicle.speed = random.uniform(20, 60)  # km/h
                vehicle.heading = random.uniform(0, 360)
                
            # Move vehicle slightly (very basic simulation)
            speed_ms = vehicle.speed * 1000 / 3600  # Convert km/h to m/s
            distance = speed_ms * self.tick_time  # Distance in meters
            
            # Convert to lat/lng (rough approximation)
            lat_change = (distance * 0.000009) * random.uniform(-1, 1)
            lng_change = (distance * 0.000009) * random.uniform(-1, 1)
            
            vehicle.lat += lat_change
            vehicle.lng += lng_change
            vehicle.last_update = datetime.now()
            
            # Vary speed slightly
            vehicle.speed += random.uniform(-5, 5)
            vehicle.speed = max(0, min(80, vehicle.speed))  # Keep speed reasonable
            
    def stop(self):
        """Stop the simulation"""
        self.running = False
        logger.info("🛑 Vehicle simulation stopped")
        
    def get_status(self) -> str:
        """Get current simulation status"""
        if not self.vehicles:
            return "❌ No vehicles loaded"
            
        status_lines = [f"🚌 {len(self.vehicles)} vehicles active:"]
        
        for vehicle_id, vehicle in self.vehicles.items():
            status_lines.append(
                f"   {vehicle_id}: {vehicle.status} on {vehicle.route_id} "
                f"at ({vehicle.lat:.6f}, {vehicle.lng:.6f}) "
                f"speed: {vehicle.speed:.1f} km/h"
            )
            
        return "\n".join(status_lines)

def main():
    """Main simulation loop"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Vehicle Simulator")
    parser.add_argument("--tick", type=float, default=1.0, help="Update interval in seconds")
    parser.add_argument("--seconds", type=int, default=60, help="Run duration in seconds")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    print("=" * 50)
    print("🚌 Simple Vehicle Simulator")
    print("=" * 50)
    print(f"⏱️  Update Interval: {args.tick} seconds")
    print(f"⏰ Duration: {args.seconds} seconds")
    print(f"🐛 Debug: {'On' if args.debug else 'Off'}")
    print("-" * 50)
    
    try:
        # Create and start simulator
        simulator = SimpleVehicleSimulator(tick_time=args.tick)
        simulator.start()
        
        # Run simulation loop
        start_time = time.time()
        last_status_time = 0
        
        while time.time() - start_time < args.seconds:
            current_time = time.time() - start_time
            
            # Update vehicles
            simulator.update()
            
            # Print status every 10 seconds
            if current_time - last_status_time >= 10:
                print(f"\n⏰ Time: {current_time:.1f}s")
                print(simulator.get_status())
                last_status_time = current_time
                
            time.sleep(args.tick)
            
        simulator.stop()
        print(f"\n✅ Simulation completed after {args.seconds} seconds")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Simulation interrupted by user")
        if 'simulator' in locals():
            simulator.stop()
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
        logger.exception("Simulation failed")

if __name__ == "__main__":
    main()
