#!/usr/bin/env python3
"""
Database-Driven World Vehicles Simulator
----------------------------------------
Enhanced version that loads vehicles, routes, and timetables from the database
instead of relying on JSON files. Integrates with the PostgreSQL backend.
"""

import logging
import sys
import os
import argparse
import time
import textwrap
import atexit
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import psycopg2
import psycopg2.extras

# Import our database configuration
from config.database import get_ssh_tunnel, get_db_config

# Configure minimal logging with our format
logging.basicConfig(
    format='%(message)s',
    level=logging.ERROR,
    force=True  # Override any existing handlers
)

def shutdown_handler():
    """Clean shutdown handler"""
    logging.shutdown()

# Register shutdown handler
atexit.register(shutdown_handler)

class DatabaseVehiclesDepot:
    """Database-driven vehicles depot that manages vehicle simulation using database data"""
    
    def __init__(self, tick_time: float = 1.0):
        self.tick_time = tick_time
        self.vehicles = {}
        self.routes = {}
        self.timetables = {}
        self.stops = {}
        self.tunnel = None
        self.db_conn = None
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize database connection
        self._connect_database()
        
        # Load data from database
        self._load_routes()
        self._load_stops()
        self._load_vehicles()
        self._load_timetables()
        
    def _connect_database(self):
        """Establish database connection through SSH tunnel"""
        try:
            # Create SSH tunnel
            self.tunnel = get_ssh_tunnel()
            self.tunnel.start()
            
            # Wait for tunnel to stabilize
            time.sleep(2)
            
            # Connect to database
            db_config = get_db_config(self.tunnel)
            self.db_conn = psycopg2.connect(**db_config)
            self.db_conn.autocommit = True
            
            self.logger.info("✅ Database connection established")
            
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            raise
            
    def _load_routes(self):
        """Load routes from database"""
        try:
            cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT id, route_id, name, 
                       ST_AsText(shape) as geometry_wkt,
                       ST_AsGeoJSON(shape) as geometry_geojson
                FROM routes 
                ORDER BY name
            """)
            
            routes_data = cursor.fetchall()
            
            for route in routes_data:
                route_id = route['route_id']  # Use route_id instead of id
                self.routes[route_id] = {
                    'id': route['id'],
                    'route_id': route_id,
                    'name': route['name'],
                    'geometry_wkt': route['geometry_wkt'],
                    'geometry_geojson': route['geometry_geojson']
                }
                
            self.logger.info(f"✅ Loaded {len(self.routes)} routes from database")
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load routes: {e}")
            
    def _load_stops(self):
        """Load stops from database"""
        try:
            cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT id, name, 
                       ST_Y(location) as lat,
                       ST_X(location) as lng
                FROM stops
                ORDER BY name
            """)
            
            stops_data = cursor.fetchall()
            
            for stop in stops_data:
                stop_id = stop['id']
                self.stops[stop_id] = {
                    'id': stop_id,
                    'name': stop['name'],
                    'lat': float(stop['lat']),
                    'lng': float(stop['lng'])
                }
                
            self.logger.info(f"✅ Loaded {len(self.stops)} stops from database")
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load stops: {e}")
            
    def _load_vehicles(self):
        """Load vehicles from database"""
        try:
            cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT v.id, v.vehicle_id, v.route_id, v.status,
                       13.2810 as lat,  -- Default Barbados coordinates
                       -59.6463 as lng,
                       0 as heading,
                       0 as speed,
                       r.name as route_name
                FROM vehicles v
                LEFT JOIN routes r ON v.route_id = r.route_id
                WHERE v.status = 'active'
                ORDER BY v.vehicle_id
            """)
            
            vehicles_data = cursor.fetchall()
            
            for vehicle in vehicles_data:
                vehicle_id = vehicle['vehicle_id']  # Use vehicle_id instead of id
                self.vehicles[vehicle_id] = {
                    'id': vehicle['id'],
                    'vehicle_id': vehicle_id,
                    'route_id': vehicle['route_id'],
                    'route_name': vehicle['route_name'],
                    'status': vehicle['status'],
                    'capacity': 40,  # Default capacity
                    'position': {
                        'lat': float(vehicle['lat']),
                        'lng': float(vehicle['lng'])
                    },
                    'heading': float(vehicle['heading']),
                    'speed': float(vehicle['speed']),
                    'active': vehicle['status'] == 'active',
                    # Add GPS and simulation components
                    'gps_device': None,
                    'engine': None,
                    'navigator': None
                }
                
            self.logger.info(f"✅ Loaded {len(self.vehicles)} vehicles from database")
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load vehicles: {e}")
            
    def _load_timetables(self):
        """Load timetables from database"""
        try:
            cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT t.id, t.route_id, t.vehicle_id, t.departure_time,
                       r.name as route_name
                FROM timetables t
                LEFT JOIN routes r ON t.route_id = r.route_id
                ORDER BY t.route_id, t.departure_time
            """)
            
            timetables_data = cursor.fetchall()
            
            # Group timetables by route
            for timetable in timetables_data:
                route_id = timetable['route_id']
                
                if route_id not in self.timetables:
                    self.timetables[route_id] = []
                    
                self.timetables[route_id].append({
                    'id': timetable['id'],
                    'route_id': route_id,
                    'route_name': timetable['route_name'],
                    'vehicle_id': timetable['vehicle_id'],
                    'departure_time': timetable['departure_time']
                })
                
            self.logger.info(f"✅ Loaded timetables for {len(self.timetables)} routes from database")
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load timetables: {e}")
            
    def initialize_gps_devices(self):
        """Initialize GPS devices for all active vehicles"""
        from world.vehicle.gps_device.device import GPSDevice
        import configparser
        
        # Load GPS configuration
        config = configparser.ConfigParser()
        config.read("config.ini")
        server_url = config.get("server", "ws_url", fallback="ws://localhost:5000/")
        auth_token = os.getenv("AUTH_TOKEN", "supersecrettoken")
        
        self.logger.info("📡 Initializing GPS devices...")
        
        for vehicle_id, vehicle_config in self.vehicles.items():
            if vehicle_config['active']:
                try:
                    # Create GPS device
                    gps_device = GPSDevice(
                        device_id=vehicle_id,
                        server_url=server_url,
                        auth_token=auth_token,
                        method="ws",
                        interval=self.tick_time
                    )
                    
                    # Start GPS device
                    gps_device.on()
                    vehicle_config['gps_device'] = gps_device
                    
                    self.logger.info(f"   📡 {vehicle_id}: GPS device started")
                    
                except Exception as e:
                    self.logger.warning(f"   ⚠️ {vehicle_id}: GPS device failed - {e}")
                    
    def start(self):
        """Start the simulation"""
        self.logger.info("🚌 Database-driven vehicle simulation starting...")
        
        # Initialize GPS devices
        self.initialize_gps_devices()
        
        # Show summary
        active_vehicles = [v for v in self.vehicles.values() if v['active']]
        
        print("\n📊 Simulation Summary:")
        print(f"   🚌 Vehicles: {len(active_vehicles)} active")
        print(f"   🛣️  Routes: {len(self.routes)}")
        print(f"   🚏 Stops: {len(self.stops)}")
        print(f"   📅 Timetables: {sum(len(t) for t in self.timetables.values())} entries")
        
        print("\n🚌 Active Vehicles:")
        for vehicle in active_vehicles:
            gps_status = "📡" if vehicle['gps_device'] else "🔒"
            route_name = vehicle['route_name'] or vehicle['route_id']
            print(f"   {gps_status} {vehicle['id']}: {route_name} at ({vehicle['position']['lat']:.6f}, {vehicle['position']['lng']:.6f})")
            
        # Show route schedules
        print(f"\n📅 Route Schedules:")
        for route_id, schedule in self.timetables.items():
            route_name = self.routes.get(route_id, {}).get('name', route_id)
            print(f"   🛣️ {route_name}: {len(schedule)} scheduled stops")
            
    def update(self):
        """Update all vehicle positions and send GPS data"""
        import random
        from datetime import datetime, timezone
        
        for vehicle_id, vehicle in self.vehicles.items():
            if not vehicle['active']:
                continue
                
            # Simple movement simulation
            position = vehicle['position']
            
            # Update speed if needed
            if vehicle['speed'] < 10:
                vehicle['speed'] = random.uniform(20, 60)
                vehicle['heading'] = random.uniform(0, 360)
                
            # Calculate movement
            speed_ms = vehicle['speed'] * 1000 / 3600  # Convert km/h to m/s
            distance = speed_ms * self.tick_time  # Distance in meters
            
            # Convert to lat/lng changes (rough approximation)
            lat_change = (distance * 0.000009) * random.uniform(-1, 1)
            lng_change = (distance * 0.000009) * random.uniform(-1, 1)
            
            # Update position
            position['lat'] += lat_change
            position['lng'] += lng_change
            
            # Vary speed slightly
            vehicle['speed'] += random.uniform(-3, 3)
            vehicle['speed'] = max(15, min(75, vehicle['speed']))
            
            # Send GPS data if device is available
            if vehicle['gps_device']:
                self._send_gps_data(vehicle_id, vehicle)
                
    def _send_gps_data(self, vehicle_id: str, vehicle: dict):
        """Send GPS data for a vehicle"""
        try:
            gps_data = {
                "lat": vehicle['position']['lat'],
                "lon": vehicle['position']['lng'],
                "speed": vehicle['speed'],
                "heading": vehicle['heading'],
                "route": vehicle['route_id'],
                "vehicle_reg": vehicle_id,
                "driver_id": f"drv-{vehicle_id}",
                "driver_name": {"first": "Driver", "last": vehicle_id},
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            
            # Send to GPS device buffer
            vehicle['gps_device'].buffer.write(gps_data)
            
        except Exception as e:
            self.logger.warning(f"⚠️ GPS transmission failed for {vehicle_id}: {e}")
            
    def stop(self):
        """Stop the simulation"""
        self.logger.info("🛑 Stopping database-driven simulation...")
        
        # Stop GPS devices
        for vehicle_id, vehicle in self.vehicles.items():
            if vehicle['gps_device']:
                try:
                    vehicle['gps_device'].off()
                    self.logger.info(f"   📡 {vehicle_id}: GPS device stopped")
                except Exception as e:
                    self.logger.warning(f"   ⚠️ {vehicle_id}: GPS stop failed - {e}")
                    
        # Close database connection
        if self.db_conn:
            self.db_conn.close()
            
        if self.tunnel:
            self.tunnel.stop()
            
        self.logger.info("✅ Database-driven simulation stopped")
        
    def get_status(self) -> str:
        """Get current simulation status"""
        active_vehicles = [v for v in self.vehicles.values() if v['active']]
        gps_active = len([v for v in active_vehicles if v['gps_device']])
        
        status_lines = []
        for vehicle in active_vehicles:
            gps_indicator = "📡" if vehicle['gps_device'] else "🔒"
            route_name = vehicle['route_name'] or vehicle['route_id']
            status_lines.append(
                f"   {gps_indicator} {vehicle['id']}: {vehicle['status']} on {route_name} "
                f"at ({vehicle['position']['lat']:.6f}, {vehicle['position']['lng']:.6f}) "
                f"speed: {vehicle['speed']:.1f} km/h"
            )
            
        return f"🚌 {len(active_vehicles)} vehicles active ({gps_active} with GPS):\n" + "\n".join(status_lines)

def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Database-Driven Vehicle Simulator - Uses PostgreSQL backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          %(prog)s --debug                     Run with debug output
          %(prog)s --tick 0.5 --seconds 30     Run for 30 seconds, update every 0.5s
          %(prog)s --no-gps                    Run without GPS transmission
        """)
    )
    
    parser.add_argument(
        "--tick",
        type=float,
        default=1.0,
        help="Update interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=60.0,
        help="Simulation duration in seconds (default: 60.0)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--no-gps",
        action="store_true",
        help="Disable GPS transmission"
    )
    
    return parser

def main():
    """Main simulation entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    print("=" * 60)
    print("🚌 Database-Driven World Vehicles Simulator")
    print("=" * 60)
    print(f"⏱️  Update Interval: {args.tick} seconds")
    print(f"⏰ Duration: {args.seconds} seconds")
    print(f"📡 GPS Transmission: {'disabled' if args.no_gps else 'enabled'}")
    print(f"🐛 Debug: {'enabled' if args.debug else 'disabled'}")
    print(f"🗄️ Data Source: PostgreSQL Database")
    print("-" * 60)
    
    depot = None
    try:
        # Initialize depot
        depot = DatabaseVehiclesDepot(tick_time=args.tick)
        
        # Start simulation
        depot.start()
        
        # Main simulation loop
        start_time = time.time()
        last_status_time = 0
        
        while time.time() - start_time < args.seconds:
            depot.update()
            
            # Show status every 15 seconds
            current_time = time.time() - start_time
            if current_time - last_status_time >= 15:
                print(f"\n⏰ Time: {current_time:.1f}s")
                print(depot.get_status())
                last_status_time = current_time
            
            time.sleep(args.tick)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted by user")
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
    finally:
        if depot:
            depot.stop()
        print("-" * 60)
        print("✅ Database-driven simulation complete")
        
if __name__ == "__main__":
    main()
