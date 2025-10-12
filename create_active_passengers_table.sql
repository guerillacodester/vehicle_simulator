-- Active Passengers Table
-- Stores passengers waiting for or riding in vehicles
-- Integrates with DepotReservoir and RouteReservoir for persistence

CREATE TABLE active_passengers (
    passenger_id VARCHAR(255) PRIMARY KEY,
    route_id VARCHAR(255) NOT NULL,
    depot_id VARCHAR(255),  -- NULL for route passengers, set for depot passengers
    direction VARCHAR(20),  -- 'INBOUND' or 'OUTBOUND'
    
    -- Current location (where passenger is waiting)
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    
    -- Destination
    destination_name VARCHAR(255) NOT NULL DEFAULT 'Destination',
    destination_lat DOUBLE PRECISION NOT NULL,
    destination_lon DOUBLE PRECISION NOT NULL,
    
    -- Timestamps
    spawned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    boarded_at TIMESTAMP,
    alighted_at TIMESTAMP,
    
    -- Status
    status VARCHAR(50) DEFAULT 'WAITING',  -- WAITING, ONBOARD, COMPLETED, EXPIRED
    priority INTEGER DEFAULT 3,
    
    -- Spatial computed columns (SQL Server geography, auto-generated from lat/lon)
    -- Note: SQL Server geography::Point expects (latitude, longitude, SRID)
    location geography AS geography::Point(latitude, longitude, 4326) PERSISTED,
    
    destination_location geography AS geography::Point(destination_lat, destination_lon, 4326) PERSISTED
);

-- Spatial indexes for fast proximity queries
CREATE INDEX idx_active_passengers_location 
    ON active_passengers USING GIST(location);

CREATE INDEX idx_active_passengers_destination 
    ON active_passengers USING GIST(destination_location);

-- Regular indexes
CREATE INDEX idx_active_passengers_route 
    ON active_passengers(route_id);

CREATE INDEX idx_active_passengers_depot 
    ON active_passengers(depot_id) WHERE depot_id IS NOT NULL;

CREATE INDEX idx_active_passengers_status 
    ON active_passengers(status);

CREATE INDEX idx_active_passengers_expires 
    ON active_passengers(expires_at) WHERE status = 'WAITING';

-- Comment for documentation
COMMENT ON TABLE active_passengers IS 
    'Active passengers waiting for or riding in vehicles. Integrates with DepotReservoir and RouteReservoir.';

-- Verify creation
SELECT 
    'Table created with ' || COUNT(*) || ' columns' as status
FROM information_schema.columns 
WHERE table_name = 'active_passengers';

-- Show indexes
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'active_passengers'
ORDER BY indexname;
