-- Seed Route 1 - St Lucy Rural spawn configuration
-- Copies existing Barbados config but adjusts temporal rates for rural area

-- First, get the existing spawn-config ID to copy from
DO $$
DECLARE
    template_config_id INT;
    new_config_id INT;
    route_1_id INT;
BEGIN
    -- Get the template spawn config (Barbados Typical Weekday)
    SELECT id INTO template_config_id 
    FROM spawn_configs 
    WHERE name = 'Barbados Typical Weekday' 
    LIMIT 1;
    
    -- Get Route 1 ID
    SELECT id INTO route_1_id
    FROM routes
    WHERE short_name = '1'
    LIMIT 1;
    
    -- Create new spawn config for Route 1
    INSERT INTO spawn_configs (
        document_id,
        name,
        description,
        is_active,
        created_at,
        updated_at,
        published_at,
        created_by_id,
        updated_by_id
    ) VALUES (
        gen_random_uuid()::text,
        'Route 1 - St Lucy Rural',
        'Rural spawn configuration for Route 1 (St Lucy to St Peter) - Lower early morning rates suitable for rural areas',
        true,
        NOW(),
        NOW(),
        NOW(),
        NULL,
        NULL
    )
    RETURNING id INTO new_config_id;
    
    RAISE NOTICE 'Created spawn-config ID: %', new_config_id;
    
    -- Copy building weights
    INSERT INTO spawn_configs_building_weights_lnk (spawn_config_id, building_weight_id, building_weight_ord)
    SELECT new_config_id, building_weight_id, building_weight_ord
    FROM spawn_configs_building_weights_lnk
    WHERE spawn_config_id = template_config_id;
    
    -- Copy POI weights
    INSERT INTO spawn_configs_poi_weights_lnk (spawn_config_id, poi_weight_id, poi_weight_ord)
    SELECT new_config_id, poi_weight_id, poi_weight_ord
    FROM spawn_configs_poi_weights_lnk
    WHERE spawn_config_id = template_config_id;
    
    -- Copy landuse weights (if any)
    INSERT INTO spawn_configs_landuse_weights_lnk (spawn_config_id, landuse_weight_id, landuse_weight_ord)
    SELECT new_config_id, landuse_weight_id, landuse_weight_ord
    FROM spawn_configs_landuse_weights_lnk
    WHERE spawn_config_id = template_config_id;
    
    -- Copy day multipliers
    INSERT INTO spawn_configs_day_multipliers_lnk (spawn_config_id, day_multiplier_id, day_multiplier_ord)
    SELECT new_config_id, day_multiplier_id, day_multiplier_ord
    FROM spawn_configs_day_multipliers_lnk
    WHERE spawn_config_id = template_config_id;
    
    -- Copy distribution params
    INSERT INTO spawn_configs_distribution_params_lnk (spawn_config_id, distribution_params_id)
    SELECT new_config_id, distribution_params_id
    FROM spawn_configs_distribution_params_lnk
    WHERE spawn_config_id = template_config_id;
    
    -- Copy hourly spawn rates BUT with adjusted rural rates
    INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
    SELECT 
        new_config_id,
        nextval('spawn_configs_cmps_id_seq'),
        'spawning.hourly-pattern',
        'hourly_spawn_rates',
        cmps."order"
    FROM spawn_configs_cmps cmps
    WHERE cmps.entity_id = template_config_id
    AND cmps.component_type = 'spawning.hourly-pattern';
    
    -- Now copy the actual hourly pattern data with ADJUSTED rates
    INSERT INTO components_spawning_hourly_patterns (hour, spawn_rate)
    SELECT 
        hp.hour,
        CASE 
            WHEN hp.hour = 4 THEN 0.15  -- Reduced from 0.3
            WHEN hp.hour = 5 THEN 0.4   -- Reduced from 0.8
            WHEN hp.hour = 6 THEN 0.6   -- CRITICAL: Reduced from 1.5 (48 passengers → ~16)
            WHEN hp.hour = 7 THEN 1.2   -- Reduced from 2.8
            WHEN hp.hour = 8 THEN 1.8   -- Reduced from 2.8
            WHEN hp.hour = 9 THEN 1.2   -- Reduced from 2.0
            WHEN hp.hour = 12 THEN 1.2  -- Increased from 1.3
            WHEN hp.hour = 13 THEN 1.2  -- Increased from 0.9
            WHEN hp.hour = 17 THEN 1.8  -- Reduced from 2.3 for rural evening
            ELSE hp.spawn_rate
        END as spawn_rate
    FROM components_spawning_hourly_patterns hp
    INNER JOIN spawn_configs_cmps cmps ON cmps.cmp_id = hp.id
    WHERE cmps.entity_id = template_config_id
    AND cmps.component_type = 'spawning.hourly-pattern';
    
    -- Link spawn config to Route 1
    INSERT INTO spawn_configs_route_lnk (spawn_config_id, route_id)
    VALUES (new_config_id, route_1_id)
    ON CONFLICT DO NOTHING;
    
    RAISE NOTICE 'Linked spawn-config % to Route 1 (ID: %)', new_config_id, route_1_id;
    RAISE NOTICE 'SUCCESS: Route 1 - St Lucy Rural configuration created';
    RAISE NOTICE '  Hour 6 rate: 0.6 (was 1.5)';
    RAISE NOTICE '  Hour 7 rate: 1.2 (was 2.8)';
    RAISE NOTICE '  Expected 6 AM spawns: ~16 passengers (was 48)';
    
END $$;
