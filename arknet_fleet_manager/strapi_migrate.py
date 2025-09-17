"""
Strapi Data Migration Script
===========================
Custom migration script that maps data from the original FastAPI/SQLAlchemy schema
to the Strapi-generated schema with proper relationship handling.
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migrate_data import SSHTunnel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strapi_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrapiDataMigrator:
    """Strapi-aware data migrator"""
    
    def __init__(self):
        # Remote database configuration (via SSH tunnel)
        self.remote_config = {
            'host': '127.0.0.1',
            'port': 6543,
            'database': 'arknettransit',
            'user': 'david',
            'password': 'Ga25w123!'
        }
        
        # Local database configuration
        self.local_config = {
            'host': '127.0.0.1',
            'port': 5432,
            'database': 'arknettransit',
            'user': 'david',
            'password': 'Ga25w123!'
        }
        
        # SSH tunnel configuration
        self.ssh_config = {
            'ssh_host': 'arknetglobal.com',
            'ssh_port': 22,
            'ssh_user': 'david',
            'ssh_pass': 'Cabbyminnie5!',
            'remote_host': 'localhost',
            'remote_port': 5432,
            'local_port': 6543
        }
        
        self.tunnel = None
        self.remote_conn = None
        self.local_conn = None
        
        # Store mapping between remote UUIDs and local integer IDs
        self.id_mappings = {}
        
    def connect_databases(self):
        """Establish connections to both databases"""
        try:
            # Start SSH tunnel
            self.tunnel = SSHTunnel(**self.ssh_config)
            self.tunnel.start()
            
            # Connect to remote database
            logger.info("Connecting to remote database via SSH tunnel...")
            self.remote_conn = psycopg2.connect(**self.remote_config, cursor_factory=RealDictCursor)
            
            # Connect to local database
            logger.info("Connecting to local database...")
            self.local_conn = psycopg2.connect(**self.local_config, cursor_factory=RealDictCursor)
            
            logger.info("Both database connections established")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.cleanup()
            raise
    
    def clear_strapi_table(self, table_name):
        """Clear Strapi table and reset sequences"""
        with self.local_conn.cursor() as cursor:
            # Clear main table
            cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
            
            # Clear related link tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name LIKE %s AND table_schema = 'public'
            """, (f"{table_name}_%_lnk",))
            
            link_tables = cursor.fetchall()
            for link_table in link_tables:
                cursor.execute(f"TRUNCATE TABLE {link_table['table_name']} RESTART IDENTITY CASCADE")
                logger.info(f"Cleared link table: {link_table['table_name']}")
            
            self.local_conn.commit()
            logger.info(f"Cleared table: {table_name}")
    
    def get_strapi_defaults(self):
        """Get default Strapi field values"""
        now = datetime.now()
        return {
            'document_id': str(uuid.uuid4()),
            'created_at': now,
            'updated_at': now,
            'published_at': now,
            'created_by_id': None,
            'updated_by_id': None,
            'locale': None
        }
    
    def migrate_countries(self):
        """Migrate countries table"""
        logger.info("Migrating countries...")
        
        # Get remote data
        with self.remote_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM countries ORDER BY name")
            remote_countries = cursor.fetchall()
        
        if not remote_countries:
            logger.info("No countries found in remote database")
            return
        
        # Clear local table
        self.clear_strapi_table('countries')
        
        # Insert into local database
        with self.local_conn.cursor() as cursor:
            for country in remote_countries:
                strapi_defaults = self.get_strapi_defaults()
                
                # Map fields
                local_data = {
                    **strapi_defaults,
                    'country_id': str(country['country_id']),
                    'name': country['name'],
                    'code': country['iso_code'],
                    'is_active': True
                }
                
                # Insert
                columns = list(local_data.keys())
                values = list(local_data.values())
                placeholders = ', '.join(['%s'] * len(values))
                column_names = ', '.join(columns)
                
                cursor.execute(f"""
                    INSERT INTO countries ({column_names}) 
                    VALUES ({placeholders}) 
                    RETURNING id
                """, values)
                
                local_id = cursor.fetchone()['id']
                self.id_mappings['countries'][str(country['country_id'])] = local_id
        
        self.local_conn.commit()
        logger.info(f"Migrated {len(remote_countries)} countries")
    
    def migrate_depots(self):
        """Migrate depots table"""
        logger.info("Migrating depots...")
        
        with self.remote_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM depots ORDER BY name")
            remote_depots = cursor.fetchall()
        
        if not remote_depots:
            logger.info("No depots found in remote database")
            return
        
        self.clear_strapi_table('depots')
        
        with self.local_conn.cursor() as cursor:
            for depot in remote_depots:
                strapi_defaults = self.get_strapi_defaults()
                
                local_data = {
                    **strapi_defaults,
                    'depot_id': str(depot['depot_id']),
                    'name': depot['name'],
                    'address': depot.get('location_address'),
                    'location': depot.get('location'),
                    'capacity': depot.get('capacity', 50),
                    'is_active': True
                }
                
                columns = list(local_data.keys())
                values = list(local_data.values())
                placeholders = ', '.join(['%s'] * len(values))
                column_names = ', '.join(columns)
                
                cursor.execute(f"""
                    INSERT INTO depots ({column_names}) 
                    VALUES ({placeholders}) 
                    RETURNING id
                """, values)
                
                local_id = cursor.fetchone()['id']
                self.id_mappings['depots'][str(depot['depot_id'])] = local_id
                
                # Create country relationship
                if depot['country_id'] and str(depot['country_id']) in self.id_mappings['countries']:
                    country_local_id = self.id_mappings['countries'][str(depot['country_id'])]
                    cursor.execute("""
                        INSERT INTO depots_country_lnk (depot_id, country_id, depot_ord)
                        VALUES (%s, %s, %s)
                    """, (local_id, country_local_id, 1))
        
        self.local_conn.commit()
        logger.info(f"Migrated {len(remote_depots)} depots")
    
    def migrate_routes(self):
        """Migrate routes table"""
        logger.info("Migrating routes...")
        
        with self.remote_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM routes ORDER BY short_name")
            remote_routes = cursor.fetchall()
        
        if not remote_routes:
            logger.info("No routes found in remote database")
            return
        
        self.clear_strapi_table('routes')
        
        with self.local_conn.cursor() as cursor:
            for route in remote_routes:
                strapi_defaults = self.get_strapi_defaults()
                
                local_data = {
                    **strapi_defaults,
                    'route_id': str(route['route_id']),
                    'short_name': route['short_name'],
                    'long_name': route.get('long_name'),
                    'parishes': route.get('parishes'),
                    'description': route.get('description'),
                    'color': route.get('color'),
                    'is_active': route.get('is_active', True),
                    'valid_from': route.get('valid_from'),
                    'valid_to': route.get('valid_to')
                }
                
                columns = list(local_data.keys())
                values = list(local_data.values())
                placeholders = ', '.join(['%s'] * len(values))
                column_names = ', '.join(columns)
                
                cursor.execute(f"""
                    INSERT INTO routes ({column_names}) 
                    VALUES ({placeholders}) 
                    RETURNING id
                """, values)
                
                local_id = cursor.fetchone()['id']
                self.id_mappings['routes'][str(route['route_id'])] = local_id
                
                # Create country relationship
                if route['country_id'] and str(route['country_id']) in self.id_mappings['countries']:
                    country_local_id = self.id_mappings['countries'][str(route['country_id'])]
                    cursor.execute("""
                        INSERT INTO routes_country_lnk (route_id, country_id, route_ord)
                        VALUES (%s, %s, %s)
                    """, (local_id, country_local_id, 1))
        
        self.local_conn.commit()
        logger.info(f"Migrated {len(remote_routes)} routes")
    
    def migrate_drivers(self):
        """Migrate drivers table"""
        logger.info("Migrating drivers...")
        
        with self.remote_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM drivers ORDER BY name")
            remote_drivers = cursor.fetchall()
        
        if not remote_drivers:
            logger.info("No drivers found in remote database")
            return
        
        self.clear_strapi_table('drivers')
        
        with self.local_conn.cursor() as cursor:
            for driver in remote_drivers:
                strapi_defaults = self.get_strapi_defaults()
                
                local_data = {
                    **strapi_defaults,
                    'driver_id': str(driver['driver_id']),
                    'name': driver['name'],
                    'license_no': driver['license_no'],
                    'employment_status': driver.get('employment_status', 'active'),
                    'phone': None,
                    'email': None,
                    'hire_date': None
                }
                
                columns = list(local_data.keys())
                values = list(local_data.values())
                placeholders = ', '.join(['%s'] * len(values))
                column_names = ', '.join(columns)
                
                cursor.execute(f"""
                    INSERT INTO drivers ({column_names}) 
                    VALUES ({placeholders}) 
                    RETURNING id
                """, values)
                
                local_id = cursor.fetchone()['id']
                self.id_mappings['drivers'][str(driver['driver_id'])] = local_id
                
                # Create country relationship
                if driver['country_id'] and str(driver['country_id']) in self.id_mappings['countries']:
                    country_local_id = self.id_mappings['countries'][str(driver['country_id'])]
                    cursor.execute("""
                        INSERT INTO drivers_country_lnk (driver_id, country_id, driver_ord)
                        VALUES (%s, %s, %s)
                    """, (local_id, country_local_id, 1))
                
                # Create home depot relationship
                if driver.get('home_depot_id') and str(driver['home_depot_id']) in self.id_mappings['depots']:
                    depot_local_id = self.id_mappings['depots'][str(driver['home_depot_id'])]
                    cursor.execute("""
                        INSERT INTO drivers_home_depot_lnk (driver_id, depot_id, driver_ord)
                        VALUES (%s, %s, %s)
                    """, (local_id, depot_local_id, 1))
        
        self.local_conn.commit()
        logger.info(f"Migrated {len(remote_drivers)} drivers")
    
    def migrate_vehicles(self):
        """Migrate vehicles table"""
        logger.info("Migrating vehicles...")
        
        with self.remote_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM vehicles ORDER BY reg_code")
            remote_vehicles = cursor.fetchall()
        
        if not remote_vehicles:
            logger.info("No vehicles found in remote database")
            return
        
        self.clear_strapi_table('vehicles')
        
        with self.local_conn.cursor() as cursor:
            for vehicle in remote_vehicles:
                strapi_defaults = self.get_strapi_defaults()
                
                local_data = {
                    **strapi_defaults,
                    'vehicle_id': str(vehicle['vehicle_id']),
                    'reg_code': vehicle['reg_code'],
                    'status': vehicle.get('status', 'available'),
                    'capacity': vehicle.get('capacity', 11),
                    'profile_id': vehicle.get('profile_id'),
                    'notes': vehicle.get('notes'),
                    'max_speed_kmh': vehicle.get('max_speed_kmh', 25.0),
                    'acceleration_mps_2': vehicle.get('acceleration_mps2', 1.2),
                    'braking_mps_2': vehicle.get('braking_mps2', 1.8),
                    'eco_mode': vehicle.get('eco_mode', False),
                    'performance_profile': vehicle.get('performance_profile')
                }
                
                columns = list(local_data.keys())
                values = list(local_data.values())
                placeholders = ', '.join(['%s'] * len(values))
                column_names = ', '.join(columns)
                
                cursor.execute(f"""
                    INSERT INTO vehicles ({column_names}) 
                    VALUES ({placeholders}) 
                    RETURNING id
                """, values)
                
                local_id = cursor.fetchone()['id']
                self.id_mappings['vehicles'][str(vehicle['vehicle_id'])] = local_id
                
                # Create relationships
                relationships = [
                    ('country_id', 'vehicles_country_lnk', 'country_id', 'countries'),
                    ('home_depot_id', 'vehicles_home_depot_lnk', 'depot_id', 'depots'),
                    ('preferred_route_id', 'vehicles_preferred_route_lnk', 'route_id', 'routes'),
                    ('assigned_driver_id', 'vehicles_assigned_driver_lnk', 'driver_id', 'drivers')
                ]
                
                for remote_field, link_table, link_field, mapping_table in relationships:
                    if vehicle.get(remote_field) and str(vehicle[remote_field]) in self.id_mappings.get(mapping_table, {}):
                        related_local_id = self.id_mappings[mapping_table][str(vehicle[remote_field])]
                        cursor.execute(f"""
                            INSERT INTO {link_table} (vehicle_id, {link_field}, vehicle_ord)
                            VALUES (%s, %s, %s)
                        """, (local_id, related_local_id, 1))
        
        self.local_conn.commit()
        logger.info(f"Migrated {len(remote_vehicles)} vehicles")
    
    def run_migration(self):
        """Run the complete Strapi migration"""
        logger.info("=" * 60)
        logger.info("Starting Strapi Data Migration")
        logger.info("=" * 60)
        
        try:
            self.connect_databases()
            
            # Initialize ID mappings
            self.id_mappings = {
                'countries': {},
                'depots': {},
                'routes': {},
                'drivers': {},
                'vehicles': {},
                'gps_devices': {}
            }
            
            # Migrate in dependency order
            self.migrate_countries()
            self.migrate_depots()
            self.migrate_routes()
            self.migrate_drivers()
            self.migrate_vehicles()
            
            logger.info("=" * 60)
            logger.info("Migration completed successfully!")
            logger.info(f"ID Mappings created:")
            for table, mappings in self.id_mappings.items():
                logger.info(f"  {table}: {len(mappings)} records")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up connections and tunnel"""
        if self.remote_conn:
            self.remote_conn.close()
        if self.local_conn:
            self.local_conn.close()
        if self.tunnel:
            self.tunnel.stop()

def main():
    """Main execution function"""
    migrator = StrapiDataMigrator()
    
    try:
        migrator.run_migration()
        logger.info("🎉 Strapi migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()