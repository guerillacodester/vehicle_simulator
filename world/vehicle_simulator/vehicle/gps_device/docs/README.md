# GPS Device Telemetry Interface

## Quick Start Guide

This interface allows you to connect any data source to the GPS device RxTx buffer in a source-agnostic way.

### Basic Usage

```python
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.telemetry_interface import (
    TelemetryInjector, SimulatedTelemetrySource
)

# 1. Create GPS device
gps_device = GPSDevice("DEV001", "ws://localhost:8765", "token")

# 2. Create data source
data_source = SimulatedTelemetrySource("DEV001", "R001") 

# 3. Connect them
injector = TelemetryInjector(gps_device, data_source)

# 4. Start transmission
gps_device.on()
injector.start_injection()

# 5. Send data
success = injector.inject_single()

# 6. Cleanup
injector.stop_injection()
gps_device.off()
```

## Creating Custom Data Sources

Implement the `ITelemetryDataSource` interface:

```python
from world.vehicle_simulator.vehicle.gps_device.telemetry_interface import ITelemetryDataSource
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import make_packet

class MyDataSource(ITelemetryDataSource):
    def __init__(self, device_id):
        self.device_id = device_id
    
    def get_telemetry_data(self):
        # Return TelemetryPacket or None
        return make_packet(
            device_id=self.device_id,
            lat=your_latitude,
            lon=your_longitude,
            speed=your_speed,
            heading=your_heading,
            route=your_route
        )
    
    def is_available(self):
        return True  # Return connection status
    
    def start(self):
        pass  # Initialize connections
    
    def stop(self):
        pass  # Cleanup
```

## Available Data Sources

- **SimulatedTelemetrySource** - Generated test data
- **SerialTelemetrySource** - Real GPS hardware via serial port  
- **FileTelemetrySource** - Replay from log files

See `example_usage.py` for complete examples.

## Key Benefits

- ✅ **Source Agnostic** - GPS device doesn't know about data sources
- ✅ **Portable** - Take GPS device anywhere, connect any source
- ✅ **Testable** - Test with simulation, deploy with real hardware
- ✅ **Simple** - One method (`inject_single()`) to put data in buffer

## Documentation

- **Full Tutorial**: `docs/TELEMETRY_INTERFACE_TUTORIAL.md`
- **Examples**: `world/vehicle_simulator/vehicle/gps_device/example_usage.py`
- **Interface**: `world/vehicle_simulator/vehicle/gps_device/telemetry_interface.py`

## Architecture

```text
Data Source → TelemetryInjector → GPS Device RxTx Buffer → WebSocket Server
```

The interface cleanly separates data generation from transmission, making the GPS device completely portable and source-independent.
