#!/usr/bin/env python3
"""
QUICK FIX: Add spatial_base, hourly_rates, and day_multipliers JSON fields
to distribution_params component table and populate with proper data.

This is a temporary fix until schema can be properly refactored.
"""
import psycopg2
import os
import json
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

try:
    print("🔧 QUICK FIX: Adding missing fields to distribution_params")
    print("=" * 70)
    
    # 1. Check if columns exist
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'components_spawning_distribution_params'
    """)
    existing_columns = [row[0] for row in cur.fetchall()]
    print(f"Existing columns: {', '.join(existing_columns)}")
    
    # 2. Add missing columns if needed
    if 'spatial_base' not in existing_columns:
        print("\n➕ Adding spatial_base column...")
        cur.execute("""
            ALTER TABLE components_spawning_distribution_params 
            ADD COLUMN spatial_base NUMERIC(5,2) DEFAULT 2.0
        """)
        print("✅ Added spatial_base")
    
    if 'hourly_rates' not in existing_columns:
        print("\n➕ Adding hourly_rates column...")
        cur.execute("""
            ALTER TABLE components_spawning_distribution_params 
            ADD COLUMN hourly_rates JSONB
        """)
        print("✅ Added hourly_rates")
    
    if 'day_multipliers' not in existing_columns:
        print("\n➕ Adding day_multipliers column...")
        cur.execute("""
            ALTER TABLE components_spawning_distribution_params 
            ADD COLUMN day_multipliers JSONB
        """)
        print("✅ Added day_multipliers")
    
    conn.commit()
    
    # 3. Populate data for Route 1's config (ID: 10)
    print("\n📝 Populating data for Route 1 spawn config...")
    
    hourly_rates = {
        "0": 0.1,    # Midnight
        "1": 0.05,   # 1 AM
        "2": 0.05,   # 2 AM
        "3": 0.05,   # 3 AM
        "4": 0.2,    # 4 AM
        "5": 0.5,    # 5 AM
        "6": 0.8,    # 6 AM - Morning commute starts
        "7": 1.5,    # 7 AM - Peak morning
        "8": 2.0,    # 8 AM - Rush hour (PEAK)
        "9": 1.2,    # 9 AM
        "10": 0.8,   # 10 AM
        "11": 0.7,   # 11 AM
        "12": 0.9,   # Noon
        "13": 0.8,   # 1 PM
        "14": 0.7,   # 2 PM
        "15": 1.0,   # 3 PM - School dismissal
        "16": 1.8,   # 4 PM - Evening rush builds
        "17": 2.2,   # 5 PM - Peak evening (PEAK)
        "18": 1.5,   # 6 PM
        "19": 1.0,   # 7 PM
        "20": 0.6,   # 8 PM
        "21": 0.4,   # 9 PM
        "22": 0.3,   # 10 PM
        "23": 0.2    # 11 PM
    }
    
    day_multipliers = {
        "0": 1.3,    # Monday
        "1": 1.3,    # Tuesday
        "2": 1.3,    # Wednesday
        "3": 1.3,    # Thursday
        "4": 1.3,    # Friday
        "5": 0.6,    # Saturday
        "6": 0.3     # Sunday
    }
    
    cur.execute("""
        UPDATE components_spawning_distribution_params
        SET spatial_base = %s,
            hourly_rates = %s,
            day_multipliers = %s
        WHERE id = 10
    """, (2.0, json.dumps(hourly_rates), json.dumps(day_multipliers)))
    
    conn.commit()
    
    # 4. Verify
    cur.execute("""
        SELECT spatial_base, hourly_rates, day_multipliers
        FROM components_spawning_distribution_params
        WHERE id = 10
    """)
    result = cur.fetchone()
    
    print("\n✅ Data populated successfully!")
    print(f"   spatial_base: {result[0]}")
    # JSONB returns as dict in psycopg2, not string
    hourly_data = result[1] if isinstance(result[1], dict) else json.loads(result[1])
    day_data = result[2] if isinstance(result[2], dict) else json.loads(result[2])
    print(f"   hourly_rates: {len(hourly_data)} hours configured")
    print(f"   day_multipliers: {len(day_data)} days configured")
    
    print("\n" + "=" * 70)
    print("🎉 QUICK FIX COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Restart commuter_simulator to reload config")
    print("  2. Verify spawning works with realistic counts")
    print("  3. Plan proper schema refactor (see SPAWN_SCHEMA_ANALYSIS.md)")
    print("\nExpected behavior:")
    print("  • 8am weekday: lambda = 2.0 × 2.0 × 1.3 = 5.2 → ~4-6 passengers")
    print("  • 5pm weekday: lambda = 2.0 × 2.2 × 1.3 = 5.72 → ~5-7 passengers")
    print("  • 12pm Sunday: lambda = 2.0 × 0.9 × 0.3 = 0.54 → ~0-1 passengers")
    print("=" * 70)

except Exception as e:
    conn.rollback()
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    raise

finally:
    cur.close()
    conn.close()
