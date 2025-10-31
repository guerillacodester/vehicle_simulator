#!/usr/bin/env python3
"""
Production-ready seed script for Route 1 spawn configuration (JSON format)

Creates a single spawn_config with all parameters in one JSON field.
Optimized for production performance.
"""
import psycopg2
import os
import json
import uuid
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
    print("🌱 Seeding Route 1 spawn config (JSON format)...")
    print("=" * 70)
    
    # Get Route 1
    cur.execute("SELECT id, document_id, short_name FROM routes WHERE short_name = '1' LIMIT 1")
    route_result = cur.fetchone()
    if not route_result:
        raise Exception("Route 1 not found!")
    
    route_id, route_doc_id, route_name = route_result
    print(f"✅ Found Route {route_name} (ID: {route_id}, documentId: {route_doc_id})")
    
    # Check if config exists
    cur.execute("""
        SELECT sc.id, sc.name 
        FROM spawn_configs sc
        JOIN spawn_configs_route_lnk scrl ON sc.id = scrl.spawn_config_id
        WHERE scrl.route_id = %s
    """, (route_id,))
    
    existing = cur.fetchone()
    if existing:
        print(f"⚠️  Existing config found: {existing[1]} (ID: {existing[0]})")
        response = input("Delete and recreate? (y/N): ").strip().lower()
        if response == 'y':
            cur.execute("DELETE FROM spawn_configs WHERE id = %s", (existing[0],))
            print(f"✅ Deleted existing config")
        else:
            print("❌ Aborted")
            cur.close()
            conn.close()
            exit(0)
    
    # Create complete JSON config
    config_json = {
        "distribution_params": {
            "spatial_base": 2.0,
            "spawn_radius_meters": 800,
            "min_spawn_interval_seconds": 45,
            "passengers_per_building_per_hour": 0.3,
            "min_trip_distance_meters": 250,
            "trip_distance_mean_meters": 2000,
            "trip_distance_std_meters": 1000,
            "max_trip_distance_ratio": 1.0
        },
        "hourly_rates": {
            "0": 0.1,   "1": 0.05,  "2": 0.05,  "3": 0.05,
            "4": 0.2,   "5": 0.5,   "6": 0.8,   "7": 1.5,
            "8": 2.0,   "9": 1.2,   "10": 0.8,  "11": 0.7,
            "12": 0.9,  "13": 0.8,  "14": 0.7,  "15": 1.0,
            "16": 1.8,  "17": 2.2,  "18": 1.5,  "19": 1.0,
            "20": 0.6,  "21": 0.4,  "22": 0.3,  "23": 0.2
        },
        "day_multipliers": {
            "0": 1.3,  # Monday
            "1": 1.3,  # Tuesday
            "2": 1.3,  # Wednesday
            "3": 1.3,  # Thursday
            "4": 1.3,  # Friday
            "5": 0.6,  # Saturday
            "6": 0.3   # Sunday
        },
        "building_weights": {
            "residential": {"weight": 3.5, "peak_multiplier": 1.0},
            "apartments": {"weight": 1.2, "peak_multiplier": 0.8},
            "house": {"weight": 4.0, "peak_multiplier": 1.2},
            "commercial": {"weight": 0.5, "peak_multiplier": 0.6},
            "retail": {"weight": 0.3, "peak_multiplier": 0.5},
            "school": {"weight": 1.8, "peak_multiplier": 2.5},
            "government": {"weight": 1.5, "peak_multiplier": 2.0},
            "civic": {"weight": 2.0, "peak_multiplier": 1.5}
        },
        "poi_weights": {
            "bus_station": {"weight": 5.0, "peak_multiplier": 3.0},
            "marketplace": {"weight": 0.8, "peak_multiplier": 1.5},
            "clinic": {"weight": 1.2, "peak_multiplier": 1.8},
            "church": {"weight": 2.0, "peak_multiplier": 1.5},
            "shopping_center": {"weight": 0.3, "peak_multiplier": 0.5},
            "beach": {"weight": 0.5, "peak_multiplier": 1.2}
        },
        "landuse_weights": {
            "residential": {"weight": 3.5, "peak_multiplier": 1.0},
            "commercial": {"weight": 0.3, "peak_multiplier": 0.5},
            "industrial": {"weight": 0.2, "peak_multiplier": 0.4},
            "farmland": {"weight": 1.5, "peak_multiplier": 0.8},
            "recreation": {"weight": 0.5, "peak_multiplier": 0.6}
        }
    }
    
    # Generate document_id
    document_id = str(uuid.uuid4()).replace('-', '')[:25]
    
    # Insert spawn_config
    cur.execute("""
        INSERT INTO spawn_configs 
        (document_id, name, description, config, is_active, created_at, updated_at, published_at, locale)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), NOW(), 'en')
        RETURNING id
    """, (
        document_id,
        'Route 1 - St Lucy Rural (Production)',
        'Optimized JSON config for Route 1 with realistic rural spawn patterns',
        json.dumps(config_json),
        True
    ))
    
    config_id = cur.fetchone()[0]
    print(f"✅ Created spawn_config (ID: {config_id}, documentId: {document_id})")
    
    # Link to route
    cur.execute("""
        INSERT INTO spawn_configs_route_lnk (spawn_config_id, route_id)
        VALUES (%s, %s)
    """, (config_id, route_id))
    
    print(f"✅ Linked to Route {route_name}")
    
    conn.commit()
    
    print("\n" + "=" * 70)
    print("✅ SEED COMPLETE!")
    print("=" * 70)
    print(f"\nConfiguration: Route 1 - St Lucy Rural (Production)")
    print(f"Database ID: {config_id}")
    print(f"Document ID: {document_id}")
    print(f"\nJSON Structure:")
    print(f"  • Distribution params: 8 fields")
    print(f"  • Hourly rates: 24 hours")
    print(f"  • Day multipliers: 7 days")
    print(f"  • Building weights: 8 types")
    print(f"  • POI weights: 6 types")
    print(f"  • Landuse weights: 5 types")
    print(f"\nExpected Performance:")
    print(f"  • 8am weekday: λ = 2.0 × 2.0 × 1.3 = 5.2 → ~4-6 passengers")
    print(f"  • 5pm weekday: λ = 2.0 × 2.2 × 1.3 = 5.72 → ~5-7 passengers")
    print(f"  • Query time: <10ms (single field fetch)")
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
