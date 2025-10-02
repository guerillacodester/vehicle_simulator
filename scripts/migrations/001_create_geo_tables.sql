-- ============================================================================
-- ArkNet Transit System - PostGIS Geographic Schema
-- Migration: 001_create_geo_tables.sql
-- Description: Create geographic tables for multi-country simulation support
-- ============================================================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify PostGIS installation
SELECT PostGIS_version();

-- ============================================================================
-- 1. COUNTRIES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS countries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(3) UNIQUE NOT NULL,  -- ISO 3166-1 alpha-3 (BRB, USA, JAM, etc.)
    name VARCHAR(255) NOT NULL,
    geometry GEOMETRY(MultiPolygon, 4326),  -- Country boundary
    config JSONB DEFAULT '{}',  -- Country-specific settings
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for countries
CREATE INDEX IF NOT EXISTS idx_countries_code ON countries(code);
CREATE INDEX IF NOT EXISTS idx_countries_geom ON countries USING GIST(geometry);

-- Add comments
COMMENT ON TABLE countries IS 'Countries available for simulation';
COMMENT ON COLUMN countries.code IS 'ISO 3166-1 alpha-3 country code';
COMMENT ON COLUMN countries.geometry IS 'Country boundary (MultiPolygon in WGS84)';
COMMENT ON COLUMN countries.config IS 'JSON configuration for country-specific settings';

-- ============================================================================
-- 2. REGIONS TABLE (Parishes, States, Provinces)
-- ============================================================================
CREATE TABLE IF NOT EXISTS regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),  -- 'parish', 'state', 'province', 'district', etc.
    geometry GEOMETRY(MultiPolygon, 4326),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for regions
CREATE INDEX IF NOT EXISTS idx_regions_country ON regions(country_id);
CREATE INDEX IF NOT EXISTS idx_regions_type ON regions(type);
CREATE INDEX IF NOT EXISTS idx_regions_geom ON regions USING GIST(geometry);

COMMENT ON TABLE regions IS 'Administrative regions within countries (parishes, states, etc.)';

-- ============================================================================
-- 3. POINTS OF INTEREST (POIs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS pois (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(id) ON DELETE CASCADE,
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    poi_type VARCHAR(100) NOT NULL,  -- 'bus_station', 'marketplace', 'clinic', 'restaurant', etc.
    name VARCHAR(255),
    geometry GEOMETRY(Point, 4326),  -- Point location (or Polygon for large facilities)
    properties JSONB DEFAULT '{}',  -- Flexible metadata (address, hours, capacity, etc.)
    spawn_weight FLOAT DEFAULT 1.0,  -- Weight for spawn rate calculations (0.0 to 5.0)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for POIs
CREATE INDEX IF NOT EXISTS idx_pois_country ON pois(country_id);
CREATE INDEX IF NOT EXISTS idx_pois_region ON pois(region_id);
CREATE INDEX IF NOT EXISTS idx_pois_type ON pois(poi_type);
CREATE INDEX IF NOT EXISTS idx_pois_geom ON pois USING GIST(geometry);

COMMENT ON TABLE pois IS 'Points of Interest (amenities, facilities, landmarks)';
COMMENT ON COLUMN pois.spawn_weight IS 'Multiplier for commuter spawn rates (higher = more spawns)';

-- ============================================================================
-- 4. BUS STOPS
-- ============================================================================
CREATE TABLE IF NOT EXISTS bus_stops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(id) ON DELETE CASCADE,
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    stop_code VARCHAR(50),  -- External ID (e.g., from GTFS feed)
    name VARCHAR(255),
    geometry GEOMETRY(Point, 4326),
    routes UUID[],  -- Array of route IDs serving this stop
    properties JSONB DEFAULT '{}',  -- Additional metadata
    amenities_nearby JSONB DEFAULT '[]',  -- Cached nearby amenities for performance
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for bus stops
CREATE INDEX IF NOT EXISTS idx_bus_stops_country ON bus_stops(country_id);
CREATE INDEX IF NOT EXISTS idx_bus_stops_region ON bus_stops(region_id);
CREATE INDEX IF NOT EXISTS idx_bus_stops_code ON bus_stops(stop_code);
CREATE INDEX IF NOT EXISTS idx_bus_stops_geom ON bus_stops USING GIST(geometry);

COMMENT ON TABLE bus_stops IS 'Bus stop locations for route planning and commuter spawning';

-- ============================================================================
-- 5. LAND USE ZONES
-- ============================================================================
CREATE TABLE IF NOT EXISTS landuse_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(id) ON DELETE CASCADE,
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    zone_type VARCHAR(100) NOT NULL,  -- 'residential', 'commercial', 'industrial', 'farmland', 'grass', etc.
    geometry GEOMETRY(MultiPolygon, 4326),
    population_density FLOAT,  -- People per square km (affects spawn rates)
    spawn_weight FLOAT DEFAULT 1.0,  -- Weight for spawn calculations
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for land use zones
CREATE INDEX IF NOT EXISTS idx_landuse_country ON landuse_zones(country_id);
CREATE INDEX IF NOT EXISTS idx_landuse_region ON landuse_zones(region_id);
CREATE INDEX IF NOT EXISTS idx_landuse_type ON landuse_zones(zone_type);
CREATE INDEX IF NOT EXISTS idx_landuse_geom ON landuse_zones USING GIST(geometry);

COMMENT ON TABLE landuse_zones IS 'Land use classifications for spawn density calculations';

-- ============================================================================
-- 6. ROUTES (Geographic)
-- ============================================================================
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID REFERENCES countries(id) ON DELETE CASCADE,
    route_code VARCHAR(50) NOT NULL,  -- Route number/identifier (e.g., "1", "1A", "ZR")
    name VARCHAR(255),
    geometry GEOMETRY(LineString, 4326),  -- Route path
    direction VARCHAR(50),  -- 'inbound', 'outbound', 'circular', 'bidirectional'
    properties JSONB DEFAULT '{}',  -- Distance, stops, schedule, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for routes
CREATE INDEX IF NOT EXISTS idx_routes_country ON routes(country_id);
CREATE INDEX IF NOT EXISTS idx_routes_code ON routes(route_code);
CREATE INDEX IF NOT EXISTS idx_routes_geom ON routes USING GIST(geometry);

COMMENT ON TABLE routes IS 'Route geometries (LineStrings) for path following and stop placement';

-- ============================================================================
-- 7. SPAWN CONFIGURATIONS (Per Country)
-- ============================================================================
CREATE TABLE IF NOT EXISTS spawn_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID UNIQUE REFERENCES countries(id) ON DELETE CASCADE,
    
    -- Time-of-day patterns (JSONB for flexibility)
    time_patterns JSONB DEFAULT '[
        {"hour_start": 6, "hour_end": 9, "multiplier": 3.0, "period": "morning_rush"},
        {"hour_start": 9, "hour_end": 16, "multiplier": 1.0, "period": "daytime"},
        {"hour_start": 16, "hour_end": 19, "multiplier": 2.5, "period": "evening_rush"},
        {"hour_start": 19, "hour_end": 6, "multiplier": 0.3, "period": "night"}
    ]'::JSONB,
    
    -- POI type weights for different times
    poi_weights JSONB DEFAULT '{
        "morning_rush": {"residential": 0.7, "bus_station": 0.2, "marketplace": 0.1},
        "daytime": {"marketplace": 0.4, "bus_station": 0.3, "residential": 0.3},
        "evening_rush": {"marketplace": 0.5, "bus_station": 0.3, "residential": 0.2},
        "night": {"residential": 0.6, "bus_station": 0.2, "marketplace": 0.2}
    }'::JSONB,
    
    -- Base spawn rates (commuters per minute at 1.0 multiplier)
    depot_base_rate INTEGER DEFAULT 10,
    route_base_rate INTEGER DEFAULT 5,
    
    -- Spatial settings
    pickup_radius_meters FLOAT DEFAULT 500.0,
    route_sampling_resolution INTEGER DEFAULT 50,  -- Points to sample along route
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE spawn_configs IS 'Country-specific spawn configuration (time patterns, rates, weights)';
COMMENT ON COLUMN spawn_configs.time_patterns IS 'Time-of-day spawn multipliers (JSONB array)';
COMMENT ON COLUMN spawn_configs.poi_weights IS 'POI type weights by time period (JSONB object)';

