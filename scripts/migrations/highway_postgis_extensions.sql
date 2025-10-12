-- ============================================================================
-- Highway PostGIS Extensions for Reverse Geocoding
-- ============================================================================
-- Creates PostGIS geometry column and indexes for highways table
-- Enables fast nearest-highway queries for location naming

-- Add PostGIS geometry column to highways table
ALTER TABLE highways 
ADD COLUMN IF NOT EXISTS geom GEOGRAPHY(LineString, 4326);

-- Create spatial index on highways geometry
CREATE INDEX IF NOT EXISTS highways_geom_gist_idx 
ON highways USING GIST (geom);

-- Create index on highway name for faster lookups
CREATE INDEX IF NOT EXISTS highways_name_idx 
ON highways(name);

-- Create index on highway_id
CREATE INDEX IF NOT EXISTS highways_highway_id_idx 
ON highways(highway_id);

-- Create index on country for filtering
CREATE INDEX IF NOT EXISTS highways_country_idx 
ON highways(country);

-- ============================================================================
-- Function: Build Highway LineString Geometry from Shapes
-- ============================================================================
CREATE OR REPLACE FUNCTION build_highway_geometry(p_highway_id TEXT)
RETURNS VOID AS $$
DECLARE
    v_shape_id TEXT;
    v_coordinates TEXT;
    v_linestring TEXT;
BEGIN
    -- Get the shape_id for this highway
    SELECT shape_id INTO v_shape_id
    FROM highway_shapes
    WHERE highway_id = p_highway_id
    AND is_active = true
    LIMIT 1;
    
    IF v_shape_id IS NULL THEN
        RAISE NOTICE 'No shape found for highway_id: %', p_highway_id;
        RETURN;
    END IF;
    
    -- Build WKT LineString from shape points
    SELECT 'LINESTRING(' || string_agg(
        shape_pt_lon::TEXT || ' ' || shape_pt_lat::TEXT, 
        ', ' 
        ORDER BY shape_pt_sequence
    ) || ')' INTO v_linestring
    FROM shapes
    WHERE shape_id = v_shape_id
    AND is_active = true;
    
    -- Update highway with PostGIS geometry
    UPDATE highways
    SET geom = ST_GeogFromText(v_linestring)
    WHERE highway_id = p_highway_id;
    
    RAISE NOTICE 'Built geometry for highway: %', p_highway_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION build_highway_geometry IS 'Build PostGIS LineString geometry for a highway from its shape points';

-- ============================================================================
-- Function: Rebuild All Highway Geometries
-- ============================================================================
CREATE OR REPLACE FUNCTION rebuild_all_highway_geometries()
RETURNS INTEGER AS $$
DECLARE
    v_highway_id TEXT;
    v_count INTEGER := 0;
BEGIN
    FOR v_highway_id IN 
        SELECT DISTINCT highway_id 
        FROM highway_shapes 
        WHERE is_active = true
    LOOP
        PERFORM build_highway_geometry(v_highway_id);
        v_count := v_count + 1;
        
        -- Progress indicator every 100 highways
        IF v_count % 100 = 0 THEN
            RAISE NOTICE 'Processed % highways...', v_count;
        END IF;
    END LOOP;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION rebuild_all_highway_geometries IS 'Rebuild PostGIS geometry for all highways';

-- ============================================================================
-- Function: Find Nearest Highway to a Point
-- ============================================================================
CREATE OR REPLACE FUNCTION find_nearest_highway(
    p_lat FLOAT,
    p_lon FLOAT,
    p_max_distance_m FLOAT DEFAULT 100.0,
    p_country_code VARCHAR(3) DEFAULT NULL
)
RETURNS TABLE (
    highway_id TEXT,
    name TEXT,
    highway_type TEXT,
    distance_meters FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.highway_id::TEXT,
        h.name::TEXT,
        h.highway_type::TEXT,
        ST_Distance(
            h.geom,
            ST_MakePoint(p_lon, p_lat)::geography
        ) AS distance_meters
    FROM highways h
    LEFT JOIN highways_country_lnk hc ON h.id = hc.highway_id
    LEFT JOIN countries c ON hc.country_id = c.id
    WHERE h.is_active = true
    AND h.geom IS NOT NULL
    AND ST_DWithin(
        h.geom,
        ST_MakePoint(p_lon, p_lat)::geography,
        p_max_distance_m
    )
    AND (p_country_code IS NULL OR c.code = p_country_code)
    ORDER BY distance_meters ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_nearest_highway IS 'Find nearest highway to a lat/lon point within max distance';

-- ============================================================================
-- Function: Get Location Description (POI + Highway)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_location_description(
    p_lat FLOAT,
    p_lon FLOAT,
    p_country_code VARCHAR(3) DEFAULT 'BRB'
)
RETURNS TEXT AS $$
DECLARE
    v_poi_name TEXT;
    v_poi_distance FLOAT;
    v_highway_name TEXT;
    v_highway_distance FLOAT;
    v_description TEXT;
BEGIN
    -- Find nearest POI
    SELECT name, ST_Distance(
        ST_MakePoint(longitude, latitude)::geography,
        ST_MakePoint(p_lon, p_lat)::geography
    )
    INTO v_poi_name, v_poi_distance
    FROM pois p
    LEFT JOIN pois_country_lnk pc ON p.id = pc.poi_id
    LEFT JOIN countries c ON pc.country_id = c.id
    WHERE p.is_active = true
    AND c.code = p_country_code
    AND ST_DWithin(
        ST_MakePoint(longitude, latitude)::geography,
        ST_MakePoint(p_lon, p_lat)::geography,
        500  -- 500m max for POIs
    )
    ORDER BY ST_Distance(
        ST_MakePoint(longitude, latitude)::geography,
        ST_MakePoint(p_lon, p_lat)::geography
    ) ASC
    LIMIT 1;
    
    -- Find nearest highway
    SELECT name, distance_meters
    INTO v_highway_name, v_highway_distance
    FROM find_nearest_highway(p_lat, p_lon, 100.0, p_country_code);
    
    -- Build description
    IF v_poi_name IS NOT NULL AND v_poi_distance < 50 THEN
        -- Very close to POI
        v_description := 'At ' || v_poi_name;
    ELSIF v_poi_name IS NOT NULL AND v_highway_name IS NOT NULL THEN
        -- Near both POI and highway
        v_description := 'On ' || v_highway_name || ', near ' || v_poi_name;
    ELSIF v_highway_name IS NOT NULL THEN
        -- Just highway
        v_description := 'On ' || v_highway_name;
    ELSIF v_poi_name IS NOT NULL THEN
        -- Just POI
        v_description := 'Near ' || v_poi_name || ' (' || ROUND(v_poi_distance) || 'm)';
    ELSE
        -- Nothing found
        v_description := 'Unknown location';
    END IF;
    
    RETURN v_description;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_location_description IS 'Get human-readable location description from coordinates';

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Example 1: Build geometry for a single highway
-- SELECT build_highway_geometry('highway_123');

-- Example 2: Rebuild all highway geometries (run after import)
-- SELECT rebuild_all_highway_geometries();

-- Example 3: Find nearest highway to a point
-- SELECT * FROM find_nearest_highway(13.098, -59.621, 100.0, 'BRB');

-- Example 4: Get location description
-- SELECT get_location_description(13.098, -59.621, 'BRB');

-- ============================================================================
COMMENT ON TABLE highways IS 'Roads and highways with PostGIS LineString geometry for reverse geocoding';
COMMENT ON TABLE highway_shapes IS 'Links highways to their geometric shapes (GTFS-compatible)';
