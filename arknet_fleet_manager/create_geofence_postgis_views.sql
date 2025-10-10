-- PostGIS Geofence Materialized Views
-- 
-- These views materialize geofence geometries from normalized point sequences
-- into PostGIS geography types for fast spatial queries.
--
-- Execute after: Strapi creates geofences, geofence_geometries, geometry_points tables

-- =============================================================================
-- 1. POLYGON GEOFENCES
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS geofence_polygons CASCADE;

CREATE MATERIALIZED VIEW geofence_polygons AS
SELECT 
  g.id,
  g.geofence_id,
  g.name,
  g.type,
  g.enabled,
  g.valid_from,
  g.valid_to,
  gg.id AS geometry_junction_id,
  gg.geometry_id,
  gg.geometry_type,
  gg.is_primary,
  gg.buffer_meters,
  
  -- Build PostGIS polygon from point sequences
  ST_MakePolygon(
    ST_MakeLine(
      ARRAY(
        SELECT ST_MakePoint(gp.point_lon, gp.point_lat)
        FROM geometry_points gp
        WHERE gp.geometry_id = gg.geometry_id
          AND gp.is_active = true
        ORDER BY gp.point_sequence
      )
    )
  )::geography AS geom,
  
  -- Compute area in square meters
  ST_Area(
    ST_MakePolygon(
      ST_MakeLine(
        ARRAY(
          SELECT ST_MakePoint(gp.point_lon, gp.point_lat)
          FROM geometry_points gp
          WHERE gp.geometry_id = gg.geometry_id
            AND gp.is_active = true
          ORDER BY gp.point_sequence
        )
      )
    )::geography
  ) AS area_sqm,
  
  -- Compute bounding box [min_lon, min_lat, max_lon, max_lat]
  ARRAY[
    (SELECT MIN(point_lon) FROM geometry_points WHERE geometry_id = gg.geometry_id AND is_active = true),
    (SELECT MIN(point_lat) FROM geometry_points WHERE geometry_id = gg.geometry_id AND is_active = true),
    (SELECT MAX(point_lon) FROM geometry_points WHERE geometry_id = gg.geometry_id AND is_active = true),
    (SELECT MAX(point_lat) FROM geometry_points WHERE geometry_id = gg.geometry_id AND is_active = true)
  ] AS bbox,
  
  -- Point count
  (SELECT COUNT(*) FROM geometry_points WHERE geometry_id = gg.geometry_id AND is_active = true) AS point_count,
  
  NOW() AS last_refreshed

FROM geofences g
JOIN geofence_geometries_geofence_lnk lnk ON g.id = lnk.geofence_id
JOIN geofence_geometries gg ON lnk.geofence_geometry_id = gg.id
WHERE gg.geometry_type = 'polygon'
  AND g.enabled = true
  AND (g.valid_from IS NULL OR g.valid_from <= NOW())
  AND (g.valid_to IS NULL OR g.valid_to >= NOW());

-- Create spatial index on geometry column
CREATE INDEX idx_geofence_polygons_geom ON geofence_polygons USING GIST(geom);

-- Create indexes for fast lookups
CREATE INDEX idx_geofence_polygons_geofence_id ON geofence_polygons(geofence_id);
CREATE INDEX idx_geofence_polygons_type ON geofence_polygons(type);
CREATE INDEX idx_geofence_polygons_geometry_id ON geofence_polygons(geometry_id);

-- =============================================================================
-- 2. CIRCLE GEOFENCES
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS geofence_circles CASCADE;

