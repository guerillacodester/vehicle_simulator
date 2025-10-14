"""Quick script to get a point from Route 1A"""
import psycopg2

conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    database='arknettransit',
    user='david',
    password='Ga25w123!'
)

cur = conn.cursor()

# Get middle point from Route 1A
cur.execute("""
    SELECT s.shape_pt_lat, s.shape_pt_lon, s.shape_pt_sequence
    FROM shapes s
    JOIN route_shapes rs ON s.shape_id = rs.shape_id
    WHERE rs.route_id = '1A'
    ORDER BY s.shape_pt_sequence
""")

rows = cur.fetchall()

if rows:
    print(f"Route 1A has {len(rows)} shape points")
    print("\nFirst 5 points:")
    for i, r in enumerate(rows[:5]):
        print(f"  {i+1}. ({r[0]}, {r[1]}) - sequence {r[2]}")
    
    print("\nMiddle 5 points:")
    mid = len(rows) // 2
    for i, r in enumerate(rows[mid:mid+5]):
        print(f"  {mid+i+1}. ({r[0]}, {r[1]}) - sequence {r[2]}")
    
    print("\n" + "="*80)
    print("SUGGESTED TEST POINT (middle of route):")
    test_point = rows[mid]
    print(f"Latitude:  {test_point[0]}")
    print(f"Longitude: {test_point[1]}")
    print(f"Sequence:  {test_point[2]}")
    print("="*80)
else:
    print("No Route 1A found")

cur.close()
conn.close()
