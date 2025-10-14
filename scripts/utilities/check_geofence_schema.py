"""Check the actual database schema for geofence tables"""
import psycopg2

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Check geofences table
print("\n=== GEOFENCES TABLE ===")
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'geofences'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Check geofence_geometries table
print("\n=== GEOFENCE_GEOMETRIES TABLE ===")
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'geofence_geometries'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Check geometry_points table
print("\n=== GEOMETRY_POINTS TABLE ===")
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'geometry_points'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

cursor.close()
conn.close()
