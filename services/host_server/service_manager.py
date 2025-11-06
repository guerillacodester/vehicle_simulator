"""
Generic Service Manager
========================

Base class for managing various service subprocesses (simulator, gpscentcom, commuter_service, geospatial).
Handles start, stop, restart, and health monitoring.
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from .config import config


logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service status enum"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ServiceConfig:
    """Configuration for a managed service"""
    def __init__(
        self,
        name: str,
        module: str,
        port: int,
        startup_wait: float = 10.0,
        args: Optional[List[str]] = None
    ):
        self.name = name
        self.module = module
        self.port = port
        self.startup_wait = startup_wait
        self.args = args or []


class ServiceManager:
    """Generic manager for service subprocesses"""
    
    def __init__(self, service_config: ServiceConfig):
        """Initialize service manager"""
        self.config = service_config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.status = ServiceStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start(self, *args: str) -> Dict[str, Any]:
        """
        Start the service subprocess
        
        Args:
            *args: Additional command line arguments
            
        Returns:
            Dict with success status and details
        """
        if self.status in [ServiceStatus.RUNNING, ServiceStatus.STARTING]:
            return {
                "success": False,
                "message": f"{self.config.name} is already {self.status.value}",
                "status": self.status.value
            }
        
        try:
            logger.info(f"Starting {self.config.name} subprocess...")
            self.status = ServiceStatus.STARTING
            self.error_message = None
            
            # Build command
            python_exe = sys.executable
            cmd = [python_exe, "-m", self.config.module]
            cmd.extend(self.config.args)
            cmd.extend(args)
            
            logger.info(f"Command: {' '.join(cmd)}")
            
            # Start subprocess
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(config.project_root)
            )
            
            # Wait briefly to check if process starts successfully
            try:
                await asyncio.wait_for(
                    self._wait_for_startup(),
                    timeout=self.config.startup_wait
                )
                
                self.status = ServiceStatus.RUNNING
                self.start_time = datetime.now()
                
                result = {
                    "success": True,
                    "message": f"{self.config.name} started successfully",
                    "status": self.status.value,
                    "pid": self.process.pid,
                    "port": self.config.port
                }
                
                logger.info(f"✅ {self.config.name} started (PID: {self.process.pid})")
                return result
                
            except asyncio.TimeoutError:
                self.status = ServiceStatus.ERROR
                self.error_message = f"Startup timeout after {self.config.startup_wait}s"
                
                # Process may still be running, kill it
                if self.process:
                    try:
                        self.process.terminate()
                        await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    except (asyncio.TimeoutError, ProcessLookupError):
                        self.process.kill()
                
                return {
                    "success": False,
                    "message": self.error_message,
                    "status": self.status.value
                }
                
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.error_message = str(e)
            logger.error(f"Failed to start {self.config.name}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to start {self.config.name}: {e}",
                "status": self.status.value
            }
    
    async def stop(self) -> Dict[str, Any]:
        """
        Stop the service subprocess
        
        Returns:
            Dict with success status and details
        """
        if self.status == ServiceStatus.STOPPED:
            return {
                "success": True,
                "message": f"{self.config.name} is already stopped",
                "status": self.status.value
            }
        
        if not self.process:
            self.status = ServiceStatus.STOPPED
            return {
                "success": True,
                "message": f"{self.config.name} stopped",
                "status": self.status.value
            }
        
        try:
            logger.info(f"Stopping {self.config.name} (PID: {self.process.pid})...")
            self.status = ServiceStatus.STOPPING
            
            # Graceful termination
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=config.process_stop_timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout stopping {self.config.name}, force killing...")
                self.process.kill()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.error(f"Failed to kill {self.config.name}")
            
            self.status = ServiceStatus.STOPPED
            self.start_time = None
            self.process = None
            
            logger.info(f"✅ {self.config.name} stopped")
            return {
                "success": True,
                "message": f"{self.config.name} stopped successfully",
                "status": self.status.value
            }
            
        except Exception as e:
            logger.error(f"Error stopping {self.config.name}: {e}", exc_info=True)
            self.status = ServiceStatus.ERROR
            self.error_message = str(e)
            return {
                "success": False,
                "message": f"Error stopping {self.config.name}: {e}",
                "status": self.status.value
            }
    
    async def restart(self, *args: str) -> Dict[str, Any]:
        """
        Restart the service
        
        Returns:
            Dict with success status and details
        """
        logger.info(f"Restarting {self.config.name}...")
        
        # Stop
        stop_result = await self.stop()
        if not stop_result["success"]:
            return stop_result
        
        # Brief delay
        await asyncio.sleep(1)
        
        # Start
        return await self.start(*args)
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "service": self.config.name,
            "status": self.status.value,
            "pid": self.process.pid if self.process else None,
            "port": self.config.port,
            "uptime": uptime,
            "error": self.error_message
        }
    
    async def _wait_for_startup(self):
        """Wait for service to be ready"""
        # Check if process is still running
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < self.config.startup_wait:
            if self.process.returncode is not None:
                # Process exited
                stderr = await self.process.stderr.read()
                raise RuntimeError(
                    f"Process exited with code {self.process.returncode}: "
                    f"{stderr.decode('utf-8', errors='ignore')}"
                )
            await asyncio.sleep(0.5)
