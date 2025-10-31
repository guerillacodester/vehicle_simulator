import psycopg2, os
from dotenv import load_dotenv

load_dotenv('arknet_fleet_manager/arknet-fleet-api/.env')
conn = psycopg2.connect(
    host=os.getenv('DATABASE_HOST', 'localhost'),
    port=os.getenv('DATABASE_PORT', '5432'),
    database=os.getenv('DATABASE_NAME', 'arknettransit'),
    user=os.getenv('DATABASE_USERNAME', 'david'),
    password=os.getenv('DATABASE_PASSWORD')
)
cur = conn.cursor()

# Find tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    AND (table_name LIKE '%hourly%' OR table_name LIKE '%day%')
    ORDER BY table_name
""")

print("Relevant tables:")
for row in cur.fetchall():
    print(f"  {row[0]}")

# Check hourly patterns
cur.execute("""
    SELECT hp.* 
    FROM components_spawning_hourly_patterns hp
    JOIN spawn_configs_cmps scc ON hp.id = scc.cmp_id
    WHERE scc.entity_id = 13
    ORDER BY hp.hour
    LIMIT 5
""")
print("\nHourly patterns (first 5):")
cols = [desc[0] for desc in cur.description]
print(f"Columns: {cols}")
for row in cur.fetchall():
    print(f"  Hour {row[1]}: rate {row[2]}")

# Check day multipliers  
cur.execute("""
    SELECT dm.* 
    FROM components_spawning_day_multipliers dm
    JOIN spawn_configs_cmps scc ON dm.id = scc.cmp_id
    WHERE scc.entity_id = 13
    ORDER BY dm.id
""")
print("\nDay multipliers:")
for row in cur.fetchall():
    print(f"  {row[1]}: {row[2]}")

conn.close()
