"""
Simple FastAPI app factory for arknet-transit-launcher.
This is a starter stub; the real server will import service_manager and adapters.
"""
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import Dict, Any, List
import os
import sys
import asyncio

import configparser
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config.ini'))

def get_enabled_services():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding='utf-8')
    services = []
    for section in config.sections():
        if section == 'launcher':
            continue
        enabled = config.getboolean(section, 'enabled', fallback=False)
        if enabled:
            services.append({
                'name': section,
                'display_name': config.get(section, 'display_name', fallback=section),
                'description': config.get(section, 'description', fallback=''),
                'category': config.get(section, 'category', fallback=''),
                'icon': config.get(section, 'icon', fallback=''),
                'port': config.get(section, 'port', fallback=''),
                'health_url': config.get(section, 'health_url', fallback=''),
                'spawn_console': config.getboolean(section, 'spawn_console', fallback=False),
                'startup_wait': config.get(section, 'startup_wait', fallback='0'),
                'dependencies': config.get(section, 'dependencies', fallback=''),
            })
    return services

# Add the current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from os_adapters import systemd, windows_service
from health import RedisHealthChecker

# Import RedisServiceManager for service management
try:
    from health.redis_service_manager import RedisServiceManager
    SERVICE_MANAGER_AVAILABLE = True
except ImportError:
    SERVICE_MANAGER_AVAILABLE = False

# Global registry to track managed processes
import atexit
import signal
managed_processes = []

def cleanup_all_processes():
    """Kill all managed processes on shutdown"""
    import psutil
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Shutting down - terminating all managed services...")
    
    for proc_info in managed_processes:
        try:
            proc = psutil.Process(proc_info['pid'])
            logger.info(f"Terminating {proc_info['service']} (PID {proc_info['pid']})")
            # Kill all children first
            for child in proc.children(recursive=True):
                child.kill()
            proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    managed_processes.clear()

# Register cleanup handler
atexit.register(cleanup_all_processes)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    cleanup_all_processes()
    sys.exit(0)

