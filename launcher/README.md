# ArkNet Fleet System Launcher

Production-grade launcher with SOLID architecture for managing the ArkNet Fleet System services.

## Architecture

### SOLID Principles Applied

- **Single Responsibility Principle (SRP)**: Each module has one clear responsibility
  - `config.py`: Configuration management only
  - `health.py`: Health checking only
  - `console.py`: Console/process launching only
  - `factory.py`: Service creation only
  - `orchestrator.py`: Startup coordination only

- **Open/Closed Principle (OCP)**: Extensible without modification
  - Platform-specific launchers in `console.py` can be extended
  - Service types can be added without modifying core orchestration

- **Liskov Substitution Principle (LSP)**: Components are interchangeable
  - HealthChecker and ConsoleLauncher are injected dependencies

- **Interface Segregation Principle (ISP)**: Focused interfaces
  - Each component exposes only necessary methods

- **Dependency Inversion Principle (DIP)**: High-level modules depend on abstractions
  - Orchestrator depends on HealthChecker/ConsoleLauncher interfaces, not implementations

## Directory Structure

```
launcher/
├── __init__.py          # Package initialization
├── app.py               # Main application (LauncherApplication)
├── config.py            # Configuration management (ConfigurationManager)
├── models.py            # Data models (ServiceDefinition, ServiceType)
├── health.py            # Health checking (HealthChecker)
├── console.py           # Console launching (ConsoleLauncher)
├── factory.py           # Service factory (ServiceFactory)
└── orchestrator.py      # Startup orchestration (StartupOrchestrator)
```

## Entry Point

**Single entry point:** `launch.py` (root directory)

```bash
python launch.py
```

## Startup Sequence

1. **Stage 1: Monitor Server** (port 8000)
   - Launches monitoring server
   - Waits for health check
   - Console spawns AFTER health passes

2. **Stage 2: Strapi CMS** (Foundation)
   - Launches Strapi via `npm run develop`
   - Waits for health check (configurable timeout)
   - Console spawns AFTER health passes
   - **CRITICAL**: Aborts if Strapi fails

3. **Stage 3: GPSCentCom Server**
   - Launches GPSCentCom
   - Waits for health check
   - Console spawns AFTER health passes
   - **CRITICAL**: Aborts if fails

4. **Stage 4: Pre-Simulator Delay**
   - Configurable delay (default 5s)
   - Allows services to stabilize

5. **Stage 5: Simulators** (Parallel Launch)
   - Vehicle Simulator
   - Commuter Service (integrated: spawning + manifest API)
   - Commuter Service has health check on port 4000

6. **Stage 6: Fleet Services**
   - GeospatialService (health gated)
   - Console spawns AFTER health passes

7. **Continuous Monitoring**
   - Health status dashboard (updates every 10s)
   - Press Ctrl+C to stop monitoring

## Configuration

Edit `config.ini` in root directory:

```ini
[launcher]
# Service enable flags
enable_gpscentcom = true
enable_geospatial = true
enable_vehicle_simulator = false
enable_commuter_service = false

# Startup timing (seconds)
monitor_port = 8000
strapi_startup_wait = 15
gpscentcom_startup_wait = 10
simulator_delay = 5
service_startup_wait = 8

[infrastructure]
# Service ports
strapi_url = http://localhost:1337
strapi_port = 1337
gpscentcom_port = 5000
geospatial_port = 6000
commuter_service_port = 4000
commuter_service_url = http://localhost:4000
```

## Cross-Platform Support

The launcher works on:
- **Windows**: CMD windows
- **Linux**: gnome-terminal, konsole, xterm, terminator, xfce4-terminal
- **macOS**: Terminal.app

## Component Details

### ConfigurationManager
Loads and validates configuration from `config.ini`.

### HealthChecker
Checks service health endpoints with retry logic.

### ConsoleLauncher
Spawns services in new console windows (platform-specific).

### ServiceFactory
Creates service definitions based on configuration.

### StartupOrchestrator
Coordinates the staged startup sequence.

### LauncherApplication
Main application coordinating all components.

## Error Handling

- **Strapi failure**: Aborts entire startup
- **GPSCentCom failure**: Aborts entire startup
- **Other service failures**: Logs warning, continues startup
- **Health check timeout**: Service marked unhealthy but continues

## Extending

To add a new service:

1. Add enable flag to `config.ini`
2. Add port to `infrastructure` section
3. Add method to `ServiceFactory` (e.g., `create_xxx_service()`)
4. Add to appropriate stage in `LauncherApplication`

Example:

```python
# factory.py
def create_new_service(self) -> Optional[ServiceDefinition]:
    if not self.launcher_config.enable_new_service:
        return None
    
    return ServiceDefinition(
        name="New Service",
        service_type=ServiceType.CORE,
        port=self.infra_config.new_service_port,
        health_url=f"http://localhost:{self.infra_config.new_service_port}/health",
        script_path=self.root_path / "new_service" / "main.py",
        startup_wait_seconds=10
    )

# app.py - add to appropriate stage
new_service = self.service_factory.create_new_service()
if new_service:
    self.orchestrator.launch_and_wait(new_service)
```

## Dependencies

- Python 3.8+
- `configparser` (stdlib)
- `subprocess` (stdlib)
- `pathlib` (stdlib)

No external dependencies required!
