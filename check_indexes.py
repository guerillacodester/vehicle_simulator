from config.database import get_ssh_tunnel, get_db_config
import psycopg2
import time

# Create SSH tunnel
tunnel = get_ssh_tunnel()
tunnel.start()
time.sleep(2)  # Wait for tunnel to stabilize

# Get database configuration
db_config = get_db_config(tunnel)

# Connect to database
conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

# Check existing indexes
cursor.execute("""
    SELECT indexname, tablename 
    FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND indexname LIKE '%shapes%'
    ORDER BY indexname
""")
indexes = cursor.fetchall()

print('Existing shape-related indexes:')
for index in indexes:
    print(f'  {index[0]} on table {index[1]}')

# Check if shapes table exists
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'shapes'
""")
shapes_table = cursor.fetchone()

print(f'\nShapes table exists: {shapes_table is not None}')

cursor.close()
conn.close()
tunnel.stop()
