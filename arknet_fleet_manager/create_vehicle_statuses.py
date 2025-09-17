#!/usr/bin/env python3
import psycopg2
from datetime import datetime

def create_vehicle_statuses():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host='127.0.0.1',
            database='arknettransit', 
            user='david',
            password='Ga25w123!',
            port='5432'
        )
        cursor = conn.cursor()
        
        # Create vehicle status records
        vehicle_statuses = [
            ('available', 'Available'),
            ('in_transit', 'In Transit'),
            ('maintenance', 'Under Maintenance'),
            ('out_of_service', 'Out of Service'),
            ('reserved', 'Reserved')
        ]
        
        current_time = datetime.now()
        
        # Check if records already exist
        cursor.execute("SELECT COUNT(*) FROM vehicle_statuses")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"Vehicle status records already exist ({existing_count} records)")
        else:
            for status_id, name in vehicle_statuses:
                cursor.execute("""
                    INSERT INTO vehicle_statuses (status_id, name, created_at, updated_at, published_at) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (status_id, name, current_time, current_time, current_time))
            
        conn.commit()
        print(f"✅ Successfully created {len(vehicle_statuses)} vehicle status records")
        
        # Verify the records
        cursor.execute("SELECT status_id, name FROM vehicle_statuses ORDER BY status_id")
        records = cursor.fetchall()
        print("\n📋 Vehicle Status Records:")
        for status_id, name in records:
            print(f"  - {status_id}: {name}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_vehicle_statuses()