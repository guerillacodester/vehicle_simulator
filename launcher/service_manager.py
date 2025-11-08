"""
FastAPI-based service manager for orchestrating subsystem lifecycle.

Single Responsibility: Manage service processes and provide API control.
"""

import asyncio
import subprocess
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, List
from collections import deque
from dataclasses import dataclass, field

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx

# Import config manager
from launcher.config import ConfigurationManager


class ServiceState(str, Enum):
    """Service lifecycle states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"


class ServiceEvent(BaseModel):
    """Event emitted when service state changes."""
    service_name: str
    timestamp: str
    state: ServiceState
    message: str
    port: Optional[int] = None


@dataclass
class ManagedService:
    """Represents a managed service with its process and metadata."""
    name: str
    port: Optional[int]
    health_url: Optional[str]
    script_path: Optional[Path] = None
    as_module: Optional[str] = None
    is_npm: bool = False
    npm_command: Optional[str] = None
    extra_args: Optional[List[str]] = None
    dependencies: List[str] = field(default_factory=list)
    spawn_console: bool = False  # Whether to spawn in separate console window
    # How long to wait (seconds) before performing health check after start
    startup_wait: int = 10
    
    # UI Metadata
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    
    # Runtime state
    process: Optional[subprocess.Popen] = None
    state: ServiceState = ServiceState.STOPPED
    stdout_buffer: deque = field(default_factory=lambda: deque(maxlen=1000))
    stderr_buffer: deque = field(default_factory=lambda: deque(maxlen=1000))
    start_time: Optional[datetime] = None
    
    def get_logs(self, lines: int = 100) -> List[str]:
        """Get recent log lines."""
        all_logs = list(self.stdout_buffer) + list(self.stderr_buffer)
        return all_logs[-lines:]
    
    def is_running(self) -> bool:
        """Check if process is running."""
        return self.process is not None and self.process.poll() is None


class ServiceManager:
    """
    Manages the lifecycle of all subsystem services.
    
    Provides subprocess management, health monitoring, and dependency resolution.
    """
    
    def __init__(self):
        """Initialize the service manager."""
        self.services: Dict[str, ManagedService] = {}
        self.event_subscribers: List[WebSocket] = []
        self.http_client = httpx.AsyncClient(timeout=5.0)
        self._monitor_task: Optional[asyncio.Task] = None
        self._startup_order: List[str] = []  # Track startup order for FILO shutdown
    
    def register_service(self, service: ManagedService):
        """Register a service for management."""
        self.services[service.name] = service
    
    def unregister_service(self, name: str):
        """Unregister a service from management."""
        if name in self.services:
            service = self.services[name]
            # Stop the service if it's running
            if service.is_running():
                service.stop()
            del self.services[name]
            print(f"   ❌ Unregistered: {name}")
    
    def update_service_config(self, name: str, spawn_console: bool):
        """Update service configuration."""
        if name in self.services:
            self.services[name].spawn_console = spawn_console
    
    async def start_service(self, name: str) -> ServiceEvent:
        """
        Start a service and its dependencies.
        
        Returns:
            ServiceEvent with the result
        """
        import logging
        start_logger = logging.getLogger(f"service.start")
        start_logger.info(f"start_service called for: '{name}'")
        start_logger.info(f"Available services: {list(self.services.keys())}")
        
        if name not in self.services:
            start_logger.error(f"Service '{name}' not found in manager")
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
        
        service = self.services[name]
        
        # Dependencies are checked but not automatically started
        # (User must start them manually or all at once)
        import logging
        dep_logger = logging.getLogger(f"service.{name}.dependencies")
        
        # Just warn if dependencies are not healthy
        for dep_name in service.dependencies:
            dep = self.services.get(dep_name)
            if not dep:
                dep_logger.warning(f"Dependency '{dep_name}' not found")
            elif dep.state != ServiceState.HEALTHY:
                dep_logger.warning(f"Dependency '{dep_name}' is {dep.state}, but starting {name} anyway")
        
        # Check if already running
        if service.is_running():
            return ServiceEvent(
                service_name=name,
                timestamp=datetime.utcnow().isoformat(),
                state=service.state,
                message=f"{name} is already running",
                port=service.port
            )
        
        # Update state to STARTING
        service.state = ServiceState.STARTING
        event = ServiceEvent(
            service_name=name,
            timestamp=datetime.utcnow().isoformat(),
            state=ServiceState.STARTING,
            message=f"Starting {name}...",
            port=service.port
        )
        await self._emit_event(event)
        
        # Emit progress message for centcom service
        if name == "gpscentcom":
            progress_event = ServiceEvent(
                service_name=name,
                timestamp=datetime.utcnow().isoformat(),
                state=ServiceState.STARTING,
                message="Initializing GPSCentCom server...",
                port=service.port
            )
            await self._emit_event(progress_event)
            await asyncio.sleep(0.5)  # Brief pause for UI update
        # Emit progress message for strapi service
        elif name == "strapi":
            progress_event = ServiceEvent(
                service_name=name,
                timestamp=datetime.utcnow().isoformat(),
                state=ServiceState.STARTING,
                message="Starting Strapi CMS...",
                port=service.port
            )
            await self._emit_event(progress_event)
            await asyncio.sleep(0.5)  # Brief pause for UI update
        
        # Build command
        if service.is_npm:
            # On Windows, npm is typically npm.cmd
            npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
            cmd = [npm_cmd, 'run', service.npm_command] if service.npm_command else [npm_cmd, 'start']
            cwd = service.script_path
        elif service.as_module:
            cmd = [sys.executable, '-m', service.as_module] + (service.extra_args or [])
            # For modules, use project root (parent of launcher directory)
            from pathlib import Path as PathModule
            cwd = PathModule(__file__).parent.parent
        else:
            cmd = [sys.executable, str(service.script_path)] + (service.extra_args or [])
            cwd = service.script_path.parent
        
        # Start subprocess
        try:
            # Set environment to force UTF-8 encoding for subprocess output
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            import logging
            startup_logger = logging.getLogger(f"service.{name}.startup")
            startup_logger.info(f"Starting service {name} (spawn_console={service.spawn_console})")
            startup_logger.info(f"Command: {' '.join(str(c) for c in cmd)}")
            startup_logger.info(f"Working directory: {cwd}")
            
            if service.spawn_console:
                # Spawn visible console window
                if sys.platform == 'win32':
                    # Windows: Use subprocess with visible window
                    service.process = subprocess.Popen(
                        cmd,
                        cwd=cwd,
                        env=env,
                        creationflags=subprocess.CREATE_NEW_CONSOLE  # Create new visible console window
                    )
                else:
                    # Linux: Try common terminal emulators
                    terminal_cmds = [
                        ['gnome-terminal', '--', 'bash', '-c', ' '.join(cmd) + '; exec bash'],
                        ['xterm', '-hold', '-e'] + cmd,
                        ['konsole', '-e'] + cmd,
                        ['xfce4-terminal', '-e', ' '.join(cmd)],
                    ]
                    
                    launched = False
                    for term_cmd in terminal_cmds:
                        try:
                            service.process = subprocess.Popen(
                                term_cmd,
                                cwd=cwd,
                                env=env
                            )
                            launched = True
                            break
                        except FileNotFoundError:
                            continue
                    
                    if not launched:
                        startup_logger.warning("No terminal emulator found, falling back to background process")
                        service.spawn_console = False  # Fallback to background
            
            # Background process with pipe capture
            if not service.spawn_console:
                service.process = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Combine stderr into stdout
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0  # Hide console on Windows
                )
            
            startup_logger.info(f"Process spawned with PID: {service.process.pid}")
            
            service.start_time = datetime.utcnow()
            service.state = ServiceState.RUNNING
            
            # Start capturing output in background (only for background processes, not console windows)
            if not service.spawn_console:
                asyncio.create_task(self._capture_output(service))
            
            # Emit progress message for centcom service
            if name == "gpscentcom":
                progress_event = ServiceEvent(
                    service_name=name,
                    timestamp=datetime.utcnow().isoformat(),
                    state=ServiceState.RUNNING,
                    message=f"GPSCentCom server process started (PID: {service.process.pid})",
                    port=service.port
                )
                await self._emit_event(progress_event)
                await asyncio.sleep(0.5)  # Brief pause for UI update
            
            event = ServiceEvent(
                service_name=name,
                timestamp=datetime.utcnow().isoformat(),
                state=ServiceState.RUNNING,
                message=f"{name} started (PID: {service.process.pid})",
                port=service.port
            )
            await self._emit_event(event)
            
            # Track startup order for FILO shutdown
            if name not in self._startup_order:
                self._startup_order.append(name)
            
            # Wait for health check if applicable
            if service.health_url:
                # Emit progress message for centcom service before health check
                if name == "gpscentcom":
                    progress_event = ServiceEvent(
                        service_name=name,
                        timestamp=datetime.utcnow().isoformat(),
                        state=ServiceState.RUNNING,
                        message="Waiting for GPSCentCom server to become healthy...",
                        port=service.port
                    )
                    await self._emit_event(progress_event)
                    await asyncio.sleep(0.5)  # Brief pause for UI update
                # Emit progress message for strapi service before health check
                elif name == "strapi":
                    progress_event = ServiceEvent(
                        service_name=name,
                        timestamp=datetime.utcnow().isoformat(),
                        state=ServiceState.RUNNING,
                        message="Waiting for Strapi CMS to become healthy...",
                        port=service.port
                    )
                    await self._emit_event(progress_event)
                    await asyncio.sleep(0.5)  # Brief pause for UI update
                
                # Wait for configured startup window before health check (allows slower services like Strapi)
                wait_seconds = getattr(service, 'startup_wait', 2) or 2
                startup_logger.info(f"Waiting {wait_seconds}s for {name} to bind before health check...")
                await asyncio.sleep(wait_seconds)
                healthy = await self._check_health(service)
                if healthy:
                    service.state = ServiceState.HEALTHY
                    event = ServiceEvent(
                        service_name=name,
                        timestamp=datetime.utcnow().isoformat(),
                        state=ServiceState.HEALTHY,
                        message=f"{name} is healthy",
                        port=service.port
                    )
                    await self._emit_event(event)
            
            return event
            
        except Exception as e:
            service.state = ServiceState.FAILED
            event = ServiceEvent(
                service_name=name,
                timestamp=datetime.utcnow().isoformat(),
                state=ServiceState.FAILED,
                message=f"Failed to start {name}: {str(e)}",
                port=service.port
            )
            await self._emit_event(event)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def stop_service(self, name: str) -> ServiceEvent:
        """Stop a running service."""
        if name not in self.services:
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
        
        service = self.services[name]
        
        import logging
        logger = logging.getLogger("service_manager.stop")
        if not service.is_running():
            logger.info(f"Stop requested for {name}, but it is not running.")
            return ServiceEvent(
                service_name=name,
                timestamp=datetime.utcnow().isoformat(),
                state=ServiceState.STOPPED,
                message=f"{name} is not running",
                port=service.port
            )

        logger.info(f"Attempting to terminate process for {name} (PID: {getattr(service.process, 'pid', None)})...")
        try:
            service.process.terminate()
            logger.info(f"Sent terminate signal to {name} (PID: {getattr(service.process, 'pid', None)}). Waiting up to 10s...")
            service.process.wait(timeout=10)
            logger.info(f"Process for {name} terminated cleanly.")
        except subprocess.TimeoutExpired:
            logger.warning(f"Process for {name} did not terminate in time. Sending kill signal...")
            service.process.kill()
            logger.info(f"Process for {name} killed.")
        except Exception as e:
            logger.error(f"Error terminating process for {name}: {e}")

        # Clear process reference
        service.process = None
        service.state = ServiceState.STOPPED
        event = ServiceEvent(
            service_name=name,
            timestamp=datetime.utcnow().isoformat(),
            state=ServiceState.STOPPED,
            message=f"{name} stopped",
            port=service.port
        )
        logger.info(f"Service {name} marked as stopped. Emitting event.")
        await self._emit_event(event)
        return event
    
    async def shutdown_all(self) -> List[ServiceEvent]:
        """
        Shutdown all running services in FILO order (reverse of startup).
        
        Returns:
            List of ServiceEvent for each stopped service
        """
        events = []
        
        # Shutdown in reverse order of startup (FILO)
        shutdown_order = list(reversed(self._startup_order))
        
        print()
        print("=" * 70)
        print("🛑 GRACEFUL SHUTDOWN - FILO Order")
        print("=" * 70)
        print()
        
        for service_name in shutdown_order:
            if service_name not in self.services:
                continue
            
            service = self.services[service_name]
            
            if not service.is_running():
                print(f"   ⏭️  {service_name} - already stopped")
                continue
            
            print(f"   🛑 Stopping {service_name}...")
            
            try:
                event = await self.stop_service(service_name)
                events.append(event)
                print(f"      ✅ {service_name} stopped")
            except Exception as e:
                print(f"      ⚠️  Error stopping {service_name}: {e}")
            
            # Small delay between shutdowns
            await asyncio.sleep(0.5)
        
        print()
        print("=" * 70)
        print("✅ All services stopped")
        print("=" * 70)
        print()
        
        return events
    
    async def get_status(self, name: str) -> dict:
        """Get detailed status of a service."""
        if name not in self.services:
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
        
        service = self.services[name]
        
        return {
            "name": service.name,
            "state": service.state.value,
            "port": service.port,
            "health_url": service.health_url,
            "is_running": service.is_running(),
            "pid": service.process.pid if service.process else None,
            "start_time": service.start_time.isoformat() if service.start_time else None,
            "dependencies": service.dependencies,
            "log_lines": len(service.stdout_buffer) + len(service.stderr_buffer),
            # UI Metadata
            "display_name": service.display_name,
            "description": service.description,
            "category": service.category,
            "icon": service.icon
        }
    
    async def get_all_services(self) -> List[dict]:
        """Get status of all services."""
        return [await self.get_status(name) for name in self.services.keys()]
    
    async def _check_health(self, service: ManagedService) -> bool:
        """Check if service is healthy via HTTP health endpoint."""
        if not service.health_url:
            return True
        
        try:
            response = await self.http_client.get(service.health_url)
            # Accept 200 OK or 204 No Content as healthy
            return response.status_code in [200, 204]
        except Exception:
            return False
    
    async def _capture_output(self, service: ManagedService):
        """Capture stdout/stderr from service process and log to file."""
        import logging
        logger = logging.getLogger(f"service.{service.name}.output")
        
        try:
            # Read combined stdout/stderr stream
            loop = asyncio.get_event_loop()
            while service.is_running():
                try:
                    line = await loop.run_in_executor(None, service.process.stdout.readline)
                    if line:
                        timestamp = datetime.utcnow().isoformat()
                        service.stdout_buffer.append(f"{timestamp} | {line.strip()}")
                        logger.info(f"{line.strip()}")
                    else:
                        break
                except Exception as e:
                    logger.error(f"Error reading process output: {e}")
                    break
        except Exception as e:
            logger.error(f"Error in output capture: {e}")
    
    async def _monitor_health(self):
        """Background task that monitors service health."""
        import logging
        monitor_logger = logging.getLogger("service_monitor")
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds

            for service in self.services.values():
                # Check if process has exited unexpectedly
                if service.process is not None and not service.is_running():
                    # Process exited - check exit code
                    exit_code = service.process.returncode
                    monitor_logger.error(f"Process for {service.name} exited with code {exit_code}")
                    
                    # Log captured output if available
                    if service.stderr_buffer:
                        monitor_logger.error(f"Last stderr from {service.name}:")
                        for line in list(service.stderr_buffer)[-10:]:  # Last 10 lines
                            monitor_logger.error(f"  {line}")
                
                # If process is not running, mark as stopped
                if not service.is_running():
                    if service.state != ServiceState.STOPPED:
                        service.state = ServiceState.STOPPED
                        event = ServiceEvent(
                            service_name=service.name,
                            timestamp=datetime.utcnow().isoformat(),
                            state=ServiceState.STOPPED,
                            message=f"{service.name} process not running, marked as stopped",
                            port=service.port
                        )
                        await self._emit_event(event)
                    continue

                # Only mark healthy if process is running AND health endpoint responds
                if service.state in [ServiceState.RUNNING, ServiceState.HEALTHY]:
                    healthy = await self._check_health(service)
                    if healthy and service.state != ServiceState.HEALTHY:
                        service.state = ServiceState.HEALTHY
                        event = ServiceEvent(
                            service_name=service.name,
                            timestamp=datetime.utcnow().isoformat(),
                            state=ServiceState.HEALTHY,
                            message=f"{service.name} became healthy",
                            port=service.port
                        )
                        await self._emit_event(event)
                    elif not healthy and service.state == ServiceState.HEALTHY:
                        service.state = ServiceState.UNHEALTHY
                        event = ServiceEvent(
                            service_name=service.name,
                            timestamp=datetime.utcnow().isoformat(),
                            state=ServiceState.UNHEALTHY,
                            message=f"{service.name} became unhealthy",
                            port=service.port
                        )
                        await self._emit_event(event)
    
    async def _emit_event(self, event: ServiceEvent):
        """Emit event to all WebSocket subscribers and Socket.IO clients."""
        # Emit to WebSocket subscribers
        disconnected = []
        for ws in self.event_subscribers:
            try:
                await ws.send_json(event.dict())
            except Exception:
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.event_subscribers.remove(ws)
        
        # Emit to Socket.IO clients
        try:
            from launcher.socket_server import sio
            await sio.emit('service_status', event.dict())
        except Exception as e:
            # Silently fail if Socket.IO is not available
            pass
    
    async def subscribe_events(self, websocket: WebSocket):
        """Subscribe a WebSocket client to service events."""
        await websocket.accept()
        self.event_subscribers.append(websocket)
        
        # Send current state of all services
        for service in self.services.values():
            event = ServiceEvent(
                service_name=service.name,
                timestamp=datetime.utcnow().isoformat(),
                state=service.state,
                message=f"Current state: {service.state.value}",
                port=service.port
            )
            await websocket.send_json(event.dict())
        
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.event_subscribers.remove(websocket)
    
    def start_monitoring(self):
        """Start the background health monitoring task."""
        if not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._monitor_health())


# Create FastAPI app
app = FastAPI(title="ArkNet Service Manager", version="1.0.0")
manager = ServiceManager()

# Configure CORS - will be set from config by launcher_server.py
# This is just a placeholder, actual origins are loaded from config.ini
def configure_cors(cors_origins: list):
    """Configure CORS middleware with origins from config."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup():
    """Initialize service manager on startup."""
    manager.start_monitoring()


