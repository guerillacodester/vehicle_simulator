from config.database import get_ssh_tunnel, get_db_config
import psycopg2
import time

def verify_db_state():
    """Verify the current state of the database"""
    
    # Create SSH tunnel
    tunnel = get_ssh_tunnel()
    tunnel.start()
    time.sleep(2)  # Wait for tunnel to stabilize
    
    try:
        # Get database configuration
        db_config = get_db_config(tunnel)
        
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print(f"📋 Connected to database: {db_config['dbname']}")
        print(f"🌐 Host: {db_config['host']}:{db_config['port']}")
        
        # Check all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print('\n📊 All tables:')
        for table in tables:
            print(f'  {table[0]}')
        
        # Check all indexes
        cursor.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname LIKE '%shapes%'
            ORDER BY indexname
        """)
        indexes = cursor.fetchall()
        
        print('\n🔍 Shape-related indexes:')
        for index in indexes:
            print(f'  {index[0]} on {index[1]}')
        
        # Check alembic version
        cursor.execute("""
            SELECT version_num 
            FROM alembic_version 
            LIMIT 1
        """)
        version = cursor.fetchone()
        print(f'\n📈 Alembic version: {version[0] if version else "None"}')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        tunnel.stop()

if __name__ == "__main__":
    verify_db_state()
