import psycopg2
import os
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

# Check spawn-config 10
cur.execute('SELECT id, name FROM spawn_configs WHERE id = 10')
config = cur.fetchone()
print(f"Config: {config}")

# Check components
cur.execute('SELECT cmp_id, component_type, field FROM spawn_configs_cmps WHERE entity_id = 10 ORDER BY field, "order"')
rows = cur.fetchall()
print(f'\nTotal components: {len(rows)}')

# Group by field
from collections import defaultdict
by_field = defaultdict(list)
for row in rows:
    by_field[row[2]].append(row)

for field, comps in by_field.items():
    print(f'  {field}: {len(comps)} components')

cur.close()
conn.close()
