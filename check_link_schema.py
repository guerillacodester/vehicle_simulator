"""Check link table schema"""
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

print("\n=== GEOFENCE_GEOMETRIES_GEOFENCE_LNK TABLE ===")
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'geofence_geometries_geofence_lnk'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Check sample data
print("\n=== SAMPLE DATA ===")
cursor.execute("""
    SELECT * FROM geofence_geometries_geofence_lnk
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  {row}")

cursor.close()
conn.close()
