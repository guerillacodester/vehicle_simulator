# GPS Telemetry Client Library

**Interface-agnostic Python library for consuming GPS telemetry from GPSCentCom server.**

## 🎯 Design Philosophy

This library is **completely decoupled** from any UI framework or interface. It can be consumed by:

- ✅ **CLI applications** (Python argparse, click, typer)
- ✅ **Console applications** (curses, rich, textual)
- ✅ **GUI applications** (Tkinter, PyQt, wxPython)
- ✅ **.NET applications** (via pythonnet/Python.NET)
- ✅ **Web dashboards** (Flask, FastAPI, Django)
- ✅ **Data pipelines** (pandas, Apache Spark)
- ✅ **Monitoring tools** (Prometheus exporters, Grafana)

## 📦 Installation

```bash
# From within vehicle_simulator project
cd gps_telemetry_client
pip install -e .

# Or add to requirements.txt
# -e ./gps_telemetry_client
```

## 🚀 Quick Start

### Synchronous (HTTP Polling)

```python
from gps_telemetry_client import GPSTelemetryClient

# Create client
client = GPSTelemetryClient("http://localhost:8000")

# Get all devices
vehicles = client.get_all_devices()
for vehicle in vehicles:
    print(f"{vehicle.deviceId}: Route {vehicle.route}, "
          f"Speed {vehicle.speed} km/h")

# Get specific device
vehicle = client.get_device("GPS-ZR102")
if vehicle:
    print(f"Found: {vehicle.deviceId} at ({vehicle.lat}, {vehicle.lon})")

# Get devices on route
route_vehicles = client.get_route_devices("1")
print(f"Route 1 has {len(route_vehicles)} active vehicles")

# Get analytics
analytics = client.get_analytics()
print(f"Total devices: {analytics.totalDevices}")
for route_code, stats in analytics.routes.items():
    print(f"Route {route_code}: {stats.count} vehicles, avg speed {stats.avgSpeed} km/h")
```

### Asynchronous (SSE Streaming with Observer)

```python
from gps_telemetry_client import GPSTelemetryClient, TelemetryObserver, Vehicle

# Define custom observer
class MyObserver(TelemetryObserver):
    def on_vehicle_update(self, vehicle: Vehicle):
        print(f"[UPDATE] {vehicle.deviceId}: {vehicle.lat}, {vehicle.lon}")
    
    def on_error(self, error: Exception):
        print(f"[ERROR] {error}")
    
    def on_connected(self):
        print("[CONNECTED] Stream started")
    
    def on_disconnected(self):
        print("[DISCONNECTED] Stream ended")

# Create client and observer
client = GPSTelemetryClient("http://localhost:8000")
observer = MyObserver()

# Register observer
client.add_observer(observer)

# Start streaming (non-blocking)
client.start_stream()

# Do other work...
import time
time.sleep(60)

# Stop streaming
client.stop_stream()
```

### Streaming with Callback (Simpler)

```python
from gps_telemetry_client import GPSTelemetryClient, CallbackObserver

def on_update(vehicle):
    print(f"{vehicle.deviceId}: {vehicle.speed} km/h")

client = GPSTelemetryClient("http://localhost:8000")
client.add_observer(CallbackObserver(on_vehicle_update=on_update))

# Blocking stream (runs until Ctrl+C)
client.start_stream(blocking=True)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Consumer Interface (Your Code)        │
│  - CLI, GUI, Web, .NET, etc.           │
└──────────────────┬──────────────────────┘
                   │
                   │ Import & Use
                   │
┌──────────────────▼──────────────────────┐
│  gps_telemetry_client Library           │
│  ┌────────────────────────────────────┐ │
│  │ GPSTelemetryClient                 │ │
│  │ - get_all_devices()                │ │
│  │ - get_device(id)                   │ │
│  │ - get_route_devices(route)         │ │
│  │ - start_stream() / stop_stream()   │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Observer Pattern                   │ │
│  │ - TelemetryObserver (abstract)     │ │
│  │ - CallbackObserver (concrete)      │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Data Models (Pydantic)             │ │
│  │ - Vehicle, PersonName              │ │
│  │ - AnalyticsResponse, HealthResponse│ │
│  └────────────────────────────────────┘ │
└──────────────────┬──────────────────────┘
                   │
                   │ HTTP / SSE
                   │
┌──────────────────▼──────────────────────┐
│  GPSCentCom Server / Unified Backend    │
│  - GET /gps/devices                     │
│  - GET /gps/device/{id}                 │
│  - GET /gps/stream (SSE)                │
└─────────────────────────────────────────┘
```

## 📚 API Reference

### GPSTelemetryClient

#### Constructor
```python
client = GPSTelemetryClient(base_url="http://localhost:8000")
```

#### Synchronous Methods (HTTP Polling)
- `get_all_devices() -> List[Vehicle]` - Get all active devices
- `get_device(device_id: str) -> Optional[Vehicle]` - Get specific device
- `get_route_devices(route_code: str) -> List[Vehicle]` - Get devices on route
- `get_analytics() -> AnalyticsResponse` - Get fleet analytics
- `get_health() -> HealthResponse` - Get server health status
- `test_connection() -> bool` - Test if server is reachable

