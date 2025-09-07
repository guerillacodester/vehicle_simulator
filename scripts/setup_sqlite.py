#!/usr/bin/env python3
"""
SQLite Database Setup for Development
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def create_sqlite_database():
    """Create SQLite database with our tables"""
    db_path = "vehicle_simulator.db"
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Removed existing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"📝 Creating SQLite database: {db_path}")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id TEXT UNIQUE NOT NULL,
            name TEXT,
            shape TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'active',
            route_id TEXT,
            FOREIGN KEY (route_id) REFERENCES routes (route_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE stops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stop_id TEXT UNIQUE NOT NULL,
            name TEXT,
            location TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE timetables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id TEXT,
            departure_time DATETIME NOT NULL,
            vehicle_id TEXT,
            FOREIGN KEY (route_id) REFERENCES routes (route_id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id)
        )
    """)
    
    print("✅ Tables created successfully")
    
    # Insert sample data
    print("📊 Inserting sample data...")
    
    # Routes
    routes = [
        ('R001', 'Downtown Express'),
        ('R002', 'North-South Line'),
        ('R003', 'East-West Connector')
    ]
    
    cursor.executemany("INSERT INTO routes (route_id, name) VALUES (?, ?)", routes)
    
    # Vehicles
    vehicles = [
        ('BUS001', 'active', 'R001'),
        ('BUS002', 'active', 'R002'),
        ('BUS003', 'active', 'R003'),
        ('ZR1001', 'active', 'R001'),
        ('BUS004', 'maintenance', None)
    ]
    
    cursor.executemany("INSERT INTO vehicles (vehicle_id, status, route_id) VALUES (?, ?, ?)", vehicles)
    
    # Stops
    stops = [
        ('S001', 'Central Station'),
        ('S002', 'Market Square'),
        ('S003', 'University Campus'),
        ('S004', 'Shopping Center')
    ]
    
    cursor.executemany("INSERT INTO stops (stop_id, name) VALUES (?, ?)", stops)
    
    # Timetables (sample hourly departures)
    base_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    timetables = []
    
    for route_id in ['R001', 'R002', 'R003']:
        for hour in range(6, 22):  # 6 AM to 10 PM
            departure_time = base_time + timedelta(hours=hour-6)
            vehicle_id = f'BUS00{route_id[-1]}'
            timetables.append((route_id, departure_time, vehicle_id))
    
    cursor.executemany("INSERT INTO timetables (route_id, departure_time, vehicle_id) VALUES (?, ?, ?)", timetables)
    
    conn.commit()
    
    # Verify data
    cursor.execute("SELECT COUNT(*) FROM routes")
    route_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    vehicle_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stops")
    stop_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM timetables")
    timetable_count = cursor.fetchone()[0]
    
    print(f"✅ Data inserted: {route_count} routes, {vehicle_count} vehicles, {stop_count} stops, {timetable_count} timetables")
    
    conn.close()
    return db_path

def test_sqlite_database(db_path):
    """Test the SQLite database"""
    print(f"\n🔬 Testing SQLite database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("""
        SELECT v.vehicle_id, v.status, r.name as route_name 
        FROM vehicles v 
        LEFT JOIN routes r ON v.route_id = r.route_id 
        WHERE v.status = 'active'
    """)
    
    vehicles = cursor.fetchall()
    print(f"🚌 Active vehicles:")
    for vehicle_id, status, route_name in vehicles:
        print(f"   • {vehicle_id}: {status} on {route_name or 'No route'}")
    
    conn.close()
    return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("🏗️  SQLite Database Setup for Development")
    print("=" * 60)
    
    try:
        db_path = create_sqlite_database()
        test_sqlite_database(db_path)
        
        print(f"\n✅ SQLite database ready: {db_path}")
        print("   You can now use this for development instead of PostgreSQL")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()
