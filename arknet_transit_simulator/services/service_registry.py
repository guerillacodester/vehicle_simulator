"""
Service Registry and Lifecycle Management
==========================================

Manages service definitions, process spawning, health checks, and lifecycle.

Single Responsibility:
  - Track service definitions (name, command, port, health URL)
  - Spawn/terminate service processes
  - Check service health status
  - Auto-restart failed services

SOLID Principles:
  - SRP: Only manages service lifecycle (no HTTP routing)
  - OCP: Extensible service list (add new services without modifying code)
  - LSP: All services follow common interface
  - ISP: Focused interface (just lifecycle methods)
  - DIP: Depends on abstractions (ServiceDefinition)
"""

import asyncio
import logging
import subprocess
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import sys
import os

import httpx


logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service lifecycle states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ServiceDefinition:
    """Service configuration"""
    name: str                           # e.g., 'simulator', 'gpscentcom'
    module: str                         # Python module (e.g., 'arknet_transit_simulator')
    port: Optional[int] = None          # Service port (if applicable)
    health_url: Optional[str] = None    # Health check endpoint
    health_timeout: float = 10.0        # Health check timeout in seconds
    startup_timeout: float = 30.0       # Startup timeout in seconds
    dependencies: Optional[List[str]] = None  # Services that must start first
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
    
    def get_command(self, extra_args: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Build command to start service
        
        Args:
            extra_args: Additional arguments (service-specific)
        
        Returns:
            Command as list of strings
        """
        cmd = [sys.executable, '-m', self.module]
        
        # Add service-specific args if provided
        if extra_args:
            for key, value in extra_args.items():
                if value is not None:
                    if isinstance(value, bool):
                        if value:
                            cmd.append(f'--{key}')
                    else:
                        cmd.append(f'--{key}')
                        cmd.append(str(value))
        
        return cmd


@dataclass
class ServiceProcess:
    """Running service process"""
    definition: ServiceDefinition
    process: Optional[subprocess.Popen] = None
    status: ServiceStatus = ServiceStatus.STOPPED
    started_at: Optional[datetime] = None
    error: Optional[str] = None
    restart_count: int = 0
    
    @property
    def uptime_seconds(self) -> Optional[float]:
        """Seconds since service started"""
        if self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None
    
    @property
    def pid(self) -> Optional[int]:
        """Process ID"""
        return self.process.pid if self.process else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        return {
            'name': self.definition.name,
            'status': self.status.value,
            'pid': self.pid,
            'uptime': self.uptime_seconds,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'error': self.error,
            'restart_count': self.restart_count,
        }


class ServiceRegistry:
    """
    Manages service lifecycle (spawn, health check, restart, shutdown)
    
    Responsibilities:
      - Track all service definitions
      - Spawn service processes with correct arguments
      - Check service health via HTTP endpoints
      - Auto-restart failed services
      - Graceful shutdown in dependency order
    """
    
    def __init__(self):
        """Initialize service registry"""
        self.services: Dict[str, ServiceProcess] = {}
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("ServiceRegistry initialized")
    
    def register_service(self, definition: ServiceDefinition):
        """Register a service definition"""
        self.services[definition.name] = ServiceProcess(definition=definition)
        logger.info(f"Registered service: {definition.name}")
    
    async def start_service(
        self,
        service_name: str,
        extra_args: Optional[Dict[str, Any]] = None,
        auto_health_check: bool = True
    ) -> ServiceProcess:
        """
        Start a service (blocking until health check passes or timeout)
        
        Args:
            service_name: Service name
            extra_args: Service-specific arguments
            auto_health_check: Wait for health check to pass
        
        Returns:
            ServiceProcess with running process
        
        Raises:
            ValueError: Service not found or already running
            TimeoutError: Service failed to start within timeout
        """
        if service_name not in self.services:
            raise ValueError(f"Service not registered: {service_name}")
        
        service = self.services[service_name]
        
        # Check if already running
        if service.status in [ServiceStatus.RUNNING, ServiceStatus.STARTING]:
            raise ValueError(f"Service already running: {service_name}")
        
        # Handle dependencies
        for dep in service.definition.dependencies:
            if self.services[dep].status != ServiceStatus.RUNNING:
                logger.info(f"Starting dependency: {dep}")
                await self.start_service(dep, extra_args=None, auto_health_check=True)
        
        # Build command
        cmd = service.definition.get_command(extra_args)
        logger.info(f"🚀 Starting {service_name}: {' '.join(cmd)}")
        
        # Update state
        service.status = ServiceStatus.STARTING
        service.error = None
        
        try:
            # Spawn process
            service.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            service.started_at = datetime.now()
            logger.info(f"✅ Process spawned for {service_name} (PID: {service.pid})")
            
            # Wait for health check if applicable
            if auto_health_check and service.definition.health_url:
                if await self._wait_for_health(service):
                    service.status = ServiceStatus.RUNNING
                    service.restart_count = 0
                    logger.info(f"🟢 {service_name} is healthy")
                    return service
                else:
                    # Health check failed
                    raise TimeoutError(f"Health check failed for {service_name}")
            else:
                # No health check, assume running
                service.status = ServiceStatus.RUNNING
                service.restart_count = 0
                return service
        
        except Exception as e:
            service.status = ServiceStatus.ERROR
            service.error = str(e)
            logger.error(f"❌ Failed to start {service_name}: {e}")
            
            # Clean up process
            if service.process:
                try:
                    service.process.terminate()
                    service.process.wait(timeout=5)
                except:
                    service.process.kill()
            
            raise
    
    async def stop_service(self, service_name: str, timeout: float = 5.0):
        """
        Stop a service gracefully
        
        Args:
            service_name: Service name
            timeout: Seconds to wait before forcing kill
        
        Raises:
            ValueError: Service not found
        """
        if service_name not in self.services:
            raise ValueError(f"Service not registered: {service_name}")
        
        service = self.services[service_name]
        
        if service.status == ServiceStatus.STOPPED:
            logger.info(f"{service_name} is already stopped")
            return
        
        logger.info(f"🛑 Stopping {service_name}...")
        service.status = ServiceStatus.STOPPING
        
        if service.process:
            try:
                # Graceful shutdown
                service.process.terminate()
                try:
                    service.process.wait(timeout=timeout)
                    logger.info(f"✅ {service_name} terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if timeout
                    logger.warning(f"⚠️  Force-killing {service_name}")
                    service.process.kill()
                    service.process.wait()
            except Exception as e:
                logger.error(f"Error stopping {service_name}: {e}")
        
        service.status = ServiceStatus.STOPPED
        service.process = None
    
    async def _wait_for_health(self, service: ServiceProcess) -> bool:
        """
        Wait for service health check to pass
        
        Args:
            service: Service to check
        
        Returns:
            True if healthy, False if timeout
        """
        if not service.definition.health_url:
            return True
        
        start_time = time.time()
        timeout = service.definition.startup_timeout
        
        while time.time() - start_time < timeout:
            try:
                response = await self.http_client.get(service.definition.health_url)
                if response.status_code == 200:
                    logger.debug(f"✅ Health check passed for {service.definition.name}")
                    return True
            except Exception as e:
                logger.debug(f"Health check pending for {service.definition.name}: {e}")
            
            await asyncio.sleep(0.5)  # Poll every 500ms
        
        logger.error(f"❌ Health check timeout for {service.definition.name}")
        return False
    
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get current service status including health
        
        Args:
            service_name: Service name
        
        Returns:
            Status dict
        """
        if service_name not in self.services:
            raise ValueError(f"Service not registered: {service_name}")
        
        service = self.services[service_name]
        status_dict = service.to_dict()
        
        # Try to get health status
        if service.definition.health_url and service.status == ServiceStatus.RUNNING:
            try:
                response = await self.http_client.get(service.definition.health_url)
                status_dict['health'] = 'healthy' if response.status_code == 200 else 'unhealthy'
            except Exception as e:
                status_dict['health'] = 'unreachable'
        
        return status_dict
    
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        return {
            name: service.to_dict()
            for name, service in self.services.items()
        }
    
    async def start_all_services(self, extra_args: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """
        Start all services in dependency order
        
        Args:
            extra_args: Arguments to pass to all services
        
        Returns:
            Dict of service_name -> success
        """
        results = {}
        
        for service_name in self.services:
            try:
                await self.start_service(service_name, extra_args=extra_args)
                results[service_name] = True
                logger.info(f"✅ Started: {service_name}")
            except Exception as e:
                results[service_name] = False
                logger.error(f"❌ Failed to start {service_name}: {e}")
        
        return results
    
    async def stop_all_services(self) -> Dict[str, bool]:
        """
        Stop all services in reverse dependency order
        
        Returns:
            Dict of service_name -> success
        """
        results = {}
        
        # Stop in reverse order (respecting dependencies)
        services_to_stop = list(reversed(self.services.keys()))
        
        for service_name in services_to_stop:
            try:
                await self.stop_service(service_name)
                results[service_name] = True
                logger.info(f"✅ Stopped: {service_name}")
            except Exception as e:
                results[service_name] = False
                logger.error(f"❌ Failed to stop {service_name}: {e}")
        
        return results
    
    async def restart_service(self, service_name: str, extra_args: Optional[Dict[str, Any]] = None):
        """Restart a service"""
        await self.stop_service(service_name)
        await asyncio.sleep(1)  # Brief delay before restarting
        return await self.start_service(service_name, extra_args=extra_args)
    
    async def close(self):
        """Clean up resources"""
        await self.stop_all_services()
        await self.http_client.aclose()
        logger.info("ServiceRegistry closed")
