#!/usr/bin/env python3
"""
Seed Route 1 - St Lucy Rural spawn configuration with realistic rural values
"""
import psycopg2
import os
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
    print("🔍 Checking for existing Route 1 spawn config...")
    
    # Check if already exists
    cur.execute("SELECT id FROM spawn_configs WHERE name = 'Route 1 - St Lucy Rural'")
    existing = cur.fetchone()
    if existing:
        print(f"⚠️  Route 1 config already exists (ID: {existing[0]}), deleting first...")
        cur.execute("DELETE FROM spawn_configs WHERE id = %s", (existing[0],))
    
    # Get Route 1 ID
    cur.execute("SELECT id FROM routes WHERE short_name = '1' LIMIT 1")
    route_result = cur.fetchone()
    if not route_result:
        raise Exception("Route 1 not found!")
    route_id = route_result[0]
    print(f"✅ Found Route 1 (ID: {route_id})")
    
    # Create spawn config with document_id
    import uuid
    document_id = str(uuid.uuid4()).replace('-', '')[:25]  # Strapi v5 document ID format
    
    cur.execute("""
        INSERT INTO spawn_configs (document_id, name, description, is_active, created_at, updated_at, published_at, locale)
        VALUES (%s, %s, %s, %s, NOW(), NOW(), NOW(), 'en')
        RETURNING id
    """, (
        document_id,
        'Route 1 - St Lucy Rural',
        'Rural spawn configuration for Route 1 (St Lucy to St Peter) - Statistically realistic for rural Barbados areas with lower population density',
        True
    ))
    config_id = cur.fetchone()[0]
    print(f"✅ Created spawn config (ID: {config_id}, documentId: {document_id})")
    
    # Link to Route 1
    cur.execute("""
        INSERT INTO spawn_configs_route_lnk (spawn_config_id, route_id)
        VALUES (%s, %s)
    """, (config_id, route_id))
    
    # 1. BUILDING WEIGHTS (Rural: Residential dominant, minimal commercial)
    building_weights = [
        ('residential', 3.5, 1.0),    # High: Most buildings are residential
        ('apartments', 1.2, 0.8),     # Low: Few apartment complexes in rural areas
        ('house', 4.0, 1.2),          # Very High: Single family homes dominant
        ('commercial', 0.5, 0.6),     # Very Low: Minimal commercial activity
        ('retail', 0.3, 0.5),         # Very Low: Few shops
        ('school', 1.8, 2.5),         # Moderate-High: Schools generate traffic
        ('government', 1.5, 2.0),     # Moderate: Government buildings
        ('civic', 2.0, 1.5)           # High: Community civic buildings
    ]
    
    for building_type, weight, peak_mult in building_weights:
        cur.execute("""
            INSERT INTO components_spawning_building_weights (building_type, weight, peak_multiplier, is_active)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id
        """, (building_type, weight, peak_mult))
        comp_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
            VALUES (%s, %s, 'spawning.building-weight', 'building_weights', %s)
        """, (config_id, comp_id, building_weights.index((building_type, weight, peak_mult))))
    
    print(f"✅ Created {len(building_weights)} building weights")
    
    # 2. POI WEIGHTS (Rural: Minimal POIs, basic services)
    poi_weights = [
        ('bus_station', 5.0, 3.0),       # Very High: Bus stops critical for rural transit
        ('marketplace', 0.8, 1.5),       # Low: Occasional markets
        ('clinic', 1.2, 1.8),            # Moderate: Healthcare access points
        ('church', 2.0, 1.5),            # High: Churches important in rural areas
        ('shopping_center', 0.3, 0.5),   # Very Low: Minimal shopping centers
        ('beach', 0.5, 1.2)              # Low: Some beach access
    ]
    
    for poi_type, weight, peak_mult in poi_weights:
        cur.execute("""
            INSERT INTO components_spawning_poi_weights (poi_type, weight, peak_multiplier, is_active)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id
        """, (poi_type, weight, peak_mult))
        comp_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
            VALUES (%s, %s, 'spawning.poi-weight', 'poi_weights', %s)
        """, (config_id, comp_id, poi_weights.index((poi_type, weight, peak_mult))))
    
    print(f"✅ Created {len(poi_weights)} POI weights")
    
    # 3. LANDUSE WEIGHTS (Rural: Agricultural and residential)
    landuse_weights = [
        ('residential', 3.5, 1.0),    # High: Residential areas
        ('commercial', 0.3, 0.5),     # Very Low: Minimal commercial zones
        ('industrial', 0.2, 0.4),     # Very Low: Almost no industrial
        ('farmland', 1.5, 0.8),       # Moderate: Agricultural land (lower spawn rate)
        ('recreation', 0.5, 0.6)      # Low: Parks/recreational areas
    ]
    
    for landuse_type, weight, peak_mult in landuse_weights:
        cur.execute("""
            INSERT INTO components_spawning_landuse_weights (landuse_type, weight, peak_multiplier, is_active)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id
        """, (landuse_type, weight, peak_mult))
        comp_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
            VALUES (%s, %s, 'spawning.landuse-weight', 'landuse_weights', %s)
        """, (config_id, comp_id, landuse_weights.index((landuse_type, weight, peak_mult))))
    
    print(f"✅ Created {len(landuse_weights)} landuse weights")
    
    # 4. HOURLY SPAWN RATES (Rural: Lower overall, single morning peak, early evening peak)
    hourly_rates = [
        (0, 0.05),   # Midnight: Almost no activity
        (1, 0.02),   # 1 AM: Minimal
        (2, 0.02),   # 2 AM: Minimal
        (3, 0.03),   # 3 AM: Minimal
        (4, 0.15),   # 4 AM: Early risers (farmers, workers)
        (5, 0.40),   # 5 AM: Building up
        (6, 0.60),   # 6 AM: Morning peak start (rural workers to town) - ~16 passengers
        (7, 1.20),   # 7 AM: Main morning peak - ~32 passengers
        (8, 1.00),   # 8 AM: Tapering off
        (9, 0.70),   # 9 AM: Mid-morning
        (10, 0.50),  # 10 AM: Light activity
        (11, 0.60),  # 11 AM: Pre-lunch
        (12, 0.80),  # Noon: Lunch movement
        (13, 0.70),  # 1 PM: Post-lunch
        (14, 0.50),  # 2 PM: Afternoon lull
        (15, 0.80),  # 3 PM: School dismissal
        (16, 1.20),  # 4 PM: Evening peak building
        (17, 1.50),  # 5 PM: Main evening peak (return from town) - ~40 passengers
        (18, 1.00),  # 6 PM: Tapering
        (19, 0.60),  # 7 PM: Evening
        (20, 0.40),  # 8 PM: Light evening
        (21, 0.25),  # 9 PM: Low
        (22, 0.15),  # 10 PM: Very low
        (23, 0.08)   # 11 PM: Minimal
    ]
    
    for hour, rate in hourly_rates:
        cur.execute("""
            INSERT INTO components_spawning_hourly_patterns (hour, spawn_rate)
            VALUES (%s, %s)
            RETURNING id
        """, (hour, rate))
        comp_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
            VALUES (%s, %s, 'spawning.hourly-pattern', 'hourly_spawn_rates', %s)
        """, (config_id, comp_id, hour))
    
    print(f"✅ Created {len(hourly_rates)} hourly rates")
    
    # 5. DAY MULTIPLIERS (Rural: Lower weekday activity, Sunday reduced)
    day_multipliers = [
        ('monday', 1.0),      # Normal
        ('tuesday', 1.0),     # Normal
        ('wednesday', 1.0),   # Normal
        ('thursday', 1.0),    # Normal
        ('friday', 1.1),      # Slightly higher (weekend prep)
        ('saturday', 0.7),    # Lower (less commuting)
        ('sunday', 0.4)       # Much lower (minimal activity)
    ]
    
    for day, mult in day_multipliers:
        cur.execute("""
            INSERT INTO components_spawning_day_multipliers (day_of_week, multiplier)
            VALUES (%s, %s)
            RETURNING id
        """, (day, mult))
        comp_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
            VALUES (%s, %s, 'spawning.day-multiplier', 'day_multipliers', %s)
        """, (config_id, comp_id, day_multipliers.index((day, mult))))
    
    print(f"✅ Created {len(day_multipliers)} day multipliers")
    
    # 6. DISTRIBUTION PARAMS (Rural: Lower frequency, wider radius)
    cur.execute("""
        INSERT INTO components_spawning_distribution_params 
        (poisson_lambda_base, max_spawns_per_cycle, min_spawn_interval_seconds, 
         max_spawn_radius_meters, min_distance_between_spawns_meters)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        0.8,    # Lower base lambda for rural (was 1.5)
        5,      # Fewer max spawns per cycle (was 10)
        45,     # Longer interval between spawns (was 30)
        800,    # Wider search radius (was 500)
        150     # Greater spacing between spawns (was 100)
    ))
    comp_id = cur.fetchone()[0]
    
    cur.execute("""
        INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
        VALUES (%s, %s, 'spawning.distribution-params', 'distribution_params', 0)
    """, (config_id, comp_id))
    
    print(f"✅ Created distribution params")
    
    # Commit
    conn.commit()
    
    print("\n" + "="*70)
    print("✅ SUCCESS! Route 1 - St Lucy Rural spawn config created")
    print("="*70)
    print(f"Configuration ID: {config_id}")
    print(f"Linked to Route: {route_id}")
    print("\nRural Characteristics:")
    print("  • Building Focus: Residential (houses), churches, schools")
    print("  • Commercial Activity: Very low (rural area)")
    print("  • Peak Hours: 7 AM (to town), 5 PM (return home)")
    print("  • Hour 6 rate: 0.6 (~16 passengers)")
    print("  • Hour 7 rate: 1.2 (~32 passengers)")
    print("  • Hour 17 rate: 1.5 (~40 passengers)")
    print("  • Lower spawn frequency, wider radius")
    print("  • Sunday activity: 40% of normal weekday")
    print("="*70)

except Exception as e:
    conn.rollback()
    print(f"❌ ERROR: {e}")
    raise

finally:
    cur.close()
    conn.close()
