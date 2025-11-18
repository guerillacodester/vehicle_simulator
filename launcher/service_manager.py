from fastapi import APIRouter, Request
from fastapi.responses import Response
# Create APIRouter for service endpoints
service_router = APIRouter()
# --- LOGIN ENDPOINT FOR ELECTRON UI ---
@service_router.post("/login")
async def login(request: Request):
    """Authenticate user via Strapi GraphQL and return JWT/cookie."""
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required.")

    # Strapi GraphQL login mutation
    graphql_url = "http://localhost:1337/graphql"  # Update if needed
    query = '''mutation Login($identifier: String!, $password: String!) { login(input: { identifier: $identifier, password: $password }) { jwt user { id username email } } }'''
    variables = {"identifier": username, "password": password}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(graphql_url, json={"query": query, "variables": variables})
            result = resp.json()
            jwt = result.get("data", {}).get("login", {}).get("jwt")
            user = result.get("data", {}).get("login", {}).get("user")
            if not jwt or not user:
                raise HTTPException(status_code=401, detail="Invalid credentials.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

    # Set JWT as HTTP-only cookie
    import json
    response = Response(content=json.dumps({"success": True, "user": user}), media_type="application/json")
    response.set_cookie(key="jwt", value=jwt, httponly=True, max_age=86400)
    return response
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
from typing import Dict

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
    version: str = "1.0"
    event_type: str = "service_status"


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
    extra_config: Dict[str, str] = field(default_factory=dict)
    # Raw command for non-Python executables (e.g. ['redis-server', '--port', '6379'])
    raw_command: Optional[List[str]] = None
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

    def create_status_event(self, service, new_state):
        from datetime import datetime
        return ServiceEvent(
            service_name=service.name,
            timestamp=datetime.utcnow().isoformat(),
            state=new_state,
            message=f"Service {service.name} is {new_state.value if hasattr(new_state, 'value') else str(new_state)}",
            port=service.port
        )

    def __init__(self):
        """Initialize the service manager."""
        self.services: Dict[str, ManagedService] = {}
        self.event_subscribers: List[WebSocket] = []
        self.http_client = httpx.AsyncClient(timeout=5.0)
        self._monitor_task: Optional[asyncio.Task] = None
        self._startup_order: List[str] = []  # Track startup order for FILO shutdown
        self._last_service_states: Dict[str, str] = {}  # Track last emitted state for each service
    
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
        pass
        
        if name not in self.services:
            pass
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
        
        service = self.services[name]
        
        # Dependencies are checked but not automatically started
        # (User must start them manually or all at once)
        import logging
        pass
        
        # Just warn if dependencies are not healthy
        for dep_name in service.dependencies:
            dep = self.services.get(dep_name)
            if not dep:
                pass
        
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
        # Respect auto_start configuration: prefer OS-native system service when configured
        auto_start_mode = (service.extra_config.get('auto_start') or service.extra_config.get('autoStart') or 'process').lower() if service.extra_config else 'process'
        if auto_start_mode == 'system_service':
            import logging
            # Ensure startup_logger exists before use
            pass
            try:
                pass
                adapter = None
                if sys.platform.startswith('linux'):
                    try:
                        from arknet_transit_launcher.os_adapters import systemd as _systemd
                        adapter = _systemd
                        adapter_type = 'systemd'
                    except Exception:
                        adapter = None
                        adapter_type = None
                elif sys.platform.startswith('win'):
                    try:
                        from arknet_transit_launcher.os_adapters import windows_service as _win
                        adapter = _win
                        adapter_type = 'windows'
                    except Exception:
                        adapter = None
                        adapter_type = None

                if adapter:
                    detect_result = adapter.detect(service.name, service.extra_config)
                    if detect_result.get('exists'):
                        unit_or_name = detect_result.get('unit_name') or detect_result.get('service_name') or service.name
                        # Determine user scope for systemd adapters
                        scope = service.extra_config.get('autostart_scope', detect_result.get('scope') or 'system')
                        user_flag = True if str(scope).lower() == 'user' else False
                        pass
                        try:
                            if adapter_type == 'systemd':
                                # systemd.start(unit_name, user: bool=False)
                                start_res = adapter.start(unit_or_name, user=user_flag)
                            else:
                                # windows adapter: start(name)
                                start_res = adapter.start(unit_or_name)
                        except TypeError:
                            # Fallback if adapter has a different signature
                            try:
                                start_res = adapter.start(unit_or_name)
                            except Exception as e:
                                start_res = {"ok": False, "error": str(e)}

                        if start_res.get('ok'):
                            # Emit an event indicating OS-managed start
                            service.state = ServiceState.STARTING
                            event = ServiceEvent(
                                service_name=name,
                                timestamp=datetime.utcnow().isoformat(),
                                state=ServiceState.STARTING,
                                message=f"Requested OS service start for {unit_or_name}",
                                port=service.port
                            )
                            await self._emit_event(event)
                            # Give OS a moment and check active state
                            await asyncio.sleep(1)
                            is_act = False
                            try:
                                if adapter_type == 'systemd' and hasattr(adapter, 'is_active'):
                                    is_act = adapter.is_active(unit_or_name, user=user_flag)
                                elif adapter_type == 'windows' and hasattr(adapter, 'is_active'):
                                    is_act = adapter.is_active(unit_or_name)
                                else:
                                    is_act = False
                            except Exception:
                                is_act = False

                            if is_act:
                                service.state = ServiceState.RUNNING
                                emoji = "🟢"
                                color_start = "\033[92m"  # Green
                                color_end = "\033[0m"
                                message = f"{emoji} {color_start}Service {name} has started (PID: {service.process.pid}){color_end}"
                                event = ServiceEvent(
                                    service_name=name,
                                    timestamp=datetime.utcnow().isoformat(),
                                    state=ServiceState.RUNNING,
                                    message=message,
                                    port=service.port,
                                    event_type="service_started"
                                )
                                print(message)
                                await self._emit_event(event)
                                return event
                            else:
                                pass
                        else:
                            pass
            except Exception as e:
                pass

        if service.raw_command:
            # Raw command provided (useful for executables like redis-server)
            cmd = list(service.raw_command) + (service.extra_args or [])
            cwd = service.script_path.parent if service.script_path else Path.cwd()
        elif service.is_npm:
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
            # If script_path points to a native executable (.exe/.bat/.cmd) run it directly
            if service.script_path and service.script_path.suffix.lower() in ['.exe', '.bat', '.cmd']:
                cmd = [str(service.script_path)] + (service.extra_args or [])
                cwd = service.script_path.parent
            else:
                # Default: execute as Python script
                cmd = [sys.executable, str(service.script_path)] + (service.extra_args or [])
                cwd = service.script_path.parent
        
        # Start subprocess
        try:
            # Set environment to force UTF-8 encoding for subprocess output
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            import logging
            pass
            
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
            
            pass
            
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
                message=f"Service {name} has started (PID: {service.process.pid})",
                port=service.port,
                event_type="service_status"
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
                pass
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
        pass
        if not service.is_running():
            pass
            return ServiceEvent(
                service_name=name,
                timestamp=datetime.utcnow().isoformat(),
                state=ServiceState.STOPPED,
                message=f"{name} is not running",
                port=service.port
            )

        pass
        try:
            service.process.terminate()
            service.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            service.process.kill()
        except Exception:
            pass

        # Clear process reference
        service.process = None
        service.state = ServiceState.STOPPED
        message = f"Service {name} has stopped"
        event = ServiceEvent(
            service_name=name,
            timestamp=datetime.utcnow().isoformat(),
            state=ServiceState.STOPPED,
            message=message,
            port=service.port,
            event_type="service_status"
        )
        print(message)
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

        # Generate status message based on current state
        message = ""
        if service.state == ServiceState.RUNNING or service.state == ServiceState.HEALTHY:
            message = f"Running on port {service.port}" if service.port else "Running"
        elif service.state == ServiceState.STARTING:
            message = "Starting service..."
        elif service.state == ServiceState.STOPPED:
            message = "Service is stopped"
        elif service.state == ServiceState.FAILED:
            message = "Service failed to start"
        elif service.state == ServiceState.UNHEALTHY:
            message = "Service is unhealthy"
        
        status = {
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
            "type": service.category,  # Map category to type for UI compatibility
            "icon": service.icon,
            "message": message
        }

        # If this is the redis managed service, add detection info (non-blocking)
        if service.name == 'redis':
            try:
                import asyncio
                from launcher.health import redis_probe

                host = service.extra_args[0] if service.extra_args and len(service.extra_args) >= 1 and service.extra_args[0].isdigit() is False and ':' in service.extra_args[0] else None
                # Prefer configured port, fall back to 6379
                port = service.port or 6379

                # We will run the blocking probe in a thread to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                probe_result = await loop.run_in_executor(None, redis_probe, '127.0.0.1' if not host else host.split(':')[0], port)

                status["detection"] = probe_result
                status["installed"] = probe_result.get("on_path", False) or bool(probe_result.get("system_service"))
                status["listening"] = probe_result.get("listening", False)
            except Exception as e:
                # Best-effort: don't fail the status endpoint
                status["detection_error"] = str(e)

        return status
    
    async def get_all_services(self) -> List[dict]:
        """Get status of all services."""
        return [await self.get_status(name) for name in self.services.keys()]
    
    async def _check_health(self, service: ManagedService) -> bool:
        """Check if service is healthy via HTTP health endpoint."""
        # If the service exposes an HTTP health_url, use it
        if service.health_url:
            try:
                response = await self.http_client.get(service.health_url)
                # Accept 200 OK or 204 No Content as healthy
                return response.status_code in [200, 204]
            except Exception:
                return False

        # Special-case Redis: use direct Redis ping for health check
        if service.name == 'redis':
            import logging
            pass
            try:
                import redis.asyncio as aioredis
                redis_client = aioredis.from_url(
                    f"redis://localhost:{service.port or 6379}",
                    socket_connect_timeout=2
                )
                result = await redis_client.ping()
                await redis_client.close()
                pass
                return result is True
            except Exception as e:
                pass
                return False

        # Default: no health URL, assume service is running if process exists
        return True
    
    async def _capture_output(self, service: ManagedService):
        """Capture stdout/stderr from service process and log to file."""
        import logging
        pass
        
        try:
            # Read combined stdout/stderr stream
            loop = asyncio.get_event_loop()
            while service.is_running():
                try:
                    line = await loop.run_in_executor(None, service.process.stdout.readline)
                    if line:
                        timestamp = datetime.utcnow().isoformat()
                        service.stdout_buffer.append(f"{timestamp} | {line.strip()}")
                        pass
                    else:
                        break
                except Exception as e:
                    pass
                    break
        except Exception as e:
            pass
    
    async def _monitor_health(self):
        """Background task that monitors service health."""
        import logging
        pass
        
        # Emit initial state for all services on startup
        pass
        # Get config for all services (even if not started)
        from launcher.config import ConfigurationManager
        config_path = Path(__file__).parent.parent / "config.ini"
        config_manager = ConfigurationManager(config_path)
        service_configs = config_manager.get_service_configs()
        for name, config in service_configs.items():
            service = self.services.get(name)
            # Determine runtime state
            if service:
                if config.enabled:
                    if service.health_url or service.name == 'redis':
                        healthy = await self._check_health(service)
                        initial_state = ServiceState.HEALTHY if healthy else ServiceState.STOPPED
                    elif service.is_running():
                        healthy = await self._check_health(service)
                        initial_state = ServiceState.HEALTHY if healthy else ServiceState.RUNNING
                    else:
                        initial_state = ServiceState.STOPPED
                else:
                    initial_state = ServiceState.STOPPED
                service.state = initial_state
                self._last_service_states[service.name] = initial_state.value
            else:
                initial_state = ServiceState.STOPPED
            # Build event with all config and runtime info
            event = ServiceEvent(
                service_name=name,
                timestamp=datetime.utcnow().isoformat(),
                state=initial_state,
                message=f"{name} initial state: {initial_state.value}",
                port=config.port,
                version="1.0",
                event_type="service_status"
            )
            # Attach extra config info for UI
            event_dict = event.dict()
            event_dict.update({
                "enabled": config.enabled,
                "spawn_console": config.spawn_console,
                "display_name": config.display_name,
                "description": config.description,
                "category": config.category,
                "icon": config.icon,
                "dependencies": config.dependencies,
                "extra_config": config.extra_config,
            })
            # Color and style for state
            state_color = {
                "healthy": "\033[92m",   # Green
                "stopped": "\033[91m",   # Red
                "starting": "\033[93m",  # Yellow
                "running": "\033[94m",   # Blue
                "unhealthy": "\033[95m", # Magenta
                "failed": "\033[41m"     # Red background
            }.get(initial_state.value, "\033[0m")
            bold = "\033[1m"
            reset = "\033[0m"
            # Tabular header (only print once per run)
            if not hasattr(self, '_table_header_printed'):
                print(f"{bold}{'='*78}{reset}")
                print(f"{bold}| {'SERVICE':<18} | {'STATE':<10} | {'ENABLED':<7} | {'CONSOLE':<7} | {'DESCRIPTION':<30} |{reset}")
                print(f"{bold}{'-'*78}{reset}")
                self._table_header_printed = True
            # Tabular row
            print(f"| {name:<18} | {state_color}{initial_state.value.upper():<10}{reset} | {str(config.enabled):<7} | {str(config.spawn_console):<7} | {config.description[:30]:<30} |")
            # Emit event with full details
            await self._emit_event(ServiceEvent.parse_obj(event_dict))
        
        while True:
            await asyncio.sleep(2)  # Check every 2 seconds

            for service in self.services.values():
                # Check if process has exited unexpectedly
                if service.process is not None and not service.is_running():
                    exit_code = service.process.returncode
                    # Logging suppressed
                    # If exit code is non-zero, mark as FAILED and do NOT restart
                    if exit_code != 0:
                        if service.state != ServiceState.FAILED or self._last_service_states.get(service.name) != ServiceState.FAILED.value:
                            service.state = ServiceState.FAILED
                            self._last_service_states[service.name] = ServiceState.FAILED.value
                            pass
                            event = self.create_status_event(service, ServiceState.FAILED)
                            await self._emit_event(event)
                        # Clear process reference so we don't keep checking it
                        service.process = None
                        continue  # Do not attempt restart or further state changes
                    # Clear process reference for any other exit
                    service.process = None

                # For services with health checks, use health status to determine state
                # (supports externally-managed services like Strapi/Redis)
                if service.health_url or service.name == 'redis':
                    healthy = await self._check_health(service)
                    new_state = ServiceState.HEALTHY if healthy else ServiceState.STOPPED
                    
                    # Only emit if state changed
                    if service.state != new_state or self._last_service_states.get(service.name) != new_state.value:
                        prev_state = service.state.value if isinstance(service.state, ServiceState) else str(service.state)
                        service.state = new_state
                        self._last_service_states[service.name] = new_state.value
                        # Tabular update format
                        state_color = {
                            "healthy": "\033[92m",   # Green
                            "stopped": "\033[91m",   # Red
                            "starting": "\033[93m",  # Yellow
                            "running": "\033[94m",   # Blue
                            "unhealthy": "\033[95m", # Magenta
                            "failed": "\033[41m"     # Red background
                        }.get(new_state.value, "\033[0m")
                        bold = "\033[1m"
                        reset = "\033[0m"
                        # Print status table only when state changes
                        if not hasattr(self, '_last_table_printed') or self._last_table_printed != f"{service.name}:{new_state.value}":
                            print(f"{bold}{'-'*78}{reset}")
                            print(f"| {service.name:<18} | {state_color}{new_state.value.upper():<10}{reset} | {str(getattr(service, 'enabled', True)):<7} | {str(getattr(service, 'spawn_console', False)):<7} | {getattr(service, 'description', '')[:30]:<30} |")
                            print(f"{bold}{'-'*78}{reset}")
                            self._last_table_printed = f"{service.name}:{new_state.value}"
                        event = self.create_status_event(service, new_state)
                        await self._emit_event(event)
                # For process-managed services, check if running
                elif not service.is_running():
                    # Only emit if state changed
                    if service.state != ServiceState.STOPPED or self._last_service_states.get(service.name) != ServiceState.STOPPED.value:
                        service.state = ServiceState.STOPPED
                        self._last_service_states[service.name] = ServiceState.STOPPED.value
                        event = self.create_status_event(service, ServiceState.STOPPED)
                        await self._emit_event(event)
                else:
                    healthy = await self._check_health(service)
                    new_state = ServiceState.HEALTHY if healthy else ServiceState.UNHEALTHY
                    
                    # Only emit if state changed
                    if service.state != new_state or self._last_service_states.get(service.name) != new_state.value:
                        service.state = new_state
                        self._last_service_states[service.name] = new_state.value
                        event = self.create_status_event(service, new_state)
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
        import logging
        pass
        event_data = event.dict()
        pass
        try:
            from launcher.socket_server import sio
            await sio.emit('service_status', event.dict())
        except Exception:
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




async def _start_service_safely(name: str):
    """Helper to start a service and swallow errors to avoid crashing startup."""
    try:
        await manager.start_service(name)
    except Exception:
        return


@app.post("/services/{name}/start")
async def start_service(name: str):
    """Start a service and its dependencies."""
    import logging
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
    """WebSocket endpoint for real-time service events. Requires authentication token as query param."""
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
                extra_config=service_config.extra_config,
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
            elif service_name == 'redis':
                # Allow exe_path or exe_cmd via extra_config. If exe_cmd present, treat as raw command.
                exe_path = service_config.extra_config.get('exe_path')
                exe_cmd = service_config.extra_config.get('exe_cmd')
                if exe_path:
                    managed_service.script_path = Path(exe_path)
                elif exe_cmd:
                    managed_service.raw_command = [exe_cmd]
                else:
                    # Default to relying on redis-server on PATH
                    managed_service.raw_command = ['redis-server']
                # If port configured, pass it as an extra arg
                if service_config.port:
                    managed_service.extra_args = [str(service_config.port)]
            
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
