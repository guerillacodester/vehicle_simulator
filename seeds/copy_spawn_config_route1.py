"""
Copy spawn configuration and create route-specific version for Route 1
Uses direct database access to properly copy Strapi 5 components
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Database credentials from .env
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}

def copy_spawn_config():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get template spawn config (use ID 2 which has components)
        cur.execute("""
            SELECT id, document_id FROM spawn_configs 
            WHERE id = 2
            LIMIT 1
        """)
        template = cur.fetchone()
        template_id = template['id']
        
        # Get Route 1 ID
        cur.execute("SELECT id FROM routes WHERE short_name = '1' LIMIT 1")
        route_1 = cur.fetchone()
        route_1_id = route_1['id']
        
        print(f"Template spawn-config ID: {template_id}")
        print(f"Route 1 ID: {route_1_id}")
        print()
        
        # Create new spawn config
        cur.execute("""
            INSERT INTO spawn_configs (
                document_id, name, description, is_active,
                created_at, updated_at, published_at
            ) VALUES (
                gen_random_uuid()::text,
                'Route 1 - St Lucy Rural',
                'Rural spawn configuration for Route 1 (St Lucy to St Peter) - Lower early morning rates',
                true,
                NOW(), NOW(), NOW()
            )
            RETURNING id
        """)
        new_config_id = cur.fetchone()['id']
        print(f"✅ Created new spawn-config ID: {new_config_id}")
        
        # Get all component mappings from template
        cur.execute("""
            SELECT cmp_id, component_type, field, "order"
            FROM spawn_configs_cmps
            WHERE entity_id = %s
            ORDER BY "order"
        """, (template_id,))
        components = cur.fetchall()
        
        # Copy each component
        for comp in components:
            comp_type = comp['component_type']
            field = comp['field']
            old_cmp_id = comp['cmp_id']
            
            if comp_type == 'spawning.hourly-pattern':
                # Copy but ADJUST rates for rural
                cur.execute("""
                    INSERT INTO components_spawning_hourly_patterns (hour, spawn_rate)
                    SELECT 
                        hour,
                        CASE 
                            WHEN hour = 4 THEN 0.15
                            WHEN hour = 5 THEN 0.4
                            WHEN hour = 6 THEN 0.6  -- KEY: 1.5 → 0.6
                            WHEN hour = 7 THEN 1.2  -- KEY: 2.8 → 1.2
                            WHEN hour = 8 THEN 1.8
                            WHEN hour = 9 THEN 1.2
                            WHEN hour = 12 THEN 1.2
                            WHEN hour = 13 THEN 1.2
                            WHEN hour = 17 THEN 1.8
                            ELSE spawn_rate
                        END
                    FROM components_spawning_hourly_patterns
                    WHERE id = %s
                    RETURNING id
                """, (old_cmp_id,))
                new_cmp_id = cur.fetchone()['id']
                
            elif comp_type == 'spawning.building-weight':
                cur.execute("""
                    INSERT INTO components_spawning_building_weights 
                    SELECT nextval('components_spawning_building_weights_id_seq'), 
                           building_type, weight, peak_multiplier, is_active
                    FROM components_spawning_building_weights
                    WHERE id = %s
                    RETURNING id
                """, (old_cmp_id,))
                new_cmp_id = cur.fetchone()['id']
                
            elif comp_type == 'spawning.poi-weight':
                cur.execute("""
                    INSERT INTO components_spawning_poi_weights
                    SELECT nextval('components_spawning_poi_weights_id_seq'),
                           poi_type, weight, peak_multiplier, is_active
                    FROM components_spawning_poi_weights
                    WHERE id = %s
                    RETURNING id
                """, (old_cmp_id,))
                new_cmp_id = cur.fetchone()['id']
                
            elif comp_type == 'spawning.landuse-weight':
                cur.execute("""
                    INSERT INTO components_spawning_landuse_weights
                    SELECT nextval('components_spawning_landuse_weights_id_seq'),
                           landuse_type, weight, peak_multiplier, is_active
                    FROM components_spawning_landuse_weights
                    WHERE id = %s
                    RETURNING id
                """, (old_cmp_id,))
                new_cmp_id = cur.fetchone()['id']
                
            elif comp_type == 'spawning.day-multiplier':
                cur.execute("""
                    INSERT INTO components_spawning_day_multipliers
                    SELECT nextval('components_spawning_day_multipliers_id_seq'),
                           day_of_week, multiplier
                    FROM components_spawning_day_multipliers
                    WHERE id = %s
                    RETURNING id
                """, (old_cmp_id,))
                new_cmp_id = cur.fetchone()['id']
                
            elif comp_type == 'spawning.distribution-params':
                cur.execute("""
                    INSERT INTO components_spawning_distribution_params
                    SELECT nextval('components_spawning_distribution_params_id_seq'),
                           poisson_lambda_base, max_spawns_per_cycle, 
                           min_spawn_interval_seconds, max_spawn_radius_meters,
                           min_distance_between_spawns_meters
                    FROM components_spawning_distribution_params
                    WHERE id = %s
                    RETURNING id
                """, (old_cmp_id,))
                new_cmp_id = cur.fetchone()['id']
            
            # Link component to new spawn config
            cur.execute("""
                INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
                VALUES (%s, %s, %s, %s, %s)
            """, (new_config_id, new_cmp_id, comp_type, field, comp['order']))
        
        print(f"✅ Copied {len(components)} components")
        
        # Link to Route 1
        cur.execute("""
            INSERT INTO spawn_configs_route_lnk (spawn_config_id, route_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (new_config_id, route_1_id))
        print(f"✅ Linked to Route 1 (ID: {route_1_id})")
        
        # Commit
        conn.commit()
        
        print()
        print("="*60)
        print("SUCCESS!")
        print(f"Created Route 1 - St Lucy Rural (ID: {new_config_id})")
        print(f"  Hour 6 rate: 0.6 (was 1.5)")
        print(f"  Hour 7 rate: 1.2 (was 2.8)")
        print(f"  Expected spawns at 6 AM: ~16 passengers (was 48)")
        print("="*60)
        
    except Exception as e:
        conn.rollback()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    copy_spawn_config()
