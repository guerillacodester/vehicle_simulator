"""
Database Direct Spawning API
============================
Uses direct database access to maintain single source of truth without circular dependency
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
import math

# Import database connection (using same DB as Strapi)
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("Installing psycopg2...")
    import subprocess
    subprocess.check_call(["pip", "install", "psycopg2-binary"])
    import psycopg2
    import psycopg2.extras

class DatabaseSpawningAPI:
    """Spawning API using direct database access - single source of truth"""
    
    def __init__(self):
        # Use same database connection as Strapi (load from .env file)
        try:
            from dotenv import load_dotenv
            load_dotenv()  # Load .env file
        except ImportError:
            # Load manually if dotenv not available
            env_file = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
        
        self.db_config = {
            'host': os.getenv('DATABASE_HOST', '127.0.0.1'),
            'port': int(os.getenv('DATABASE_PORT', '5432')),
            'database': os.getenv('DATABASE_NAME', 'arknettransit'),
            'user': os.getenv('DATABASE_USERNAME', 'david'),
            'password': os.getenv('DATABASE_PASSWORD', 'Ga25w123!')
        }
    
    async def get_database_data(self):
        """Fetch spawning data directly from database (same as Strapi uses)"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Fetch depots
            cursor.execute("""
                SELECT id, name, latitude, longitude, capacity, is_active 
                FROM depots 
                WHERE is_active = true AND latitude IS NOT NULL AND longitude IS NOT NULL
            """)
            depots = cursor.fetchall()
            
            # First, let's check what routes exist
            cursor.execute("SELECT id, document_id, short_name FROM routes WHERE published_at IS NOT NULL")
            route_check = cursor.fetchall()
            print(f"DEBUG: Found {len(route_check)} published routes")
            for route in route_check:
                print(f"DEBUG: Route - id: {route['id']}, document_id: {route['document_id']}, name: {route['short_name']}")
            
            # Check route_shapes
            cursor.execute("SELECT route_id, shape_id FROM route_shapes WHERE published_at IS NOT NULL LIMIT 3")
            shape_check = cursor.fetchall()
            print(f"DEBUG: Found {len(shape_check)} published route_shapes (showing first 3)")
            for shape in shape_check:
                print(f"DEBUG: Route_shape - route_id: {shape['route_id']}, shape_id: {shape['shape_id']}")
            
            # Fetch routes with their shapes using GTFS structure
            cursor.execute("""
                SELECT DISTINCT 
                    r.id,
                    r.document_id,
                    r.short_name, 
                    r.long_name,
                    rs.shape_id,
                    rs.variant_code,
                    r.is_active
                FROM routes r 
                JOIN route_shapes rs ON r.short_name = rs.route_id
                WHERE r.published_at IS NOT NULL 
                AND rs.published_at IS NOT NULL
                ORDER BY r.short_name, rs.variant_code
            """)
            routes = cursor.fetchall()
            print(f"DEBUG: JOIN resulted in {len(routes)} route records")
            
            # Fetch POIs
            cursor.execute("""
                SELECT id, name, latitude, longitude, poi_type, description
                FROM pois 
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """)
            pois = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'depots': depots,
                'routes': routes, 
                'pois': pois
            }
            
        except Exception as e:
            logging.error(f"❌ Database connection failed: {e}")
            # Fallback to reasonable defaults if DB unavailable
            return self._get_fallback_data()
    
    def _get_fallback_data(self):
        """Fallback data if database unavailable"""
        return {
            'depots': [
                {'id': 1, 'name': 'Bridgetown Terminal', 'latitude': 13.1132, 'longitude': -59.6103, 'capacity': 50},
                {'id': 2, 'name': 'Speightstown Terminal', 'latitude': 13.2501, 'longitude': -59.6326, 'capacity': 30},
            ],
            'routes': [
                {'id': 1, 'short_name': '1A', 'long_name': 'Bridgetown to Speightstown', 
                 'geometry_coordinates': [[[-59.6103, 13.1132], [-59.6326, 13.2501]]], 'coordinate_count': 387}
            ],
            'pois': [
                {'id': 1, 'name': 'Bridgetown Port', 'latitude': 13.1132, 'longitude': -59.6103, 'poi_type': 'transport'},
            ]
        }
    
    async def generate_spawn_requests(self, hour: int, time_window_minutes: int = 5):
        """Generate spawn requests using actual database data"""
        
        # Get data from database (single source of truth)
        data = await self.get_database_data()
        
        # Store db_config for use in route spawning
        self.db_config = {
            'host': os.getenv('DATABASE_HOST', '127.0.0.1'),
            'port': int(os.getenv('DATABASE_PORT', '5432')),
            'database': os.getenv('DATABASE_NAME', 'arknettransit'),
            'user': os.getenv('DATABASE_USERNAME', 'david'),
            'password': os.getenv('DATABASE_PASSWORD', 'Ga25w123!')
        }
        
        spawn_requests = []
        
        # Calculate spawn multiplier based on hour
        spawn_multipliers = {
            6: 1.2, 7: 1.8, 8: 2.5, 9: 1.5,  # Morning rush
            12: 1.3, 13: 1.1,                   # Lunch
            17: 2.2, 18: 2.0, 19: 1.4,         # Evening rush
        }
        base_multiplier = spawn_multipliers.get(hour, 0.7)
        print(f"DEBUG: Hour {hour}, multiplier: {base_multiplier}, time_window: {time_window_minutes}")
        
        # Generate depot spawns
        for depot in data['depots']:
            capacity = depot.get('capacity', 50)
            base_spawn_rate = math.sqrt(capacity) * 0.5
            spawn_count = max(1, int(base_spawn_rate * base_multiplier * time_window_minutes * 0.1))
            
            for _ in range(spawn_count):
                spawn_requests.append({
                    "latitude": depot['latitude'],
                    "longitude": depot['longitude'],
                    "spawn_type": "depot",
                    "location_name": depot['name'],
                    "zone_type": "depot",
                    "zone_population": capacity,
                    "spawn_rate": base_spawn_rate * base_multiplier,
                    "minute": random.randint(0, 59),
                    "depot_id": depot['id']
                })
        
        # Generate route spawns using GTFS structure (routes -> route_shapes -> shapes)
        processed_shapes = set()  # Track processed shapes to avoid duplicates
        
        print(f"DEBUG: Found {len(data.get('routes', []))} routes in data")
        for i, route in enumerate(data['routes']):
            print(f"DEBUG: Route {i}: {route.get('short_name')} - shape_id: {route.get('shape_id')}")
            
        for route in data['routes']:
            shape_id = route.get('shape_id')
            if shape_id and shape_id not in processed_shapes:
                processed_shapes.add(shape_id)
                
                try:
                    # Get shape coordinates from shapes table
                    conn = psycopg2.connect(**self.db_config)
                    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    
                    cursor.execute("""
                        SELECT shape_pt_lat, shape_pt_lon, shape_pt_sequence
                        FROM shapes 
                        WHERE shape_id = %s 
                        AND published_at IS NOT NULL
                        ORDER BY shape_pt_sequence
                    """, (shape_id,))
                    
                    shape_points = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    
                    if shape_points:
                        # Convert to coordinate pairs (lon, lat) 
                        all_coords = [[point['shape_pt_lon'], point['shape_pt_lat']] for point in shape_points]
                        
                        coord_count = len(all_coords)
                        if coord_count > 0:
                            base_spawn_rate = min(coord_count, 100) * 0.02
                            calculation = base_spawn_rate * base_multiplier * time_window_minutes * 0.3
                            spawn_count = max(0, int(calculation))
                            print(f"Route {route.get('short_name')} shape {shape_id}: {coord_count} coords, base_rate={base_spawn_rate}, calc={calculation}, spawn_count={spawn_count}")
                            
                            # Create route display name with variant if available
                            route_display_name = f"Route {route['short_name']}"
                            if route.get('long_name'):
                                route_display_name += f" - {route['long_name']}"
                            if route.get('variant_code'):
                                route_display_name += f" ({route['variant_code']})"
                            
                            for _ in range(spawn_count):
                                coord = random.choice(all_coords)
                                if len(coord) >= 2:
                                    # Add small spatial variation
                                    lat = coord[1] + random.gauss(0, 0.0002)
                                    lon = coord[0] + random.gauss(0, 0.0002)
                                    
                                    spawn_requests.append({
                                        "latitude": round(lat, 6),
                                        "longitude": round(lon, 6),
                                        "spawn_type": "route",
                                        "location_name": route_display_name,
                                        "zone_type": "route", 
                                        "zone_population": coord_count,
                                        "spawn_rate": base_spawn_rate * base_multiplier,
                                        "minute": random.randint(0, 59),
                                        "route_id": route['id'],
                                        "shape_id": shape_id,
                                        "variant_code": route.get('variant_code', 'default')
                                    })
                                    
                except Exception as e:
                    print(f"Error processing route {route.get('short_name')} shape {shape_id}: {e}")
                    continue
        
        # Generate POI spawns
        for poi in data['pois']:
            poi_type = poi.get('poi_type', 'unknown')
            base_spawn_rate = 2.0 if poi_type in ['transport', 'commercial'] else 1.0
            spawn_count = max(0, int(base_spawn_rate * base_multiplier * time_window_minutes * 0.1))
            
            for _ in range(spawn_count):
                # Add spatial variation around POI
                lat = poi['latitude'] + random.gauss(0, 0.0003)
                lon = poi['longitude'] + random.gauss(0, 0.0003)
                
                spawn_requests.append({
                    "latitude": round(lat, 6),
                    "longitude": round(lon, 6),
                    "spawn_type": "poi",
                    "location_name": poi['name'],
                    "zone_type": poi_type,
                    "zone_population": 100,  # Estimated POI activity
                    "spawn_rate": base_spawn_rate * base_multiplier,
                    "minute": random.randint(0, 59),
                    "poi_id": poi['id']
                })
        
        return spawn_requests

