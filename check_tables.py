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

# Check existing tables
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
tables = cursor.fetchall()

print('Existing tables:')
for table in tables:
    print(f'  {table[0]}')

cursor.close()
conn.close()
tunnel.stop()