#### Asynchronous Methods (SSE Streaming)
- `start_stream(device_id=None, route_code=None, blocking=False)` - Start telemetry stream
- `stop_stream()` - Stop telemetry stream
- `is_streaming() -> bool` - Check if stream is active

#### Observer Management
- `add_observer(observer: TelemetryObserver)` - Register observer
- `remove_observer(observer: TelemetryObserver)` - Unregister observer

### TelemetryObserver (Abstract)

Implement this interface to receive telemetry events:

```python
class TelemetryObserver(ABC):
    @abstractmethod
    def on_vehicle_update(self, vehicle: Vehicle) -> None:
        pass
    
    @abstractmethod
    def on_error(self, error: Exception) -> None:
        pass
    
    @abstractmethod
    def on_connected(self) -> None:
        pass
    
    @abstractmethod
    def on_disconnected(self) -> None:
        pass
```

### CallbackObserver

Simple callback-based observer:

```python
observer = CallbackObserver(
    on_vehicle_update=lambda v: print(v.deviceId),
    on_error=lambda e: print(f"Error: {e}"),
    on_connected=lambda: print("Connected"),
    on_disconnected=lambda: print("Disconnected")
)
```

### Vehicle Model

```python
class Vehicle(BaseModel):
    deviceId: str
    route: str
    vehicleReg: str
    lat: float  # -90 to 90
    lon: float  # -180 to 180
    speed: float  # km/h
    heading: float  # 0-360 degrees
    driverId: Optional[str]
    driverName: Optional[Union[str, PersonName]]
    timestamp: str  # ISO format
    lastSeen: str  # ISO format
    # ... additional fields
    
    # Helper methods
    def get_driver_display_name() -> str
    def get_age_seconds() -> float
    def is_stale(threshold_seconds=120) -> bool
```

## 🔌 Integration Examples

### CLI Application

```python
import argparse
from gps_telemetry_client import GPSTelemetryClient

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://localhost:8000')
args = parser.parse_args()

client = GPSTelemetryClient(args.url)
vehicles = client.get_all_devices()

for v in vehicles:
    print(f"{v.deviceId:15} Route {v.route:3} {v.speed:6.1f} km/h")
```

### .NET Integration (via pythonnet)

```csharp
using Python.Runtime;

// Initialize Python runtime
PythonEngine.Initialize();

using (Py.GIL())
{
    dynamic gps = Py.Import("gps_telemetry_client");
    dynamic client = gps.GPSTelemetryClient("http://localhost:8000");
    
    dynamic vehicles = client.get_all_devices();
    
    foreach (dynamic vehicle in vehicles)
    {
        Console.WriteLine($"{vehicle.deviceId}: {vehicle.lat}, {vehicle.lon}");
    }
}
```

### GUI Application (Tkinter)

```python
import tkinter as tk
from gps_telemetry_client import GPSTelemetryClient, CallbackObserver

class GPSMonitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GPS Monitor")
        
        self.text = tk.Text(self)
        self.text.pack()
        
        client = GPSTelemetryClient("http://localhost:8000")
        client.add_observer(CallbackObserver(
            on_vehicle_update=self.on_update
        ))
        client.start_stream()  # Non-blocking
    
    def on_update(self, vehicle):
        self.text.insert(tk.END, f"{vehicle.deviceId}: {vehicle.speed} km/h\n")

app = GPSMonitor()
app.mainloop()
```

### Web Dashboard (Flask)

```python
from flask import Flask, jsonify
from gps_telemetry_client import GPSTelemetryClient

app = Flask(__name__)
client = GPSTelemetryClient("http://localhost:8000")

@app.route('/api/vehicles')
def get_vehicles():
    vehicles = client.get_all_devices()
    return jsonify([v.model_dump() for v in vehicles])

@app.route('/api/vehicles/<device_id>')
def get_vehicle(device_id):
    vehicle = client.get_device(device_id)
    return jsonify(vehicle.model_dump() if vehicle else None)

app.run(port=3000)
```

## 🧪 Testing

```bash
# Test connection
python -c "from gps_telemetry_client import GPSTelemetryClient; \
           print('Connected!' if GPSTelemetryClient().test_connection() else 'Failed')"

# List devices
python -c "from gps_telemetry_client import GPSTelemetryClient; \
           vehicles = GPSTelemetryClient().get_all_devices(); \
           print(f'Found {len(vehicles)} devices')"
```

## 📋 Requirements

```
pydantic>=2.0
requests>=2.28
```

## 🎯 Design Patterns Used

- **Observer Pattern** - Event-driven updates
- **Facade Pattern** - Simplified interface to complex HTTP/SSE operations
- **Strategy Pattern** - Pluggable observers
- **Dependency Inversion** - Depends on abstractions (TelemetryObserver)

## 🔮 Future Extensions

- WebSocket support (in addition to SSE)
- Caching layer (Redis)
- Batch operations
- Historical data queries
- Geofence event filtering
- Circuit breaker for fault tolerance
