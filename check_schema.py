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

# Check vehicles table schema
cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'vehicles'
    ORDER BY ordinal_position
""")
columns = cursor.fetchall()

print('Vehicles table columns:')
for col in columns:
    print(f'  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})')

print('\n' + '='*50)

# Check routes table schema
cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'routes'
    ORDER BY ordinal_position
""")
columns = cursor.fetchall()

print('Routes table columns:')
for col in columns:
    print(f'  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})')

cursor.close()
conn.close()
tunnel.stop()
