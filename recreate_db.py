from config.database import get_ssh_tunnel, get_db_config
import psycopg2
import time

def recreate_database():
    """Drop and recreate the arknettransit database"""
    
    print("🔄 Recreating database...")
    
    # Create SSH tunnel
    tunnel = get_ssh_tunnel()
    tunnel.start()
    time.sleep(2)  # Wait for tunnel to stabilize
    
    try:
        # Get database configuration but connect to postgres database first
        db_config = get_db_config(tunnel)
        postgres_config = db_config.copy()
        postgres_config['dbname'] = 'postgres'  # Connect to postgres DB to drop/create other DBs
        
        # Connect to postgres database
        conn = psycopg2.connect(**postgres_config)
        conn.autocommit = True  # Required for DROP/CREATE DATABASE
        cursor = conn.cursor()
        
        print("📋 Connected to PostgreSQL server")
        
        # Terminate all connections to the target database
        print("🔌 Terminating existing connections...")
        cursor.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'arknettransit' AND pid <> pg_backend_pid()
        """)
        
        # Drop the database
        print("🗑️ Dropping arknettransit database...")
        cursor.execute("DROP DATABASE IF EXISTS arknettransit")
        
        # Create the database
        print("🏗️ Creating arknettransit database...")
        cursor.execute("CREATE DATABASE arknettransit")
        
        # Enable PostGIS extension
        cursor.close()
        conn.close()
        
        # Now connect to the new database to enable PostGIS
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("🌍 Enabling PostGIS extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        
        print("✅ Database recreated successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        tunnel.stop()

if __name__ == "__main__":
    recreate_database()