# Global instance
spawning_api = DatabaseSpawningAPI()

async def handle_spawn_request(hour: int, time_window_minutes: int = 5) -> Dict[str, Any]:
    """Main entry point for spawning API"""
    try:
        spawn_requests = await spawning_api.generate_spawn_requests(hour, time_window_minutes)
        
        logging.info(f"✅ Generated {len(spawn_requests)} spawn requests from database")
        
        return {
            "success": True,
            "spawn_requests": spawn_requests,
            "hour": hour,
            "total_passengers": len(spawn_requests),
            "time_window_minutes": time_window_minutes
        }
        
    except Exception as e:
        logging.error(f"❌ Database spawning failed: {e}")
        return {
            "success": False,
            "error": f"Database spawning failed: {str(e)}",
            "spawn_requests": []
        }

if __name__ == "__main__":
    import sys
    
    # Get parameters from command line arguments or use defaults
    hour = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    time_window_minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Execute the spawning request
    result = asyncio.run(handle_spawn_request(hour, time_window_minutes))
    
    # Output in the format expected by the TypeScript controller
    print('RESULT_START')
    print(json.dumps(result))
    print('RESULT_END')
    
    # Count spawns by type and show summary AFTER the JSON
    spawn_counts = {}
    for passenger in result.get('passengers', []):
        spawn_type = passenger.get('spawn_type', 'unknown')
        spawn_counts[spawn_type] = spawn_counts.get(spawn_type, 0) + 1
    
    print(f"\nSPAWN SUMMARY:")
    print(f"Total passengers: {result.get('total_passengers', 0)}")
    for spawn_type, count in spawn_counts.items():
        print(f"  {spawn_type.capitalize()} spawns: {count}")