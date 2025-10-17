# Commuter Service Configuration

## Database-Driven Spawn Intervals

The commuter service now loads its spawn intervals from the Strapi configuration database, allowing you to adjust spawning speed without code changes.

## Configuration Parameters

### Route Reservoir Spawn Interval
- **Parameter**: `commuter_service.spawning.route_spawn_interval_seconds`
- **Type**: Number (float)
- **Default**: 30.0 seconds
- **Description**: How often the route reservoir spawns passengers along routes (bidirectional)

### Depot Reservoir Spawn Interval
- **Parameter**: `commuter_service.spawning.depot_spawn_interval_seconds`
- **Type**: Number (float)
- **Default**: 30.0 seconds
- **Description**: How often the depot reservoir spawns passengers at depot locations

## How to Configure via Strapi

### Option 1: Strapi Admin UI
1. Log into Strapi admin at `http://localhost:1337/admin`
2. Navigate to **Content Manager** → **Operational Configurations**
3. Create or edit configurations with these parameters:
   - **Section**: `commuter_service.spawning`
   - **Parameter**: `route_spawn_interval_seconds` or `depot_spawn_interval_seconds`
   - **Value**: Your desired interval in seconds (e.g., `2.0` for fast testing, `30.0` for production)

### Option 2: REST API
```powershell
# Set route spawn interval to 2 seconds (fast testing)
Invoke-RestMethod -Uri "http://localhost:1337/api/operational-configurations" -Method POST -Body (@{
    data = @{
        section = "commuter_service.spawning"
        parameter = "route_spawn_interval_seconds"
        value = "2.0"
        data_type = "number"
    }
} | ConvertTo-Json) -ContentType "application/json"

# Set depot spawn interval to 2 seconds (fast testing)
Invoke-RestMethod -Uri "http://localhost:1337/api/operational-configurations" -Method POST -Body (@{
    data = @{
        section = "commuter_service.spawning"
        parameter = "depot_spawn_interval_seconds"
        value = "2.0"
        data_type = "number"
    }
} | ConvertTo-Json) -ContentType "application/json"
```

### Option 3: SQL Direct Insert (if using PostgreSQL/SQLite)
```sql
-- Insert route spawn interval configuration
INSERT INTO operational_configurations (section, parameter, value, data_type, created_at, updated_at)
VALUES ('commuter_service.spawning', 'route_spawn_interval_seconds', '2.0', 'number', NOW(), NOW())
ON CONFLICT (section, parameter) DO UPDATE SET value = '2.0', updated_at = NOW();

-- Insert depot spawn interval configuration
INSERT INTO operational_configurations (section, parameter, value, data_type, created_at, updated_at)
VALUES ('commuter_service.spawning', 'depot_spawn_interval_seconds', '2.0', 'number', NOW(), NOW())
ON CONFLICT (section, parameter) DO UPDATE SET value = '2.0', updated_at = NOW();
```

## Recommended Values

| Use Case | Interval | Description |
|----------|----------|-------------|
| **Production** | 30-60 seconds | Realistic passenger arrival patterns |
| **Development** | 10-15 seconds | Moderate spawn rate for testing |
| **Fast Testing** | 2-5 seconds | Quick validation of boarding logic |
| **Stress Testing** | 1 second | Maximum spawn rate for capacity testing |

## Auto-Refresh

The ConfigurationService automatically refreshes configuration every 30 seconds, so changes made in Strapi will be picked up without restarting the commuter service.

## Verification

After setting the configuration, check the commuter service logs for:
```
[CONFIG] Loaded spawn_interval from database: 2.0s
```

If you see a warning like:
```
[CONFIG] Could not load spawn_interval from config service, using default 30.0s
```

This means either:
1. The configuration entry doesn't exist in the database
2. The Strapi API is not running
3. The operational-configurations content type is not set up correctly

## Example: Quick Test Setup

```powershell
# Start Strapi and create fast spawn intervals
cd arknet_fleet_manager/arknet-fleet-api
npm run develop

# In another terminal, set fast spawn intervals via REST API
Invoke-RestMethod -Uri "http://localhost:1337/api/operational-configurations" -Method POST `
  -Headers @{"Authorization"="Bearer YOUR_TOKEN"} `
  -Body '{"data":{"section":"commuter_service.spawning","parameter":"route_spawn_interval_seconds","value":"2.0","data_type":"number"}}' `
  -ContentType "application/json"

# Start commuter service - will pick up 2-second intervals
cd ../../
python start_commuter_service.py
```

## Troubleshooting

### Service not picking up configuration
1. Check Strapi is running: `http://localhost:1337`
2. Verify configuration exists: `GET http://localhost:1337/api/operational-configurations?filters[section][$eq]=commuter_service.spawning`
3. Check commuter service logs for config loading messages
4. Wait up to 30 seconds for auto-refresh to pick up changes

### Still spawning slowly
1. Verify both route and depot intervals are set (they run independently)
2. Check if GeoJSON/population data is loaded correctly
3. Ensure Poisson spawning logic has valid population zones
4. Check logs for spawn request generation and callback execution