-- ============================================================================
-- 8. HELPER FUNCTIONS
-- ============================================================================

-- Function to get nearest bus stop to a point
CREATE OR REPLACE FUNCTION get_nearest_bus_stop(
    p_country_code VARCHAR(3),
    p_location GEOMETRY,
    p_max_distance_m FLOAT DEFAULT 500
)
RETURNS TABLE (
    stop_id UUID,
    stop_name VARCHAR,
    distance_m FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bs.id,
        bs.name,
        ST_Distance(bs.geometry::geography, p_location::geography) as dist
    FROM bus_stops bs
    JOIN countries c ON bs.country_id = c.id
    WHERE c.code = p_country_code
      AND ST_DWithin(
          bs.geometry::geography,
          p_location::geography,
          p_max_distance_m
      )
    ORDER BY dist ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_nearest_bus_stop IS 'Find nearest bus stop to a location within max distance';

-- Function to get POIs within radius
CREATE OR REPLACE FUNCTION get_pois_within_radius(
    p_country_code VARCHAR(3),
    p_location GEOMETRY,
    p_radius_m FLOAT DEFAULT 1000,
    p_poi_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    poi_id UUID,
    poi_name VARCHAR,
    poi_type VARCHAR,
    distance_m FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.name,
        p.poi_type,
        ST_Distance(p.geometry::geography, p_location::geography) as dist
    FROM pois p
    JOIN countries c ON p.country_id = c.id
    WHERE c.code = p_country_code
      AND ST_DWithin(
          p.geometry::geography,
          p_location::geography,
          p_radius_m
      )
      AND (p_poi_type IS NULL OR p.poi_type = p_poi_type)
    ORDER BY dist ASC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_pois_within_radius IS 'Get all POIs within radius of location, optionally filtered by type';

-- ============================================================================
-- 9. VERIFICATION QUERY
-- ============================================================================

-- Query to verify all tables and indexes
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('countries', 'regions', 'pois', 'bus_stops', 'landuse_zones', 'routes', 'spawn_configs');
    
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND tablename IN ('countries', 'regions', 'pois', 'bus_stops', 'landuse_zones', 'routes', 'spawn_configs');
    
    RAISE NOTICE 'Migration complete!';
    RAISE NOTICE 'Tables created: %', table_count;
    RAISE NOTICE 'Spatial indexes created: %', index_count;
    RAISE NOTICE 'PostGIS version: %', PostGIS_version();
END $$;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
