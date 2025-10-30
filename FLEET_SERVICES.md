# Fleet Services Quick Start

## Starting All Services

Run the unified launcher to start all three services in separate console windows:

```powershell
python start_fleet_services.py
```

This will launch:
- **GPSCentCom Server** (Port 5000) - GPS telemetry WebSocket & HTTP API
- **GeospatialService** (Port 6000) - PostGIS spatial queries
- **Manifest API** (Port 4000) - Passenger manifest enrichment

## Configuration (`.env` file)

All service URLs and ports are configured in `.env` (single source of truth):

```bash
# Service Ports
GPSCENTCOM_PORT=5000
GEOSPATIAL_PORT=6000
MANIFEST_PORT=4000

# Optional: Override URLs (auto-constructed if not set)
# GPSCENTCOM_HTTP_URL=http://localhost:5000
# GPSCENTCOM_WS_URL=ws://localhost:5000
# GEO_URL=http://localhost:6000
# MANIFEST_URL=http://localhost:4000
```

## Service Endpoints

### GPSCentCom Server (Port 5000)
- HTTP API: `http://localhost:5000`
- WebSocket: `ws://localhost:5000/device`
- Health: `http://localhost:5000/health`
- Devices: `http://localhost:5000/devices`

### GeospatialService (Port 6000)
- HTTP API: `http://localhost:6000`
- Health: `http://localhost:6000/health`
- Reverse Geocode: `http://localhost:6000/reverse-geocode`

### Manifest API (Port 4000)
- HTTP API: `http://localhost:4000`
- Health: `http://localhost:4000/health`
- Passengers: `http://localhost:4000/passengers`

## Health Checks

Verify all services are running:

```powershell
curl http://localhost:5000/health
curl http://localhost:6000/health
curl http://localhost:4000/health
```

## Testing GPS Telemetry

Start the vehicle simulator:
```powershell
python -m arknet_transit_simulator --mode depot
```

Monitor GPS telemetry:
```powershell
python -m gps_telemetry_client.test_client --url http://localhost:5000 --prefix / poll --interval 1
```

## Stopping Services

Close each console window individually or press `Ctrl+C` in each service window.
