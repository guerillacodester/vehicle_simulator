#!/usr/bin/env python3
"""
PRODUCTION REFACTOR: Migrate spawn_configs from normalized components to JSON

This script:
1. Backs up existing component data
2. Converts components to JSON format
3. Updates spawn_configs table with new config column
4. Preserves all existing data
5. Validates migration success

Run AFTER updating Strapi schema to new JSON-based structure.
"""
import psycopg2
import os
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('arknet_fleet_manager/arknet-fleet-api/.env')

conn = psycopg2.connect(
    host=os.getenv('DATABASE_HOST', 'localhost'),
    port=os.getenv('DATABASE_PORT', '5432'),
    database=os.getenv('DATABASE_NAME', 'arknettransit'),
    user=os.getenv('DATABASE_USERNAME', 'david'),
    password=os.getenv('DATABASE_PASSWORD')
)
cur = conn.cursor()

def backup_table(table_name):
    """Create backup of table"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{table_name}_backup_{timestamp}"
    cur.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}")
    print(f"✅ Backed up {table_name} → {backup_name}")

try:
    print("=" * 70)
    print("PRODUCTION MIGRATION: Components → JSON")
    print("=" * 70)
    
    # Step 1: Backup critical tables
    print("\n📦 Step 1: Creating backups...")
    backup_table('spawn_configs')
    backup_table('spawn_configs_cmps')
    conn.commit()
    
    # Step 2: Check if config column exists, add if not
    print("\n🔧 Step 2: Adding 'config' JSONB column...")
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'spawn_configs' AND column_name = 'config'
    """)
    
    if not cur.fetchone():
        cur.execute("""
            ALTER TABLE spawn_configs 
            ADD COLUMN config JSONB
        """)
        print("✅ Added 'config' column")
    else:
        print("✅ 'config' column already exists")
    
    conn.commit()
    
    # Step 3: Migrate data for each spawn_config
    print("\n🔄 Step 3: Migrating component data to JSON...")
    
    cur.execute("SELECT id, name, document_id FROM spawn_configs")
    configs = cur.fetchall()
    
    for config_id, config_name, doc_id in configs:
        print(f"\n  Processing: {config_name} (ID: {config_id})")
        
        config_json = {
            "distribution_params": {},
            "hourly_rates": {},
            "day_multipliers": {},
            "building_weights": {},
            "poi_weights": {},
            "landuse_weights": {}
        }
        
        # Get distribution params
        cur.execute("""
            SELECT dp.spatial_base, dp.spawn_radius_meters, 
                   dp.min_spawn_interval_seconds, dp.passengers_per_building_per_hour,
                   dp.min_trip_distance_meters, dp.trip_distance_mean_meters,
                   dp.trip_distance_std_meters, dp.max_trip_distance_ratio,
                   dp.hourly_rates, dp.day_multipliers
            FROM components_spawning_distribution_params dp
            JOIN spawn_configs_cmps scc ON dp.id = scc.cmp_id
            WHERE scc.entity_id = %s 
            AND scc.component_type = 'spawning.distribution-params'
            LIMIT 1
        """, (config_id,))
        
        dist_result = cur.fetchone()
        if dist_result:
            config_json["distribution_params"] = {
                "spatial_base": float(dist_result[0]) if dist_result[0] else 2.0,
                "spawn_radius_meters": dist_result[1] or 800,
                "min_spawn_interval_seconds": dist_result[2] or 45,
                "passengers_per_building_per_hour": float(dist_result[3]) if dist_result[3] else 0.3,
                "min_trip_distance_meters": dist_result[4] or 250,
                "trip_distance_mean_meters": dist_result[5] or 2000,
                "trip_distance_std_meters": dist_result[6] or 1000,
                "max_trip_distance_ratio": float(dist_result[7]) if dist_result[7] else 1.0
            }
            
            # hourly_rates and day_multipliers from JSONB columns
            if dist_result[8]:  # hourly_rates
                config_json["hourly_rates"] = dist_result[8] if isinstance(dist_result[8], dict) else json.loads(dist_result[8])
            
            if dist_result[9]:  # day_multipliers
                config_json["day_multipliers"] = dist_result[9] if isinstance(dist_result[9], dict) else json.loads(dist_result[9])
            
            print(f"    ✅ Distribution params: {len(config_json['distribution_params'])} fields")
            print(f"    ✅ Hourly rates: {len(config_json['hourly_rates'])} hours")
            print(f"    ✅ Day multipliers: {len(config_json['day_multipliers'])} days")
        
        # Get building weights (optional)
        cur.execute("""
            SELECT bw.building_type, bw.weight, bw.peak_multiplier
            FROM components_spawning_building_weights bw
            JOIN spawn_configs_cmps scc ON bw.id = scc.cmp_id
            WHERE scc.entity_id = %s 
            AND scc.component_type = 'spawning.building-weight'
        """, (config_id,))
        
        for row in cur.fetchall():
            config_json["building_weights"][row[0]] = {
                "weight": float(row[1]),
                "peak_multiplier": float(row[2])
            }
        
        if config_json["building_weights"]:
            print(f"    ✅ Building weights: {len(config_json['building_weights'])} types")
        
        # Get POI weights (optional)
        cur.execute("""
            SELECT pw.poi_type, pw.weight, pw.peak_multiplier
            FROM components_spawning_poi_weights pw
            JOIN spawn_configs_cmps scc ON pw.id = scc.cmp_id
            WHERE scc.entity_id = %s 
            AND scc.component_type = 'spawning.poi-weight'
        """, (config_id,))
        
        for row in cur.fetchall():
            config_json["poi_weights"][row[0]] = {
                "weight": float(row[1]),
                "peak_multiplier": float(row[2])
            }
        
        if config_json["poi_weights"]:
            print(f"    ✅ POI weights: {len(config_json['poi_weights'])} types")
        
        # Get landuse weights (optional)
        cur.execute("""
            SELECT lw.landuse_type, lw.weight, lw.peak_multiplier
            FROM components_spawning_landuse_weights lw
            JOIN spawn_configs_cmps scc ON lw.id = scc.cmp_id
            WHERE scc.entity_id = %s 
            AND scc.component_type = 'spawning.landuse-weight'
        """, (config_id,))
        
        for row in cur.fetchall():
            config_json["landuse_weights"][row[0]] = {
                "weight": float(row[1]),
                "peak_multiplier": float(row[2])
            }
        
        if config_json["landuse_weights"]:
            print(f"    ✅ Landuse weights: {len(config_json['landuse_weights'])} types")
        
        # Update spawn_configs with JSON
        cur.execute("""
            UPDATE spawn_configs 
            SET config = %s
            WHERE id = %s
        """, (json.dumps(config_json), config_id))
        
        print(f"    ✅ Migrated to JSON config")
    
    conn.commit()
    
    # Step 4: Validation
    print("\n✅ Step 4: Validating migration...")
    cur.execute("""
        SELECT id, name, config IS NOT NULL as has_config,
               jsonb_typeof(config) as config_type
        FROM spawn_configs
    """)
    
    all_valid = True
    for row in cur.fetchall():
        config_id, name, has_config, config_type = row
        if not has_config or config_type != 'object':
            print(f"  ❌ {name}: Invalid config")
            all_valid = False
        else:
            print(f"  ✅ {name}: Valid JSON config")
    
    if not all_valid:
        raise Exception("Migration validation failed!")
    
    # Step 5: Display summary
    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 70)
    
    cur.execute("SELECT COUNT(*) FROM spawn_configs WHERE config IS NOT NULL")
    migrated_count = cur.fetchone()[0]
    
    print(f"\nMigrated: {migrated_count} spawn config(s)")
    print("\nBackup tables created:")
    print(f"  - spawn_configs_backup_{datetime.now().strftime('%Y%m%d')}_*")
    print(f"  - spawn_configs_cmps_backup_{datetime.now().strftime('%Y%m%d')}_*")
    
    print("\n⚠️  OLD COMPONENT TABLES STILL EXIST")
    print("They are preserved for rollback safety.")
    print("\nTo remove after confirming system works:")
    print("  DROP TABLE spawn_configs_cmps;")
    print("  DROP TABLE components_spawning_*;")
    
    print("\n📋 Next Steps:")
    print("  1. Restart Strapi (schema changes take effect)")
    print("  2. Test API: python check_spawn_configs.py")
    print("  3. Test spawning: python -m commuter_simulator.main")
    print("  4. If all works, drop old component tables (optional)")
    print("=" * 70)

except Exception as e:
    conn.rollback()
    print(f"\n❌ MIGRATION FAILED: {e}")
    print("\nRolling back...")
    print("Your data is safe. Check error and retry.")
    import traceback
    traceback.print_exc()
    raise

finally:
    cur.close()
    conn.close()
