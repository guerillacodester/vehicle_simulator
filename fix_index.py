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

# Check if shapes table exists (including in all schemas)
cursor.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_name = 'shapes'
""")
shapes_tables = cursor.fetchall()

print('Shapes tables in all schemas:')
for table in shapes_tables:
    print(f'  {table[0]}.{table[1]}')

print()

# Check for any index with this name (including hidden ones)
cursor.execute("""
    SELECT schemaname, tablename, indexname, indexdef
    FROM pg_indexes 
    WHERE indexname = 'idx_shapes_geom'
""")
indexes = cursor.fetchall()

print('Indexes named idx_shapes_geom:')
for idx in indexes:
    print(f'  {idx[0]}.{idx[1]}.{idx[2]}: {idx[3]}')

print()

# Let's try to drop this index if it exists
try:
    cursor.execute("DROP INDEX IF EXISTS idx_shapes_geom")
    conn.commit()
    print("Successfully dropped index idx_shapes_geom")
except Exception as e:
    print(f"Error dropping index: {e}")

cursor.close()
conn.close()
tunnel.stop()
