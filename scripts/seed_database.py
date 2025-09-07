import sys
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import WKTElement

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import Base, Vehicle, Route, Stop, Timetable
from config.database import get_ssh_tunnel, get_db_config

class DatabaseSeeder:
    def __init__(self):
        self.tunnel = None
        self.session = None
        
    def setup_connection(self):
        """Setup database connection with SSH tunnel"""
        print("Setting up database connection...")
        self.tunnel = get_ssh_tunnel()
        self.tunnel.start()
        
        db_config = get_db_config(self.tunnel)
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        engine = create_engine(connection_string)
        
        Session = sessionmaker(bind=engine)
        self.session = Session()
        print("Database connection established!")
        
    def seed_routes(self):
        """Seed basic transit routes"""
        print("Seeding routes...")
        
        routes_data = [
            {
                'route_id': 'R001',
                'name': 'Downtown Express',
                'shape': WKTElement('LINESTRING(-73.935242 40.730610, -73.925242 40.740610)', srid=4326)
            },
            {
                'route_id': 'R002', 
                'name': 'North-South Line',
                'shape': WKTElement('LINESTRING(-73.935242 40.730610, -73.935242 40.750610)', srid=4326)
            },
            {
                'route_id': 'R003',
                'name': 'East-West Connector',
                'shape': WKTElement('LINESTRING(-73.945242 40.730610, -73.915242 40.730610)', srid=4326)
            }
        ]
        
        for route_data in routes_data:
            existing = self.session.query(Route).filter_by(route_id=route_data['route_id']).first()
            if not existing:
                # Let the database auto-generate the id
                route = Route()
                route.route_id = route_data['route_id']
                route.name = route_data['name']
                route.shape = route_data['shape']
                self.session.add(route)
                
        self.session.commit()
        print(f"Seeded {len(routes_data)} routes")
        
    def seed_stops(self):
        """Seed bus stops"""
        print("Seeding stops...")
        
        stops_data = [
            {
                'stop_id': 'S001',
                'name': 'Central Station',
                'location': WKTElement('POINT(-73.935242 40.730610)', srid=4326)
            },
            {
                'stop_id': 'S002',
                'name': 'Market Square',
                'location': WKTElement('POINT(-73.925242 40.740610)', srid=4326)
            },
            {
                'stop_id': 'S003',
                'name': 'University Campus',
                'location': WKTElement('POINT(-73.935242 40.750610)', srid=4326)
            },
            {
                'stop_id': 'S004',
                'name': 'Shopping Center',
                'location': WKTElement('POINT(-73.915242 40.730610)', srid=4326)
            }
        ]
        
        for stop_data in stops_data:
            existing = self.session.query(Stop).filter_by(stop_id=stop_data['stop_id']).first()
            if not existing:
                # Let the database auto-generate the id
                stop = Stop()
                stop.stop_id = stop_data['stop_id']
                stop.name = stop_data['name']
                stop.location = stop_data['location']
                self.session.add(stop)
                
        self.session.commit()
        print(f"Seeded {len(stops_data)} stops")
        
    def seed_vehicles(self):
        """Seed fleet vehicles from existing JSON"""
        print("Seeding vehicles...")
        
        # Load existing vehicle data
        vehicles_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'world', 'vehicles.json')
        with open(vehicles_file, 'r') as f:
            vehicle_config = json.load(f)
        
        # Add vehicles from JSON file
        vehicles_data = vehicle_config.get('vehicles', [])
        
        # Also add the ZR1001 vehicle
        vehicles_data.append({
            'id': 'ZR1001',
            'route_id': 'R001',  # Assign to route 1
            'status': 'active'
        })
        
        for vehicle_data in vehicles_data:
            vehicle_id = vehicle_data.get('id')
            route_id = vehicle_data.get('route_id')
            status = vehicle_data.get('status', 'active')
            
            existing = self.session.query(Vehicle).filter_by(vehicle_id=vehicle_id).first()
            if not existing:
                # Let the database auto-generate the id
                vehicle = Vehicle()
                vehicle.vehicle_id = vehicle_id
                vehicle.status = status
                vehicle.route_id = route_id
                self.session.add(vehicle)
                
        self.session.commit()
        print(f"Seeded {len(vehicles_data)} vehicles")
        
    def seed_timetables(self):
        """Seed basic timetables"""
        print("Seeding timetables...")
        
        base_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        
        timetables_data = []
        
        # Create hourly departures for each route
        for route_id in ['R001', 'R002', 'R003']:
            for hour in range(6, 22):  # 6 AM to 10 PM
                departure_time = base_time + timedelta(hours=hour-6)
                timetables_data.append({
                    'route_id': route_id,
                    'departure_time': departure_time,
                    'vehicle_id': f'BUS00{route_id[-1]}'  # Simple assignment
                })
        
        for timetable_data in timetables_data:
            existing = self.session.query(Timetable).filter_by(
                route_id=timetable_data['route_id'],
                departure_time=timetable_data['departure_time']
            ).first()
            
            if not existing:
                # Let the database auto-generate the id
                timetable = Timetable()
                timetable.route_id = timetable_data['route_id']
                timetable.departure_time = timetable_data['departure_time']
                timetable.vehicle_id = timetable_data['vehicle_id']
                self.session.add(timetable)
                
        self.session.commit()
        print(f"Seeded {len(timetables_data)} timetable entries")
        
    def cleanup(self):
        """Clean up connections"""
        if self.session:
            self.session.close()
        if self.tunnel:
            self.tunnel.stop()
            
    def seed_all(self):
        """Run all seeding operations"""
        try:
            self.setup_connection()
            self.seed_routes()
            self.seed_stops()
            self.seed_vehicles()
            self.seed_timetables()
            print("\n✅ Database seeding completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            if self.session:
                self.session.rollback()
        finally:
            self.cleanup()

if __name__ == "__main__":
    seeder = DatabaseSeeder()
    seeder.seed_all()