# ArkNet Fleet Clients

GUI-agnostic client libraries for consuming ArkNet fleet services. These clients can be used from any interface (Next.js web UI, console apps, desktop apps, mobile apps, etc.).

## Architecture

Each client is a standalone module that:
- Has no UI dependencies
- Provides a clean, typed interface to its service
- Can be used synchronously or asynchronously (where applicable)
- Follows the Observable pattern for real-time updates
- Includes Pydantic models for type safety

## Available Clients

### 1. GPSCentCom Client (`clients/gpscentcom/`)
**Service**: GPSCentCom Server (port 5000)  
**Purpose**: GPS device telemetry and analytics

**Features**:
- HTTP polling for device positions
- SSE streaming for real-time updates
- Observable pattern for event-driven architectures
- Analytics queries

**Usage**:
```python
from clients.gpscentcom import GPSCentComClient

client = GPSCentComClient("http://localhost:5000")
vehicles = client.get_all_devices()
for v in vehicles:
    print(f"{v.deviceId}: {v.lat}, {v.lon}")
```

### 2. Geospatial Client (`clients/geospatial/`)
**Service**: Geospatial Service (port 6000)  
**Purpose**: Spatial queries, geocoding, route geometry

**Features**:
- Reverse geocoding (coordinates → address)
- Route geometry queries
- Building proximity searches
- Spatial analytics

**Usage**:
```python
from clients.geospatial import GeospatialClient

client = GeospatialClient("http://localhost:6000")
address = client.reverse_geocode(13.0969, -59.6137)
print(address)  # "Highway 1B, near parking, Saint Lucy"
```

### 3. Commuter Client (`clients/commuter/`)
**Service**: Commuter Service (port 4000)  
**Purpose**: Passenger manifest queries, seeding, visualization

**Features**:
- Manifest queries with filtering
- Visualization data (bar charts, tables)
- Passenger seeding (trigger spawning)
- Statistics and metrics

**Usage**:
```python
from clients.commuter import CommuterClient

client = CommuterClient("http://localhost:4000")

# Query manifest
passengers = client.get_manifest(route="1", limit=100)

# Get visualization data
barchart = client.get_barchart(date="2024-11-04", route="1")

# Seed passengers
result = client.seed_passengers(
    route="1", 
    day="monday", 
    start_hour=7, 
    end_hour=9
)
```

### 4. Vehicle Client (`clients/vehicle/`)
**Service**: Vehicle Simulator (no HTTP interface currently)  
**Purpose**: Vehicle simulation control (future)

**Status**: To be implemented when vehicle simulator exposes HTTP API

## Installation

Each client can be installed independently:

```bash
# Install specific client
pip install -e clients/gpscentcom

# Install all clients
pip install -e clients/gpscentcom -e clients/geospatial -e clients/commuter
```

## Design Patterns

### 1. Configuration
All clients support multiple configuration methods:
```python
# Method 1: Explicit URL
client = Client("http://localhost:PORT")

# Method 2: Auto-load from config.ini (via common.config_provider)
client = Client()  # Reads from config.ini

# Method 3: Environment variables
# URL loaded from STRAPI_URL, GEOSPATIAL_URL, etc.
```

### 2. Error Handling
All clients raise standard HTTP exceptions:
```python
try:
    data = client.get_something()
except requests.HTTPError as e:
    print(f"HTTP error: {e.response.status_code}")
except requests.RequestException as e:
    print(f"Request failed: {e}")
```

### 3. Type Safety
All responses use Pydantic models:
```python
from clients.gpscentcom import Vehicle

vehicles: List[Vehicle] = client.get_all_devices()
# vehicles[0].deviceId is typed as str
# vehicles[0].lat is typed as float
```

### 4. Observable Pattern (Real-time)
For services with streaming:
```python
from clients.gpscentcom import GPSCentComClient, CallbackObserver

def on_update(vehicle):
    print(f"Vehicle {vehicle.deviceId} moved")

client = GPSCentComClient()
client.add_observer(CallbackObserver(on_vehicle_update=on_update))
client.start_stream()  # Non-blocking
```

## Testing

Each client includes:
- Unit tests (mocked HTTP)
- Integration tests (requires service running)
- Example scripts

```bash
# Test specific client
cd clients/gpscentcom
pytest

# Test all clients
pytest clients/
```

## For GUI Developers

### Next.js / React
```typescript
// Use via Python backend API proxy
fetch('/api/gps/devices')
  .then(res => res.json())
  .then(vehicles => console.log(vehicles))
```

### Desktop (Electron, Tauri)
```javascript
// Call Python client via child_process or IPC
const { spawn } = require('child_process');
const python = spawn('python', ['-c', `
from clients.gpscentcom import GPSCentComClient
client = GPSCentComClient()
print(client.get_all_devices())
`]);
```

### .NET / WPF / WinForms
```csharp
// Use pythonnet
using Python.Runtime;

dynamic gps = Py.Import("clients.gpscentcom");
var client = gps.GPSCentComClient("http://localhost:5000");
var vehicles = client.get_all_devices();
```

### Mobile (React Native)
```javascript
// Use via REST API proxy
const response = await fetch('http://localhost:5000/gps/devices');
const vehicles = await response.json();
```

## Contributing

When adding a new client:
1. Create `clients/<service_name>/` directory
2. Include: `client.py`, `models.py`, `README.md`, `setup.py`, `requirements.txt`
3. Follow existing patterns (config loading, error handling, typing)
4. Add tests
5. Update this README
