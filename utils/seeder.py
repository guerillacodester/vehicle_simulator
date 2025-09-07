import uuid
import random
import datetime
import psycopg2
from psycopg2.extras import register_uuid
from typing import List, Dict, Tuple

class TransitSeeder:
    def __init__(self, db_params: Dict[str, str]):
        """Initialize database connection"""
        self.conn = psycopg2.connect(**db_params)
        register_uuid()
        
    def seed_vehicles(self, count: int = 50) -> List[uuid.UUID]:
        """Seed sample vehicles with random attributes"""
        vehicle_ids = []
        with self.conn.cursor() as cur:
            for _ in range(count):
                vehicle_id = uuid.uuid4()
                cur.execute("""
                    INSERT INTO vehicles (vehicle_id, status)
                    VALUES (%s, 'available')
                    RETURNING vehicle_id
                """, (vehicle_id,))
                vehicle_ids.append(cur.fetchone()[0])
        self.conn.commit()
        return vehicle_ids

    def seed_stops(self, count: int = 100) -> List[uuid.UUID]:
        """Seed bus stops with realistic coordinates"""
        stop_ids = []
        # Example coordinates for a city area
        base_lat, base_lon = 51.5074, -0.1278  # London center
        
        with self.conn.cursor() as cur:
            for _ in range(count):
                stop_id = uuid.uuid4()
                lat = base_lat + random.uniform(-0.1, 0.1)
                lon = base_lon + random.uniform(-0.1, 0.1)
                
                cur.execute("""
                    INSERT INTO stops (stop_id, geom)
                    VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    RETURNING stop_id
                """, (stop_id, lon, lat))
                stop_ids.append(cur.fetchone()[0])
        self.conn.commit()
        return stop_ids

    def seed_routes(self, stop_ids: List[uuid.UUID], count: int = 10) -> List[uuid.UUID]:
        """Create realistic bus routes between stops"""
        route_ids = []
        with self.conn.cursor() as cur:
            for _ in range(count):
                route_id = uuid.uuid4()
                # Select random stops for this route
                route_stops = random.sample(stop_ids, random.randint(5, 15))
                
                # Create route
                cur.execute("""
                    INSERT INTO routes (route_id)
                    VALUES (%s)
                    RETURNING route_id
                """, (route_id,))
                route_ids.append(cur.fetchone()[0])
                
                # Create route shape
                points = []
                for stop_id in route_stops:
                    cur.execute("""
                        SELECT ST_AsText(geom) FROM stops WHERE stop_id = %s
                    """, (stop_id,))
                    points.append(cur.fetchone()[0])
                
                # Create linestring from points
                linestring = f"LINESTRING({','.join(points)})"
                cur.execute("""
                    INSERT INTO route_shapes (route_id, geom, is_default)
                    VALUES (%s, ST_GeomFromText(%s, 4326), true)
                """, (route_id, linestring))

        self.conn.commit()
        return route_ids

    def seed_timetable(self, route_ids: List[uuid.UUID]) -> List[uuid.UUID]:
        """Create 24-hour timetable for routes"""
        timetable_ids = []
        
        with self.conn.cursor() as cur:
            for route_id in route_ids:
                # Create multiple departure times throughout the day
                start_time = datetime.time(5, 0)  # 5 AM start
                end_time = datetime.time(23, 0)   # 11 PM end
                
                current_time = start_time
                while current_time <= end_time:
                    timetable_id = uuid.uuid4()
                    
                    cur.execute("""
                        INSERT INTO timetables (timetable_id, route_id, departure_time)
                        VALUES (%s, %s, %s)
                        RETURNING timetable_id
                    """, (timetable_id, route_id, current_time))
                    
                    timetable_ids.append(cur.fetchone()[0])
                    
                    # Add 15-30 minutes between departures
                    minutes = random.randint(15, 30)
                    current_time = (datetime.datetime.combine(datetime.date.today(), current_time) + 
                                  datetime.timedelta(minutes=minutes)).time()
                    
        self.conn.commit()
        return timetable_ids