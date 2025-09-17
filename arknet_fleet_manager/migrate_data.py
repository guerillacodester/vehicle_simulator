"""
Data Migration Script: Remote PostgreSQL to Local PostgreSQL
============================================================
This script migrates data from the remote arknetglobal.com PostgreSQL database
to the local PostgreSQL database for the Strapi fleet management system.
"""

import os
import sys
import psycopg2
import paramiko
import threading
import socket
import time
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SSHTunnel:
    """SSH Tunnel manager for database connection"""
    
    def __init__(self, ssh_host: str, ssh_port: int, ssh_user: str, ssh_pass: str,
                 remote_host: str, remote_port: int, local_port: int):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_pass = ssh_pass
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.local_port = local_port
        self.ssh_client = None
        self.forwarder = None
        
    def start(self):
        """Start SSH tunnel"""
        logger.info(f"Starting SSH tunnel to {self.ssh_host}:{self.ssh_port}")
        
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(
            self.ssh_host, 
            port=self.ssh_port, 
            username=self.ssh_user, 
            password=self.ssh_pass
        )
        
        self.forwarder = Forwarder(
            self.ssh_client.get_transport(),
            self.local_port,
            self.remote_host,
            self.remote_port
        )
        self.forwarder.start()
        
        # Wait a moment for tunnel to establish
        time.sleep(2)
        logger.info(f"SSH tunnel established on local port {self.local_port}")
        
    def stop(self):
        """Stop SSH tunnel"""
        if self.forwarder:
            self.forwarder.stop()
        if self.ssh_client:
            self.ssh_client.close()
        logger.info("SSH tunnel closed")

class Forwarder(threading.Thread):
    """Port forwarder for SSH tunnel"""
    daemon = True
    
    def __init__(self, transport, local_port, remote_host, remote_port):
        super().__init__()
        self.transport = transport
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.sock = None
        self._stop = threading.Event()

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", self.local_port))
        self.sock.listen(1)
        
        while not self._stop.is_set():
            try:
                client, _ = self.sock.accept()
                chan = self.transport.open_channel(
                    "direct-tcpip",
                    (self.remote_host, self.remote_port),
                    client.getsockname(),
                )
                threading.Thread(target=self._pipe, args=(client, chan), daemon=True).start()
                threading.Thread(target=self._pipe, args=(chan, client), daemon=True).start()
            except Exception as e:
                if not self._stop.is_set():
                    logger.error(f"Tunnel error: {e}")
                break

    def _pipe(self, src, dst):
        try:
            while True:
                data = src.recv(1024)
                if not data:
                    break
                dst.sendall(data)
        except Exception:
            pass
        finally:
            try:
                src.close()
                dst.close()
            except:
                pass

    def stop(self):
        self._stop.set()
        if self.sock:
            self.sock.close()

class DataMigrator:
    """Main data migration class"""
    
    def __init__(self):
        # Remote database configuration (via SSH tunnel)
        self.remote_config = {
            'host': '127.0.0.1',  # via tunnel
            'port': 6543,         # tunnel port
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
        
        # Define table migration order (respecting foreign key dependencies)
        self.table_order = [
            'countries',
            'depots', 
            'routes',
            'drivers',
            'gps_devices',
            'vehicles',
            'services',
            'shapes',
            'trips',
            'stops',
            'stop_times',
            'blocks',
            'block_breaks',
            'block_trips',
            'driver_assignments',
            'vehicle_assignments',
            'vehicle_status_events',
            'frequencies',
            'timetables',
            'route_shapes'
        ]
    
    def connect_databases(self):
        """Establish connections to both remote and local databases"""
        try:
            # Start SSH tunnel
            self.tunnel = SSHTunnel(**self.ssh_config)
            self.tunnel.start()
            
            # Connect to remote database (via tunnel)
            logger.info("Connecting to remote database via SSH tunnel...")
            self.remote_conn = psycopg2.connect(**self.remote_config, cursor_factory=RealDictCursor)
            logger.info("Remote database connected successfully")
            
            # Connect to local database
            logger.info("Connecting to local database...")
            self.local_conn = psycopg2.connect(**self.local_config, cursor_factory=RealDictCursor)
            logger.info("Local database connected successfully")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.cleanup()
            raise
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get table structure information"""
        with self.remote_conn.cursor() as cursor:
            # Get column information
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            # Get primary key information
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
            """, (table_name,))
            
            pk_columns = [row['column_name'] for row in cursor.fetchall()]
            
            return {
                'columns': columns,
                'primary_keys': pk_columns
            }
    
    def check_table_exists(self, table_name: str, connection) -> bool:
        """Check if table exists in database"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table_name,))
            return cursor.fetchone()[0]
    
    def get_table_data(self, table_name: str) -> List[Dict]:
        """Get all data from a remote table"""
        with self.remote_conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            return cursor.fetchall()
    
    def clear_table(self, table_name: str):
        """Clear all data from local table"""
        with self.local_conn.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
            self.local_conn.commit()
            logger.info(f"Cleared table: {table_name}")
    
    def insert_data(self, table_name: str, data: List[Dict]):
        """Insert data into local table"""
        if not data:
            logger.info(f"No data to insert for table: {table_name}")
            return
        
        # Get column names from first row
        columns = list(data[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join(columns)
        
        insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
        
        with self.local_conn.cursor() as cursor:
            try:
                for row in data:
                    values = [row[col] for col in columns]
                    cursor.execute(insert_sql, values)
                
                self.local_conn.commit()
                logger.info(f"Inserted {len(data)} rows into {table_name}")
                
            except Exception as e:
                self.local_conn.rollback()
                logger.error(f"Failed to insert data into {table_name}: {e}")
                raise
    
    def migrate_table(self, table_name: str):
        """Migrate a single table"""
        logger.info(f"Migrating table: {table_name}")
        
        # Check if table exists in remote database
        if not self.check_table_exists(table_name, self.remote_conn):
            logger.warning(f"Table {table_name} does not exist in remote database, skipping...")
            return
        
        # Check if table exists in local database
        if not self.check_table_exists(table_name, self.local_conn):
            logger.warning(f"Table {table_name} does not exist in local database, skipping...")
            return
        
        try:
            # Get data from remote table
            data = self.get_table_data(table_name)
            
            if data:
                # Clear local table first
                self.clear_table(table_name)
                
                # Insert data into local table
                self.insert_data(table_name, data)
            else:
                logger.info(f"Table {table_name} is empty in remote database")
                
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            raise
    
    def run_migration(self):
        """Run the complete data migration"""
        logger.info("Starting data migration from remote to local database...")
        
        try:
            self.connect_databases()
            
            # Migrate tables in dependency order
            for table_name in self.table_order:
                self.migrate_table(table_name)
            
            logger.info("Data migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up connections and tunnel"""
        if self.remote_conn:
            self.remote_conn.close()
            logger.info("Remote database connection closed")
        
        if self.local_conn:
            self.local_conn.close()
            logger.info("Local database connection closed")
        
        if self.tunnel:
            self.tunnel.stop()

def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("Starting ArkNet Transit Data Migration")
    logger.info("=" * 60)
    
    migrator = DataMigrator()
    
    try:
        migrator.run_migration()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()