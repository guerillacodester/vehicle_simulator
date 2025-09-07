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

# Check all indexes
cursor.execute("""
    SELECT indexname, tablename, indexdef
    FROM pg_indexes 
    WHERE schemaname = 'public' 
    ORDER BY indexname
""")
indexes = cursor.fetchall()

print('All indexes:')
for index in indexes:
    print(f'  {index[0]} on {index[1]}: {index[2]}')

cursor.close()
conn.close()
tunnel.stop()
