from config.database import get_ssh_tunnel, get_db_config
import psycopg2
import time

def test_direct_sql():
    """Test creating shapes table directly with SQL"""
    
    # Create SSH tunnel
    tunnel = get_ssh_tunnel()
    tunnel.start()
    time.sleep(2)  # Wait for tunnel to stabilize
    
    try:
        # Get database configuration
        db_config = get_db_config(tunnel)
        
        # Connect to database
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("🧪 Testing direct SQL...")
        
        # Try to create shapes table directly
        cursor.execute("""
            CREATE TABLE shapes (
                shape_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                geom GEOMETRY(LINESTRING, 4326) NOT NULL
            )
        """)
        print("✅ Created shapes table")
        
        # Try to create the index
        cursor.execute("""
            CREATE INDEX idx_shapes_geom ON shapes USING gist (geom)
        """)
        print("✅ Created idx_shapes_geom index")
        
        # Check if the table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'shapes'
        """)
        result = cursor.fetchone()
        print(f"📊 Shapes table exists: {result is not None}")
        
        # Check if the index exists
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE indexname = 'idx_shapes_geom'
        """)
        result = cursor.fetchone()
        print(f"🔍 Index exists: {result is not None}")
        
        # Clean up - drop the table
        cursor.execute("DROP TABLE shapes CASCADE")
        print("🧹 Cleaned up test table")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        tunnel.stop()

if __name__ == "__main__":
    test_direct_sql()
