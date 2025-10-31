#!/usr/bin/env python3
"""Check if Route 1 has spawn configuration"""
import psycopg2
import os
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

# Check Route 1 spawn config
cur.execute("""
    SELECT 
        r.short_name,
        sc.id,
        sc.name,
        sc.config IS NOT NULL as has_config
    FROM routes r
    LEFT JOIN spawn_configs_route_lnk scrl ON r.id = scrl.route_id
    LEFT JOIN spawn_configs sc ON scrl.spawn_config_id = sc.id
    WHERE r.short_name = '1'
""")

result = cur.fetchone()
if result:
    print(f"Route: {result[0]}")
    print(f"Config ID: {result[1]}")
    print(f"Config Name: {result[2]}")
    print(f"Has Config: {'YES ✅' if result[3] else 'NO ❌'}")
else:
    print("Route 1 not found!")

cur.close()
conn.close()
