"""
Find Strapi Permissions Tables
"""
import psycopg2
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', 'arknet_fleet_manager', 'arknet-fleet-api', '.env')
load_dotenv(env_path)

DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', '127.0.0.1'),
    'port': os.getenv('DATABASE_PORT', '5432'),
    'database': os.getenv('DATABASE_NAME', 'arknettransit'),
    'user': os.getenv('DATABASE_USERNAME', 'david'),
    'password': os.getenv('DATABASE_PASSWORD', '')
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("🔍 Looking for permissions tables...")
    
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND (
            table_name LIKE '%permission%'
            OR table_name LIKE '%role%'
            OR table_name LIKE 'up_%'
        )
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    
    print(f"\nFound {len(tables)} related tables:")
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"  📋 {table_name} ({count} rows)")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