# Register signal handlers (Windows supports SIGTERM, SIGINT)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def create_app() -> FastAPI:
    # Initialize Redis health checker
    redis_url = os.getenv("REDIS_URL", None)
    redis_health_checker = RedisHealthChecker(
        redis_url=redis_url,
        latency_threshold_ms=float(os.getenv("REDIS_LATENCY_THRESHOLD_MS", "100.0"))
    )

    # Initialize Redis service manager
    redis_service_manager = RedisServiceManager() if SERVICE_MANAGER_AVAILABLE else None

    # Store Redis status
    redis_status = {}
    
    async def update_redis_health():
        """Periodically update Redis health status"""
        nonlocal redis_status
        while True:
            try:
                redis_status = await redis_health_checker.check_health()
            except Exception as e:
                redis_status = {
                    "name": "redis",
                    "state": "unhealthy",
                    "message": f"Health check error: {str(e)}"
                }
            await asyncio.sleep(float(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30.0")))
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan event handler for startup/shutdown"""
        # Startup
        asyncio.create_task(update_redis_health())
        yield
        # Shutdown - cleanup all managed processes
        cleanup_all_processes()
    
    app = FastAPI(title="ArkNet Transit Launcher", lifespan=lifespan)

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "arknet-transit-launcher"}
    

    @app.get("/services")
    async def get_services_status() -> List[Dict[str, Any]]:
        """Get all enabled services from config.ini with real-time status"""
        import psutil
        services = get_enabled_services()
        
        # Check actual running status for each service
        import requests
        for service in services:
            service_name = service['name']
            port = service.get('port', '')
            health_url = service.get('health_url', '')
            is_running = False
            is_healthy = None
            pid_list = []

            try:
                # Check by port
                if port:
                    for conn in psutil.net_connections():
                        if conn.laddr.port == int(port) and conn.status == 'LISTEN':
                            is_running = True
                            if conn.pid and conn.pid not in pid_list:
                                pid_list.append(conn.pid)

                # Also check by process patterns
                if service_name == 'strapi':
                    patterns = ['npm', 'node']
                    cwd_pattern = 'arknet-fleet-api'
                elif service_name == 'gpscentcom':
                    patterns = ['python']
                    cwd_pattern = 'gpscentcom'
                elif service_name == 'nextjs_admin':
                    patterns = ['npm', 'node', 'next']
                    cwd_pattern = 'dashboard'
                elif service_name == 'vehicle_simulator':
                    patterns = ['python']
                    cwd_pattern = 'arknet_transit_simulator'
                else:
                    patterns = []
                    cwd_pattern = None

                if cwd_pattern:
                    for proc in psutil.process_iter(['pid', 'name', 'cwd', 'cmdline']):
                        try:
                            if proc.info['name'] in patterns:
                                cwd = proc.info.get('cwd', '')
                                cmdline = ' '.join(proc.info.get('cmdline', []))
                                if cwd_pattern in cwd or cwd_pattern in cmdline:
                                    is_running = True
                                    if proc.info['pid'] not in pid_list:
                                        pid_list.append(proc.info['pid'])
                        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                            continue
            except (ValueError, AttributeError):
                pass

            # Health check if running and health_url defined

            if is_running and health_url:
                try:
                    resp = requests.get(health_url, timeout=2)
                    if resp.status_code in (200, 204):
                        is_healthy = True
                    else:
                        is_healthy = False
                except Exception:
                    is_healthy = False

            # Add runtime status to service info
            if is_running:
                if is_healthy is False:
                    service['state'] = 'unhealthy'
                else:
                    service['state'] = 'running'
            else:
                service['state'] = 'stopped'
            service['pids'] = pid_list if pid_list else []

        return services

    @app.post("/services/{service_name}/start")
    async def start_service(service_name: str) -> Dict[str, Any]:
        services = get_enabled_services()
        service = next((s for s in services if s['name'] == service_name), None)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found or not enabled")
        # Actually start the process if exe_cmd is defined
        import subprocess
        import logging
        logger = logging.getLogger(__name__)
        
        exe_cmd = None
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH, encoding='utf-8')
        if config.has_option(service_name, 'exe_cmd'):
            exe_cmd = config.get(service_name, 'exe_cmd')
        if exe_cmd:
            try:
                # Get service display name and spawn_console setting
                display_name = service.get('display_name', service_name)
                spawn_console = service.get('spawn_console', False)
                logger.info(f"Starting {display_name}...")
                
                # Get the working directory (project root)
                work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
                
                # Start the process with proper settings
                if sys.platform == 'win32' and spawn_console:
                    # For Windows with console: use cmd /k to keep console open
                    cmd = f'cmd /k "cd /d {work_dir} && {exe_cmd}"'
                    proc = subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                elif sys.platform == 'win32':
                    # For Windows without console: hide the window
                    proc = subprocess.Popen(
                        exe_cmd,
                        shell=True,
                        cwd=work_dir,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    # For non-Windows platforms
                    proc = subprocess.Popen(
                        exe_cmd,
                        shell=True,
                        cwd=work_dir
                    )
                
                # Register the process for cleanup on shutdown
                import time
                time.sleep(0.5)  # Give process time to spawn children
                managed_processes.append({
                    'service': service_name,
                    'pid': proc.pid,
                    'started_at': time.time()
                })
                logger.info(f"Registered {display_name} process (PID {proc.pid}) for lifecycle management")
                
                # Return immediate feedback
                msg = f"{display_name} is starting..."
                if spawn_console:
                    msg += " Check the console window for progress."
                
                return {
                    "message": msg,
                    "success": True,
                    "service_name": service_name,
                    "status": "starting"
                }
            except Exception as e:
                logger.error(f"Failed to start {service_name}: {str(e)}")
                return {"message": f"Failed to start '{service_name}': {str(e)}", "success": False}
        else:
            return {"message": f"Service '{service_name}' has no exe_cmd defined in config.ini", "success": False}

    @app.post("/services/{service_name}/stop")
    async def stop_service(service_name: str) -> Dict[str, Any]:
        services = get_enabled_services()
        service = next((s for s in services if s['name'] == service_name), None)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found or not enabled")
        
        import psutil
        import logging
        logger = logging.getLogger(__name__)
        
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH, encoding='utf-8')
        
        # Get service port to identify processes
        port = config.get(service_name, 'port', fallback=None)
        display_name = service.get('display_name', service_name)
        

        killed = 0
        try:
            # Collect all candidate PIDs
            candidate_pids = set()
            # By port
            if port:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        for conn in proc.info.get('connections', []):
                            if conn.laddr.port == int(port):
                                candidate_pids.add(proc.info['pid'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                        continue
            # By process name/cwd pattern
            if service_name == 'strapi':
                patterns = ['npm', 'node']
                cwd_pattern = 'arknet-fleet-api'
            elif service_name == 'gpscentcom':
                patterns = ['python']
                cwd_pattern = 'gpscentcom'
            elif service_name == 'nextjs_admin':
                patterns = ['npm', 'node', 'next']
                cwd_pattern = 'dashboard'
            else:
                patterns = []
                cwd_pattern = None
            if cwd_pattern:
                for proc in psutil.process_iter(['pid', 'name', 'cwd', 'cmdline']):
                    try:
                        if proc.info['name'] in patterns:
                            cwd = proc.info.get('cwd', '')
                            cmdline = ' '.join(proc.info.get('cmdline', []))
                            if cwd_pattern in cwd or cwd_pattern in cmdline:
                                candidate_pids.add(proc.info['pid'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                        continue
            # By managed_processes registry
            global managed_processes
            for proc_info in managed_processes:
                if proc_info['service'] == service_name:
                    candidate_pids.add(proc_info['pid'])
            # Kill all candidates
            for pid in candidate_pids:
                try:
                    parent = psutil.Process(pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
                    killed += 1
                    logger.info(f"Killed {parent.name()} (PID {pid}) for service {service_name}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            # Remove from managed_processes
            managed_processes = [p for p in managed_processes if p['service'] != service_name or p['pid'] not in candidate_pids]
            if killed > 0:
                return {"message": f"Stopped {display_name} ({killed} process(es) terminated)", "success": True}
            else:
                return {"message": f"No running process found for {display_name}", "success": False}
        except Exception as e:
            logger.error(f"Error stopping {service_name}: {str(e)}")
            return {"message": f"Error stopping {display_name}: {str(e)}", "success": False}

    @app.get("/services/processes")
    async def get_all_processes() -> Dict[str, Any]:
        """Get all processes related to managed services for monitoring"""
        import psutil
        
        processes = []
        service_patterns = {
            'strapi': {'names': ['npm', 'node'], 'cwd': 'arknet-fleet-api'},
            'gpscentcom': {'names': ['python'], 'cwd': 'gpscentcom'},
            'nextjs_admin': {'names': ['npm', 'node', 'next'], 'cwd': 'dashboard'},
            'vehicle_simulator': {'names': ['python'], 'cwd': 'arknet_transit_simulator'},
            'redis': {'names': ['redis-server'], 'cwd': None}
        }
        
        for service_name, patterns in service_patterns.items():
            for proc in psutil.process_iter(['pid', 'name', 'cwd', 'cmdline', 'create_time', 'memory_info']):
                try:
                    if proc.info['name'] in patterns['names']:
                        cwd = proc.info.get('cwd', '')
                        cmdline = ' '.join(proc.info.get('cmdline', []))
                        
                        if patterns['cwd'] is None or patterns['cwd'] in cwd or patterns['cwd'] in cmdline:
                            processes.append({
                                'service': service_name,
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': cmdline[:100] + '...' if len(cmdline) > 100 else cmdline,
                                'memory_mb': round(proc.info['memory_info'].rss / 1024 / 1024, 1),
                                'create_time': proc.info['create_time']
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                    continue
        
        return {'processes': processes, 'total': len(processes)}

    @app.post("/autostart/enable")
    async def enable_autostart(service: str) -> Dict[str, Any]:
        """Enable autostart for a service."""
        if os.name == 'nt':  # Windows
            # Assume task name is service name
            result = windows_service.enable_user_autostart(service, f'"{service}"')  # Placeholder command
        else:  # Linux
            result = systemd.enable(service, user=True)
        
        if not result.get('ok'):
            raise HTTPException(status_code=500, detail=f"Failed to enable autostart: {result}")
        
        return {"message": f"Autostart enabled for {service}"}

    @app.post("/autostart/disable")
    async def disable_autostart(service: str) -> Dict[str, Any]:
        """Disable autostart for a service."""
        if os.name == 'nt':  # Windows
            result = windows_service.disable_user_autostart(service)
        else:  # Linux
            result = systemd.disable(service, user=True)
        
        if not result.get('ok'):
            raise HTTPException(status_code=500, detail=f"Failed to disable autostart: {result}")
        
        return {"message": f"Autostart disabled for {service}"}

    @app.get("/autostart/status")
    async def get_autostart_status(service: str) -> Dict[str, Any]:
        """Get autostart status for a service."""
        if os.name == 'nt':  # Windows
            enabled = windows_service.is_user_autostart_enabled(service)
        else:  # Linux
            enabled = systemd.is_active(service, user=True)
        
        return {"service": service, "autostart_enabled": enabled}

    @app.post("/services/redis/start")
    async def start_redis_service() -> Dict[str, Any]:
        """Start the Redis service using service manager."""
        if not redis_service_manager:
            raise HTTPException(status_code=500, detail="Redis service manager not available")

        success = redis_service_manager.ensure_running()
        if success:
            return {"message": "Redis service started successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start Redis service")

    @app.post("/services/redis/stop")
    async def stop_redis_service() -> Dict[str, Any]:
        """Stop the Redis service using service manager."""
        if not redis_service_manager:
            raise HTTPException(status_code=500, detail="Redis service manager not available")

        success = redis_service_manager.stop_service()
        if success:
            return {"message": "Redis service stopped successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to stop Redis service")

    @app.post("/services/redis/enable")
    async def enable_redis_service() -> Dict[str, Any]:
        """Enable Redis service auto-start."""
        if not redis_service_manager:
            raise HTTPException(status_code=500, detail="Redis service manager not available")

        success = redis_service_manager.ensure_auto_start()
        if success:
            return {"message": "Redis service auto-start enabled"}
        else:
            raise HTTPException(status_code=500, detail="Failed to enable Redis service auto-start")


    return app

# Expose FastAPI app for Uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
