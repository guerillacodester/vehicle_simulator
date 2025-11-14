-- Seed data for spawn_configs with Barbados typical weekday pattern
-- Uses Strapi v5 structure with document_id

-- Insert spawn_config
INSERT INTO spawn_configs (
    document_id,
    name,
    description,
    is_active,
    locale,
    published_at,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'Barbados Typical Weekday',
    'Default spawn configuration for Barbados commuter patterns - morning/evening peaks with reduced weekend traffic',
    true,
    'en',
    NOW(),
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Get the spawn_config id for linking components
DO $$
DECLARE
    config_id INTEGER;
    barbados_country_id INTEGER;
    building_weight_ids INTEGER[];
    poi_weight_ids INTEGER[];
    landuse_weight_ids INTEGER[];
    hourly_pattern_ids INTEGER[];
    day_multiplier_ids INTEGER[];
    distribution_params_id INTEGER;
    i INTEGER;
BEGIN
    SELECT id INTO config_id FROM spawn_configs WHERE name = 'Barbados Typical Weekday' LIMIT 1;

    -- Insert building_weights components
    INSERT INTO components_spawning_building_weights (building_type, weight, peak_multiplier, is_active)
    VALUES
        ('residential', 2.0, 2.5, true),
        ('apartments', 2.5, 2.8, true),
        ('commercial', 1.5, 1.2, true),
        ('office', 1.8, 1.5, true),
        ('school', 2.5, 3.0, true),
        ('university', 2.8, 2.5, true),
        ('hospital', 1.5, 1.0, true),
        ('retail', 2.0, 1.3, true);
    
    SELECT ARRAY_AGG(id ORDER BY id) INTO building_weight_ids 
    FROM (SELECT id FROM components_spawning_building_weights ORDER BY id DESC LIMIT 8) AS t;

    -- Insert poi_weights components
    INSERT INTO components_spawning_poi_weights (poi_type, weight, peak_multiplier, is_active)
    VALUES
        ('bus_station', 3.0, 3.5, true),
        ('marketplace', 2.5, 2.0, true),
        ('shopping_center', 2.2, 1.5, true),
        ('school', 2.5, 3.0, true),
        ('hospital', 1.5, 1.0, true),
        ('beach', 1.8, 0.8, true);
    
    SELECT ARRAY_AGG(id ORDER BY id) INTO poi_weight_ids
    FROM (SELECT id FROM components_spawning_poi_weights ORDER BY id DESC LIMIT 6) AS t;

    -- Insert landuse_weights components
    INSERT INTO components_spawning_landuse_weights (landuse_type, weight, peak_multiplier, is_active)
    VALUES
        ('residential', 2.0, 2.5, true),
        ('commercial', 2.5, 1.8, true),
        ('industrial', 1.5, 1.2, true),
        ('retail', 2.3, 1.5, true),
        ('mixed_use', 2.2, 2.0, true);
    
    SELECT ARRAY_AGG(id ORDER BY id) INTO landuse_weight_ids
    FROM (SELECT id FROM components_spawning_landuse_weights ORDER BY id DESC LIMIT 5) AS t;

    -- Insert hourly_spawn_rates (24 hours)
    INSERT INTO components_spawning_hourly_patterns (hour, spawn_rate, label)
    VALUES
        (0, 0.2, 'Late night'),
        (1, 0.15, 'Late night'),
        (2, 0.1, 'Late night'),
        (3, 0.1, 'Early morning'),
        (4, 0.3, 'Early morning'),
        (5, 0.8, 'Early morning'),
        (6, 1.5, 'Morning commute start'),
        (7, 2.5, 'Morning peak'),
        (8, 2.8, 'Morning peak'),
        (9, 2.0, 'Morning peak end'),
        (10, 1.2, 'Mid-morning'),
        (11, 1.0, 'Late morning'),
        (12, 1.0, 'Lunch hour'),
        (13, 0.9, 'Early afternoon'),
        (14, 0.8, 'Afternoon'),
        (15, 0.9, 'School pickup'),
        (16, 1.5, 'Evening commute start'),
        (17, 2.3, 'Evening peak'),
        (18, 2.0, 'Evening peak'),
        (19, 1.2, 'Evening'),
        (20, 0.8, 'Night'),
        (21, 0.5, 'Night'),
        (22, 0.3, 'Late night'),
        (23, 0.2, 'Late night');
    
    SELECT ARRAY_AGG(id ORDER BY id) INTO hourly_pattern_ids
    FROM (SELECT id FROM components_spawning_hourly_patterns ORDER BY id DESC LIMIT 24) AS t;

    -- Insert day_multipliers (7 days)
    INSERT INTO components_spawning_day_multipliers (day_of_week, multiplier)
    VALUES
        ('monday', 1.0),
        ('tuesday', 1.0),
        ('wednesday', 1.0),
        ('thursday', 1.0),
        ('friday', 1.0),
        ('saturday', 0.7),
        ('sunday', 0.5);
    
    SELECT ARRAY_AGG(id ORDER BY id) INTO day_multiplier_ids
    FROM (SELECT id FROM components_spawning_day_multipliers ORDER BY id DESC LIMIT 7) AS t;

    -- Insert distribution_params (single component)
    INSERT INTO components_spawning_distribution_params (
        poisson_lambda_base,
        max_spawns_per_cycle,
        min_spawn_interval_seconds,
        max_spawn_radius_meters,
        min_distance_between_spawns_meters
    ) VALUES (
        3.5,
        50,
        5,
        800,
        50
    ) RETURNING id INTO distribution_params_id;

    -- Link spawn_config to country (Barbados)
    SELECT id INTO barbados_country_id FROM countries WHERE name = 'Barbados' LIMIT 1;
    
    IF barbados_country_id IS NOT NULL THEN
        INSERT INTO spawn_configs_country_lnk (spawn_config_id, country_id)
        VALUES (config_id, barbados_country_id)
        ON CONFLICT DO NOTHING;
    END IF;

    -- Link components using Strapi v5 cmps table
    -- Link building_weights
    FOR i IN 1..array_length(building_weight_ids, 1) LOOP
        INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
        VALUES (config_id, building_weight_ids[i], 'spawning.building-weight', 'building_weights', i - 1);
    END LOOP;

    -- Link poi_weights
    FOR i IN 1..array_length(poi_weight_ids, 1) LOOP
        INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
        VALUES (config_id, poi_weight_ids[i], 'spawning.poi-weight', 'poi_weights', i - 1);
    END LOOP;

    -- Link landuse_weights
    FOR i IN 1..array_length(landuse_weight_ids, 1) LOOP
        INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
        VALUES (config_id, landuse_weight_ids[i], 'spawning.landuse-weight', 'landuse_weights', i - 1);
    END LOOP;

    -- Link hourly_spawn_rates
    FOR i IN 1..array_length(hourly_pattern_ids, 1) LOOP
        INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
        VALUES (config_id, hourly_pattern_ids[i], 'spawning.hourly-pattern', 'hourly_spawn_rates', i - 1);
    END LOOP;

    -- Link day_multipliers
    FOR i IN 1..array_length(day_multiplier_ids, 1) LOOP
        INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
        VALUES (config_id, day_multiplier_ids[i], 'spawning.day-multiplier', 'day_multipliers', i - 1);
    END LOOP;

    -- Link distribution_params (single component, no order needed)
    INSERT INTO spawn_configs_cmps (entity_id, cmp_id, component_type, field, "order")
    VALUES (config_id, distribution_params_id, 'spawning.distribution-params', 'distribution_params', 0);

END $$;
