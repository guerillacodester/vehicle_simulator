#!/usr/bin/env python3
"""
Inspect GPS device structure from remote database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor

tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
tunnel.start()

try:
    conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM gps_devices LIMIT 1')
    device = cursor.fetchone()
    print('Sample GPS device fields:')
    for key, value in device.items():
        print(f'  {key}: {value}')
    conn.close()
finally:
    tunnel.stop()