CREATE MATERIALIZED VIEW geofence_circles AS
SELECT 
  g.id,
  g.geofence_id,
  g.name,
  g.type,
  g.enabled,
  g.valid_from,
  g.valid_to,
  gg.id AS geometry_junction_id,
  gg.geometry_id,
  gg.geometry_type,
  gg.is_primary,
  gg.buffer_meters,
  
  -- Center point (point_sequence = 0 for circles)
  gp.point_lat AS center_lat,
  gp.point_lon AS center_lon,
  
  -- Radius (from buffer_meters)
  gg.buffer_meters AS radius_meters,
  
  -- Build PostGIS circle as buffered point
  ST_Buffer(
    ST_MakePoint(gp.point_lon, gp.point_lat)::geography,
    gg.buffer_meters
  ) AS geom,
  
  -- Area = π * r²
  PI() * POWER(gg.buffer_meters, 2) AS area_sqm,
  
  -- Bounding box for circle
  ARRAY[
    gp.point_lon - (gg.buffer_meters / 111320.0),  -- Approx degrees from meters at equator
    gp.point_lat - (gg.buffer_meters / 110540.0),
    gp.point_lon + (gg.buffer_meters / 111320.0),
    gp.point_lat + (gg.buffer_meters / 110540.0)
  ] AS bbox,
  
  NOW() AS last_refreshed

FROM geofences g
JOIN geofence_geometries_geofence_lnk lnk ON g.id = lnk.geofence_id
JOIN geofence_geometries gg ON lnk.geofence_geometry_id = gg.id
JOIN geometry_points gp ON gp.geometry_id = gg.geometry_id
WHERE gg.geometry_type = 'circle'
  AND gp.point_sequence = 0  -- Center point only
  AND gp.is_active = true
  AND g.enabled = true
  AND (g.valid_from IS NULL OR g.valid_from <= NOW())
  AND (g.valid_to IS NULL OR g.valid_to >= NOW());

-- Create spatial index on geometry column
CREATE INDEX idx_geofence_circles_geom ON geofence_circles USING GIST(geom);

-- Create indexes for fast lookups
CREATE INDEX idx_geofence_circles_geofence_id ON geofence_circles(geofence_id);
CREATE INDEX idx_geofence_circles_type ON geofence_circles(type);
CREATE INDEX idx_geofence_circles_geometry_id ON geofence_circles(geometry_id);

-- =============================================================================
-- 3. UNIFIED GEOFENCE VIEW (CIRCLES + POLYGONS)
-- =============================================================================

DROP VIEW IF EXISTS geofence_all CASCADE;

CREATE VIEW geofence_all AS
SELECT 
  geofence_id,
  name,
  type,
  geometry_type,
  geometry_id,
  center_lat,
  center_lon,
  radius_meters,
  area_sqm,
  bbox,
  geom
FROM (
  -- Circles
  SELECT 
    geofence_id,
    name,
    type,
    geometry_type,
    geometry_id,
    center_lat,
    center_lon,
    radius_meters,
    area_sqm,
    bbox,
    geom
  FROM geofence_circles
  
  UNION ALL
  
  -- Polygons (NULL for circle-specific fields)
  SELECT 
    geofence_id,
    name,
    type,
    geometry_type,
    geometry_id,
    NULL AS center_lat,
    NULL AS center_lon,
    NULL AS radius_meters,
    area_sqm,
    bbox,
    geom
  FROM geofence_polygons
) AS combined;

-- =============================================================================
-- 4. HELPER FUNCTIONS
-- =============================================================================