@app.post("/services/{name}/start")
async def start_service(name: str):
    """Start a service and its dependencies."""
    import logging
    rest_logger = logging.getLogger("launcher.rest_api")
    rest_logger.info(f"REST API: start_service called with name='{name}'")
    event = await manager.start_service(name)
    rest_logger.info(f"REST API: start_service returned event for '{event.service_name}': state={event.state}")
    return event


@app.post("/services/{name}/stop")
async def stop_service(name: str):
    """Stop a running service."""
    event = await manager.stop_service(name)
    return event


@app.get("/services/{name}/status")
async def get_service_status(name: str):
    """Get detailed status of a service."""
    return await manager.get_status(name)


@app.get("/services/{name}/logs")
async def get_service_logs(name: str, lines: int = 100):
    """Get recent log lines from a service."""
    if name not in manager.services:
        raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
    
    service = manager.services[name]
    return {
        "service": name,
        "lines": service.get_logs(lines)
    }


@app.get("/services")
async def list_services():
    """Get status of all services."""
    return await manager.get_all_services()


@app.websocket("/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time service events."""
    await manager.subscribe_events(websocket)


@app.post("/reload-config")
async def reload_config():
    """Reload configuration and update registered services."""
    try:
        # Re-read config
        config_path = Path(__file__).parent / "config.ini"
        config_manager = ConfigurationManager(config_path)
        launcher_config = config_manager.get_launcher_config()
        service_configs = config_manager.get_service_configs()
        root_path = Path(__file__).parent
        
        print("🔄 Reloading configuration...")
        
        # Track current services
        current_services = set(manager.services.keys())
        
        # Define expected services based on enabled services in config
        expected_services = {name for name, config in service_configs.items() if config.enabled}
        
        # Unregister services that are no longer enabled
        to_remove = current_services - expected_services
        for service_name in to_remove:
            manager.unregister_service(service_name)
        
        # Register newly enabled services
        to_add = expected_services - current_services
        for service_name in to_add:
            service_config = service_configs[service_name]
            
            # Create ManagedService from ServiceConfig
            managed_service = ManagedService(
                name=service_config.name,
                port=service_config.port,
                health_url=service_config.health_url,
                dependencies=service_config.dependencies,
                spawn_console=service_config.spawn_console,
                startup_wait=service_config.startup_wait,
                display_name=service_config.display_name,
                description=service_config.description,
                category=service_config.category,
                icon=service_config.icon
            )
            
            # Set launch configuration based on service type
            if service_name == 'strapi':
                managed_service.script_path = root_path / "arknet_fleet_manager" / "arknet-fleet-api"
                managed_service.is_npm = True
                managed_service.npm_command = "develop"
            elif service_name == 'gpscentcom':
                managed_service.script_path = root_path / "gpscentcom_server" / "server_main.py"
            elif service_name == 'geospatial':
                managed_service.as_module = "geospatial_service"
            elif service_name == 'vehicle_simulator':
                managed_service.as_module = "arknet_transit_simulator"
                managed_service.extra_args = ["--mode", service_config.extra_config.get('mode', 'depot')]
            elif service_name == 'commuter_service':
                managed_service.as_module = "commuter_service"
            
            manager.register_service(managed_service)
            print(f"   ✅ Registered: {service_config.display_name} ({service_name})")
        
        # Update spawn_console settings for existing services
        for service_name in expected_services:
            if service_name in service_configs:
                service_config = service_configs[service_name]
                manager.update_service_config(service_name, service_config.spawn_console)
        
        print(f"✅ Config reloaded. Services: {sorted(manager.services.keys())}")
        return {"success": True, "services": sorted(manager.services.keys())}
        
    except Exception as e:
        print(f"❌ Failed to reload config: {e}")
        return {"success": False, "error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "launcher"}


@app.post("/shutdown")
async def shutdown_all_services():
    """Shutdown all services in FILO order."""
    events = await manager.shutdown_all()
    return {
        "message": "All services stopped",
        "stopped_services": len(events),
        "events": events
    }
