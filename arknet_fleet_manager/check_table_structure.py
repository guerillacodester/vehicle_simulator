#!/usr/bin/env python3
import psycopg2

def check_table_structure():
    try:
        conn = psycopg2.connect(
            host='127.0.0.1',
            database='arknettransit', 
            user='david',
            password='Ga25w123!',
            port='5432'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name='vehicle_statuses' 
            ORDER BY ordinal_position
        """)
        
        print('Vehicle Status Table Structure:')
        for row in cursor.fetchall():
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            default = row[3] or ""
            print(f'  {row[0]}: {row[1]} ({nullable}) {default}')
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    check_table_structure()