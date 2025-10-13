-- Function to find highways and POIs within a specified distance of a lat/long point
-- Usage: SELECT * FROM find_nearby_features(13.1939, -59.5432, 50);

CREATE OR REPLACE FUNCTION find_nearby_features(
    p_lat FLOAT,
    p_lon FLOAT,
    p_distance_meters FLOAT DEFAULT 50
)
RETURNS TABLE(
    feature_type TEXT,
    feature_id INTEGER,
    feature_name VARCHAR(255),
    distance_meters FLOAT,
    feature_data JSONB
) AS $$
BEGIN
    -- Create a geography point from input coordinates
    -- Note: ST_MakePoint takes (lon, lat) not (lat, lon)
    
    RETURN QUERY
    -- Find nearby highways
    WITH query_point AS (
        SELECT ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography AS geom
    ),
    nearby_highways AS (
        SELECT 
            'highway' AS feature_type,
            h.id AS feature_id,
            h.name AS feature_name,
            MIN(ST_Distance(
                (SELECT geom FROM query_point),
                ST_SetSRID(ST_MakePoint(hs.shape_pt_lon, hs.shape_pt_lat), 4326)::geography
            )) AS distance_meters,
            jsonb_build_object(
                'highway_id', h.highway_id,
                'highway_type', h.highway_type,
                'ref', h.ref,
                'osm_id', h.osm_id,
                'full_id', h.full_id,
                'surface', h.surface,
                'lanes', h.lanes,
                'maxspeed', h.maxspeed,
                'oneway', h.oneway,
                'description', h.description,
                'is_active', h.is_active
            ) AS feature_data
        FROM highways h
        JOIN highway_shapes_highway_lnk lnk ON h.id = lnk.highway_id
        JOIN highway_shapes hs ON lnk.highway_shape_id = hs.id
        WHERE h.is_active = true
        GROUP BY h.id, h.highway_id, h.name, h.highway_type, h.ref, h.osm_id, 
                 h.full_id, h.surface, h.lanes, h.maxspeed, h.oneway, h.description, h.is_active
        HAVING MIN(ST_Distance(
            (SELECT geom FROM query_point),
            ST_SetSRID(ST_MakePoint(hs.shape_pt_lon, hs.shape_pt_lat), 4326)::geography
        )) <= p_distance_meters
    ),
    nearby_pois AS (
        SELECT 
            'poi' AS feature_type,
            p.id AS feature_id,
            p.name AS feature_name,
            ST_Distance(
                (SELECT geom FROM query_point),
                ST_SetSRID(ST_MakePoint(p.longitude, p.latitude), 4326)::geography
            ) AS distance_meters,
            jsonb_build_object(
                'poi_type', p.poi_type,
                'amenity', p.amenity,
                'latitude', p.latitude,
                'longitude', p.longitude,
                'osm_id', p.osm_id,
                'description', p.description,
                'is_active', p.is_active
            ) AS feature_data
        FROM pois p
        WHERE p.is_active = true
          AND ST_DWithin(
            (SELECT geom FROM query_point),
            ST_SetSRID(ST_MakePoint(p.longitude, p.latitude), 4326)::geography,
            p_distance_meters
          )
    )
    SELECT * FROM nearby_highways
    UNION ALL
    SELECT * FROM nearby_pois
    ORDER BY distance_meters ASC;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- Find all highways and POIs within 50 meters of a point:
-- SELECT * FROM find_nearby_features(13.1939, -59.5432, 50);
--
-- Find all highways and POIs within 100 meters:
-- SELECT * FROM find_nearby_features(13.1939, -59.5432, 100);
--
-- Group by feature type:
-- SELECT 
--   feature_type, 
--   COUNT(*) as count,
--   AVG(distance_meters) as avg_distance,
--   MIN(distance_meters) as closest
-- FROM find_nearby_features(13.1939, -59.5432, 50)
-- GROUP BY feature_type;

-- Create indexes to speed up the queries
CREATE INDEX IF NOT EXISTS idx_highway_shapes_coords ON highway_shapes (shape_pt_lon, shape_pt_lat);
CREATE INDEX IF NOT EXISTS idx_pois_coords ON pois (longitude, latitude);
CREATE INDEX IF NOT EXISTS idx_pois_geom ON pois USING GIST(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography);
