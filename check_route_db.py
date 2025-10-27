import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv('arknet_fleet_manager/arknet-fleet-api/.env')

conn = psycopg2.connect(
    host=os.getenv('DATABASE_HOST'),
    port=os.getenv('DATABASE_PORT'),
    database=os.getenv('DATABASE_NAME'),
    user=os.getenv('DATABASE_USERNAME'),
    password=os.getenv('DATABASE_PASSWORD')
)
cur = conn.cursor()

# First check what columns exist
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'routes' ORDER BY ordinal_position")
columns = [row[0] for row in cur.fetchall()]
print("Columns in routes table:")
print(columns)
print()

# Get Route 1 data
cur.execute("SELECT * FROM routes WHERE short_name = %s", ('1',))
row = cur.fetchone()

if row:
    print("Route 1 data:")
    for i, col in enumerate(columns):
        if col == 'geojson_data' and row[i]:
            geojson = row[i] if isinstance(row[i], dict) else json.loads(row[i])
            print(f"  {col}: GeoJSON keys: {list(geojson.keys())}")
            if 'geometry' in geojson:
                coords = geojson['geometry']['coordinates']
            elif 'coordinates' in geojson:
                coords = geojson['coordinates']
            else:
                print(f"    GeoJSON structure: {geojson}")
                continue
            print(f"    {len(coords)} coordinates")
            
            # Calculate distance
            from math import radians, cos, sin, asin, sqrt
            def haversine(lon1, lat1, lon2, lat2):
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                return c * 6371000
            
            total_dist = sum(haversine(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1]) 
                           for i in range(len(coords)-1))
            print(f"  CALCULATED DISTANCE: {total_dist:.0f}m ({total_dist/1000:.2f}km)")
        elif isinstance(row[i], str) and len(str(row[i])) > 100:
            print(f"  {col}: {len(str(row[i]))} chars")
        else:
            print(f"  {col}: {row[i]}")
else:
    print("Route 1 not found!")

cur.close()
conn.close()
