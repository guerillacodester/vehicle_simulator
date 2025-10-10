"""Check for Strapi link tables"""
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

# Find all tables with 'geofence' in the name
print("\n=== ALL GEOFENCE-RELATED TABLES ===")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%geofence%'
    ORDER BY table_name
""")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# Find link tables
print("\n=== ALL LINK TABLES ===")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%_lnk'
    ORDER BY table_name
""")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

cursor.close()
conn.close()
