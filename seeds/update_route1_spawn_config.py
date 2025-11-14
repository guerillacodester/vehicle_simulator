#!/usr/bin/env python3
"""
Update Route 1 spawn configuration with proper hourly_rates and day_multipliers
for RouteSpawner Poisson distribution calculation
"""
import psycopg2
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('arknet_fleet_manager/arknet-fleet-api/.env')

# Database connection
conn = psycopg2.connect(
    host=os.getenv('DATABASE_HOST', 'localhost'),
    port=os.getenv('DATABASE_PORT', '5432'),
    database=os.getenv('DATABASE_NAME', 'arknettransit'),
    user=os.getenv('DATABASE_USERNAME', 'david'),
    password=os.getenv('DATABASE_PASSWORD')
)
cur = conn.cursor()

try:
    print("🔍 Finding Route 1 spawn config...")
    
    # Get Route 1 documentId
    cur.execute("SELECT document_id FROM routes WHERE short_name = '1' LIMIT 1")
    route_result = cur.fetchone()
    if not route_result:
        raise Exception("Route 1 not found!")
    route_doc_id = route_result[0]
    print(f"✅ Found Route 1 (documentId: {route_doc_id})")
    
    # Get spawn config for Route 1
    cur.execute("""
        SELECT sc.id, sc.document_id, sc.name
        FROM spawn_configs sc
        JOIN spawn_configs_route_lnk scrl ON sc.id = scrl.spawn_config_id
        JOIN routes r ON r.id = scrl.route_id
        WHERE r.document_id = %s
        LIMIT 1
    """, (route_doc_id,))
    
    config_result = cur.fetchone()
    if not config_result:
        raise Exception("No spawn config found for Route 1!")
    
    config_id, config_doc_id, config_name = config_result
    print(f"✅ Found spawn config: {config_name} (ID: {config_id}, documentId: {config_doc_id})")
    
    # Get existing distribution_params component
    cur.execute("""
        SELECT cmp_id 
        FROM spawn_configs_cmps 
        WHERE entity_id = %s 
        AND component_type = 'spawning.distribution-params'
        LIMIT 1
    """, (config_id,))
    
    params_result = cur.fetchone()
    if not params_result:
        raise Exception("No distribution_params found!")
    
    params_id = params_result[0]
    print(f"✅ Found distribution_params component (ID: {params_id})")
    
    # Define proper hourly rates and day multipliers for RouteSpawner
    # These go into the distribution_params as JSON
    hourly_rates = {
        "0": 0.1,    # Midnight
        "1": 0.05,   # 1 AM
        "2": 0.05,   # 2 AM
        "3": 0.05,   # 3 AM
        "4": 0.2,    # 4 AM
        "5": 0.5,    # 5 AM
        "6": 0.8,    # 6 AM - Morning commute starts
        "7": 1.5,    # 7 AM - Peak morning
        "8": 2.0,    # 8 AM - Rush hour
        "9": 1.2,    # 9 AM
        "10": 0.8,   # 10 AM
        "11": 0.7,   # 11 AM
        "12": 0.9,   # Noon
        "13": 0.8,   # 1 PM
        "14": 0.7,   # 2 PM
        "15": 1.0,   # 3 PM - School dismissal
        "16": 1.8,   # 4 PM - Evening rush builds
        "17": 2.2,   # 5 PM - Peak evening
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
    
    # Update distribution_params with all required fields
    print("\n📝 Updating distribution_params with hourly_rates and day_multipliers...")
    
    # Check current columns
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'components_spawning_distribution_params'
        ORDER BY ordinal_position
    """)
    columns = [row[0] for row in cur.fetchall()]
    print(f"Available columns: {', '.join(columns)}")
    
    # Build UPDATE statement based on available columns
    update_fields = []
    update_values = []
    
    # Core fields that should exist
    if 'spatial_base' in columns:
        update_fields.append('spatial_base = %s')
        update_values.append(2.0)  # Base spawn rate
    
    if 'spawn_radius_meters' in columns:
        update_fields.append('spawn_radius_meters = %s')
        update_values.append(800)
    
    if 'min_spawn_interval_seconds' in columns:
        update_fields.append('min_spawn_interval_seconds = %s')
        update_values.append(45)
    
    if 'hourly_rates' in columns:
        update_fields.append('hourly_rates = %s')
        update_values.append(json.dumps(hourly_rates))
    
    if 'day_multipliers' in columns:
        update_fields.append('day_multipliers = %s')
        update_values.append(json.dumps(day_multipliers))
    
    # Additional fields
    if 'passengers_per_building_per_hour' in columns:
        update_fields.append('passengers_per_building_per_hour = %s')
        update_values.append(0.3)
    
    if 'min_trip_distance_meters' in columns:
        update_fields.append('min_trip_distance_meters = %s')
        update_values.append(250)
    
    if 'trip_distance_mean_meters' in columns:
        update_fields.append('trip_distance_mean_meters = %s')
        update_values.append(2000)
    
    if 'trip_distance_std_meters' in columns:
        update_fields.append('trip_distance_std_meters = %s')
        update_values.append(1000)
    
    if 'max_trip_distance_ratio' in columns:
        update_fields.append('max_trip_distance_ratio = %s')
        update_values.append(1)
    
    if update_fields:
        update_values.append(params_id)
        sql = f"""
            UPDATE components_spawning_distribution_params
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        cur.execute(sql, update_values)
        print(f"✅ Updated {len(update_fields)} fields in distribution_params")
    else:
        print("⚠️  No recognized columns to update")
    
    # Commit changes
    conn.commit()
    
    print("\n" + "="*70)
    print("✅ SUCCESS! Route 1 spawn config updated")
    print("="*70)
    print(f"Configuration: {config_name}")
    print(f"Updated distribution_params ID: {params_id}")
    print("\nAdded Poisson Distribution Parameters:")
    print(f"  • spatial_base: 2.0")
    print(f"  • spawn_radius_meters: 800m")
    print(f"  • Hourly rates: {len(hourly_rates)} hours configured")
    print(f"    - Hour 6 (6am): 0.8")
    print(f"    - Hour 7 (7am): 1.5")
    print(f"    - Hour 8 (8am): 2.0 (peak)")
    print(f"    - Hour 16 (4pm): 1.8")
    print(f"    - Hour 17 (5pm): 2.2 (peak)")
    print(f"  • Day multipliers: {len(day_multipliers)} days configured")
    print(f"    - Weekdays (Mon-Fri): 1.3x")
    print(f"    - Saturday: 0.6x")
    print(f"    - Sunday: 0.3x")
    print("\nExpected spawn calculation (8am weekday):")
    print(f"  lambda = 2.0 × 2.0 × 1.3 = 5.2")
    print(f"  Poisson(5.2) → ~4-6 passengers per cycle")
    print("="*70)

except Exception as e:
    conn.rollback()
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    raise

finally:
    cur.close()
    conn.close()
