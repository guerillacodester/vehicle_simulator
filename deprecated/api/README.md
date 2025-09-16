# ArkNet Transit Simulator API

RESTful API server for controlling and monitoring the ArkNet Transit Simulator.

## Quick Start

1. **Install API dependencies:**
   ```bash
   pip install fastapi uvicorn[standard]
   ```

2. **Start the API server:**
   ```bash
   cd api/
   python server.py
   ```

3. **Access the API:**
   - API Server: http://127.0.0.1:8090
   - Interactive Documentation: http://127.0.0.1:8090/docs
   - Alternative Documentation: http://127.0.0.1:8090/redoc

## API Endpoints

### Simulator Control
- `GET /health` - Health check
- `POST /simulator/start` - Start simulator
- `POST /simulator/stop` - Stop simulator  
- `GET /simulator/status` - Get simulator status
- `GET /simulator/output` - Get simulator output

### Vehicle Management (Coming Soon)
- `GET /vehicles` - Get all vehicle statuses
- `GET /vehicles/{vehicle_id}` - Get specific vehicle status
- `POST /vehicles/{vehicle_id}/start` - Start vehicle
- `POST /vehicles/{vehicle_id}/stop` - Stop vehicle

### Passenger Management (Coming Soon)
- `GET /passengers/stats` - Get passenger statistics
- `GET /passengers/scheduled` - Get scheduled passengers
- `GET /passengers/active` - Get active passengers

### Route Management (Coming Soon)
- `GET /routes` - Get all routes
- `GET /routes/{route_id}` - Get specific route info

### Driver Management (Coming Soon)  
- `GET /drivers` - Get all driver statuses
- `GET /drivers/{driver_id}` - Get specific driver status

## Usage Examples

### Start the Simulator
```bash
curl -X POST "http://127.0.0.1:8090/simulator/start" \
     -H "Content-Type: application/json" \
     -d '{
       "mode": "depot",
       "duration": 120,
       "debug": true
     }'
```

### Get Simulator Status
```bash
curl "http://127.0.0.1:8090/simulator/status"
```

### Stop the Simulator
```bash
curl -X POST "http://127.0.0.1:8090/simulator/stop"
```

## Development

### Custom Port and Host
```bash
python server.py --host 0.0.0.0 --port 8080 --reload
```

### Enable Auto-reload (Development)
```bash
python server.py --reload --log-level debug
```

## Architecture

The API server runs the simulator as a subprocess, allowing you to:
- Start/stop simulations via REST API
- Monitor simulator status in real-time
- Query vehicle, passenger, route, and driver information
- Execute commands without blocking the API server

This design keeps the API responsive while the simulator runs independently.