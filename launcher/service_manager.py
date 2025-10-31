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
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx


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
    
    async def start_service(self, name: str) -> ServiceEvent:
        """
        Start a service and its dependencies.
        
        Returns:
            ServiceEvent with the result
        """
        if name not in self.services:
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
        
        service = self.services[name]
        
        # Check dependencies first
        for dep_name in service.dependencies:
            dep = self.services.get(dep_name)
            if not dep or dep.state != ServiceState.HEALTHY:
                event = ServiceEvent(
                    service_name=name,
                    timestamp=datetime.utcnow().isoformat(),
                    state=ServiceState.FAILED,
                    message=f"Dependency '{dep_name}' is not healthy",
                    port=service.port
                )
                await self._emit_event(event)
                raise HTTPException(
                    status_code=412,
                    detail=f"Dependency '{dep_name}' must be healthy first"
                )
        
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
        
        # Build command
        if service.is_npm:
            # On Windows, npm is typically npm.cmd
            npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
            cmd = [npm_cmd, 'run', service.npm_command] if service.npm_command else [npm_cmd, 'start']
            cwd = service.script_path
        elif service.as_module:
            cmd = [sys.executable, '-m', service.as_module] + (service.extra_args or [])
            cwd = Path.cwd()
        else:
            cmd = [sys.executable, str(service.script_path)] + (service.extra_args or [])
            cwd = service.script_path.parent
        
        # Start subprocess
        try:
            # Set environment to force UTF-8 encoding for subprocess output
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Platform-specific console spawning
            if service.spawn_console:
                if sys.platform == 'win32':
                    # Windows: Use 'start' command with new console
                    # Create a batch file to run the command (avoids quoting hell)
                    import tempfile
                    batch_content = f'@echo off\ncd /d "{cwd}"\n'
                    
                    # Build the command with proper escaping
                    cmd_parts = []
                    for part in cmd:
                        part_str = str(part)
                        # Escape special characters and quote if contains spaces
                        if ' ' in part_str or '&' in part_str or '|' in part_str:
                            # Escape internal quotes
                            part_str = part_str.replace('"', '""')
                            cmd_parts.append(f'"{part_str}"')
                        else:
                            cmd_parts.append(part_str)
                    
                    batch_content += ' '.join(cmd_parts) + '\n'
                    batch_content += 'pause\n'  # Keep window open on error
                    
                    # Write batch file
                    batch_file = tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False)
                    batch_file.write(batch_content)
                    batch_file.close()
                    
                    # Start new console running the batch file
                    service.process = subprocess.Popen(
                        f'start "{service.name}" cmd.exe /c "{batch_file.name}"',
                        shell=True,
                        env=env
                    )
                else:
                    # Linux: Try common terminal emulators
                    # Priority: gnome-terminal, xterm, konsole, xfce4-terminal
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
                        raise RuntimeError("No suitable terminal emulator found. Install gnome-terminal, xterm, konsole, or xfce4-terminal.")
            else:
                # Normal background process (no console)
                service.process = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace',  # Replace unencodable characters instead of crashing
                    env=env
                )
            
            service.start_time = datetime.utcnow()
            service.state = ServiceState.RUNNING
            
            # Start capturing output in background (only if not spawning console)
            if not service.spawn_console:
                asyncio.create_task(self._capture_output(service))
            
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
                await asyncio.sleep(2)  # Give it time to bind port
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
        
        if not service.is_running():
            return ServiceEvent(
                service_name=name,
                timestamp=datetime.utcnow().isoformat(),
                state=ServiceState.STOPPED,
                message=f"{name} is not running",
                port=service.port
            )
        
        # Terminate process
        service.process.terminate()
        try:
            service.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            service.process.kill()
        
        service.state = ServiceState.STOPPED
        event = ServiceEvent(
            service_name=name,
            timestamp=datetime.utcnow().isoformat(),
            state=ServiceState.STOPPED,
            message=f"{name} stopped",
            port=service.port
        )
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
            "log_lines": len(service.stdout_buffer) + len(service.stderr_buffer)
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
        """Capture stdout/stderr from service process."""
        async def read_stream(stream, buffer):
            loop = asyncio.get_event_loop()
            while service.is_running():
                try:
                    line = await loop.run_in_executor(None, stream.readline)
                    if line:
                        buffer.append(f"{datetime.utcnow().isoformat()} | {line.strip()}")
                    else:
                        break
                except Exception:
                    break
        
        # Capture both stdout and stderr concurrently
        await asyncio.gather(
            read_stream(service.process.stdout, service.stdout_buffer),
            read_stream(service.process.stderr, service.stderr_buffer),
            return_exceptions=True
        )
    
    async def _monitor_health(self):
        """Background task that monitors service health."""
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            for service in self.services.values():
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
        """Emit event to all WebSocket subscribers."""
        disconnected = []
        for ws in self.event_subscribers:
            try:
                await ws.send_json(event.dict())
            except Exception:
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.event_subscribers.remove(ws)
    
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


@app.on_event("startup")
async def startup():
    """Initialize service manager on startup."""
    manager.start_monitoring()


@app.post("/services/{name}/start")
async def start_service(name: str):
    """Start a service and its dependencies."""
    event = await manager.start_service(name)
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