-- Function: Check if point is inside ANY geofence
CREATE OR REPLACE FUNCTION check_point_in_geofences(
  p_lat FLOAT,
  p_lon FLOAT,
  p_geofence_types TEXT[] DEFAULT NULL  -- Filter by type (optional)
)
RETURNS TABLE(
  geofence_id TEXT,
  name TEXT,
  type TEXT,
  geometry_type TEXT,
  distance_meters FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    g.geofence_id::TEXT,
    g.name::TEXT,
    g.type::TEXT,
    g.geometry_type::TEXT,
    ST_Distance(g.geom, ST_MakePoint(p_lon, p_lat)::geography) AS distance_meters
  FROM geofence_all g
  WHERE ST_DWithin(g.geom, ST_MakePoint(p_lon, p_lat)::geography, 0)
    AND (p_geofence_types IS NULL OR g.type = ANY(p_geofence_types))
  ORDER BY distance_meters ASC;
END;
$$ LANGUAGE plpgsql;

-- Function: Find nearest geofence to a point
CREATE OR REPLACE FUNCTION find_nearest_geofence(
  p_lat FLOAT,
  p_lon FLOAT,
  p_max_distance_meters FLOAT DEFAULT 1000.0,
  p_geofence_types TEXT[] DEFAULT NULL
)
RETURNS TABLE(
  geofence_id TEXT,
  name TEXT,
  type TEXT,
  geometry_type TEXT,
  distance_meters FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    g.geofence_id::TEXT,
    g.name::TEXT,
    g.type::TEXT,
    g.geometry_type::TEXT,
    ST_Distance(g.geom, ST_MakePoint(p_lon, p_lat)::geography) AS distance_meters
  FROM geofence_all g
  WHERE ST_DWithin(g.geom, ST_MakePoint(p_lon, p_lat)::geography, p_max_distance_meters)
    AND (p_geofence_types IS NULL OR g.type = ANY(p_geofence_types))
  ORDER BY distance_meters ASC
  LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function: Refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_geofence_views()
RETURNS TEXT AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY geofence_polygons;
  REFRESH MATERIALIZED VIEW CONCURRENTLY geofence_circles;
  RETURN 'Geofence views refreshed at ' || NOW()::TEXT;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 5. EXAMPLE QUERIES
-- =============================================================================

-- Example 1: Check if Kingston Central (18.0179, -76.8099) is in any depot geofence
-- SELECT * FROM check_point_in_geofences(18.0179, -76.8099, ARRAY['depot']);

-- Example 2: Find nearest boarding zone to Half Way Tree (18.0127, -76.7945)
-- SELECT * FROM find_nearest_geofence(18.0127, -76.7945, 500.0, ARRAY['boarding_zone']);

-- Example 3: Get all active polygons with area > 10,000 sqm
-- SELECT geofence_id, name, type, area_sqm 
-- FROM geofence_polygons 
-- WHERE area_sqm > 10000
-- ORDER BY area_sqm DESC;

-- Example 4: Get all circles within 100m radius
-- SELECT geofence_id, name, center_lat, center_lon, radius_meters
-- FROM geofence_circles
-- WHERE radius_meters <= 100
-- ORDER BY radius_meters ASC;

-- Example 5: Direct ST_Contains query
-- SELECT geofence_id, name, type
-- FROM geofence_all
-- WHERE ST_Contains(geom, ST_MakePoint(-76.8099, 18.0179)::geography);

-- =============================================================================
-- 6. REFRESH VIEWS (RUN AFTER DATA CHANGES)
-- =============================================================================

-- Manual refresh
-- REFRESH MATERIALIZED VIEW CONCURRENTLY geofence_polygons;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY geofence_circles;

-- Or use helper function
-- SELECT refresh_geofence_views();

-- =============================================================================
-- 7. PERFORMANCE NOTES
-- =============================================================================

-- GIST Indexes: O(log n) spatial lookups
-- ST_Contains: ~10-50ms for 1000s of polygons
-- ST_DWithin: ~5-20ms for nearest neighbor search
-- Materialized views: Refresh when geometry changes (INSERT/UPDATE/DELETE on geometry_points)

-- For real-time updates, consider triggers:
-- CREATE TRIGGER refresh_geofence_views_on_change
-- AFTER INSERT OR UPDATE OR DELETE ON geometry_points
-- FOR EACH STATEMENT
-- EXECUTE FUNCTION refresh_geofence_views();

COMMENT ON MATERIALIZED VIEW geofence_polygons IS 'PostGIS polygon geofences built from geometry_points';
COMMENT ON MATERIALIZED VIEW geofence_circles IS 'PostGIS circle geofences built from center point + radius';
COMMENT ON VIEW geofence_all IS 'Unified view of all geofences (circles + polygons)';
COMMENT ON FUNCTION check_point_in_geofences IS 'Check if lat/lon is inside any geofence';
COMMENT ON FUNCTION find_nearest_geofence IS 'Find nearest geofence to lat/lon within max distance';
COMMENT ON FUNCTION refresh_geofence_views IS 'Refresh all geofence materialized views';
