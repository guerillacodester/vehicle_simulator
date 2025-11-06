"""
Base Service Manager
====================

Abstract base class for managing long-running services as subprocesses.
Provides common lifecycle management: start, stop, restart, monitor, health checks.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service status enum"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class BaseServiceManager(ABC):
    """
    Abstract base class for service managers.
    
    Subclasses must implement:
    - build_command(): Return command list to start the service
    - health_check(): Verify service is running correctly (optional, defaults to process check)
    """
    
    def __init__(
        self,
        service_name: str,
        project_root: Path,
        process_check_interval: float = 5.0,
        process_start_timeout: float = 30.0,
        process_stop_timeout: float = 10.0
    ):
        """
        Initialize service manager.
        
        Args:
            service_name: Name of service (e.g., "simulator", "gpscentcom")
            project_root: Root path of project
            process_check_interval: Interval to check process health (seconds)
            process_start_timeout: Timeout for process startup (seconds)
            process_stop_timeout: Timeout for process shutdown (seconds)
        """
        self.service_name = service_name
        self.project_root = project_root
        self.process: Optional[asyncio.subprocess.Process] = None
        self.status = ServiceStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self.process_check_interval = process_check_interval
        self.process_start_timeout = process_start_timeout
        self.process_stop_timeout = process_stop_timeout
    
    @abstractmethod
    def build_command(self, **kwargs) -> List[str]:
        """
        Build the command to start the service.
        
        Returns:
            List of command components suitable for subprocess.Popen
        """
        pass
    
    async def health_check(self) -> bool:
        """
        Perform health check on running service.
        Override in subclass for service-specific checks (HTTP endpoint, etc).
        
        Returns:
            True if service is healthy, False otherwise
        """
        # Default: just check if process is still running
        return self.process is not None and self.process.returncode is None
    
    async def start(self, **kwargs) -> Dict[str, Any]:
        """
        Start the service subprocess.
        
        Args:
            **kwargs: Service-specific arguments passed to build_command()
        
        Returns:
            Dict with success status, message, status, PID, etc.
        """
        if self.status in [ServiceStatus.RUNNING, ServiceStatus.STARTING]:
            return {
                "success": False,
                "message": f"{self.service_name} is already {self.status.value}",
                "status": self.status.value
            }
        
        try:
            logger.info(f"Starting {self.service_name}...")
            self.status = ServiceStatus.STARTING
            self.error_message = None
            
            # Build command
            cmd = self.build_command(**kwargs)
            logger.debug(f"Command: {' '.join(cmd)}")
            
            # Start subprocess with inherited environment
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root),
                env=os.environ.copy()
            )
            
            # Wait for startup
            try:
                await asyncio.wait_for(
                    self._wait_for_startup(),
                    timeout=self.process_start_timeout
                )
                
                self.status = ServiceStatus.RUNNING
                self.start_time = datetime.now()
                
                # Start monitoring task
                self._monitor_task = asyncio.create_task(self._monitor_process())
                
                logger.info(f"✅ {self.service_name} started (PID: {self.process.pid})")
                
                return {
                    "success": True,
                    "message": f"{self.service_name} started successfully",
                    "status": self.status.value,
                    "pid": self.process.pid,
                    "start_time": self.start_time.isoformat()
                }
                
            except asyncio.TimeoutError:
                logger.error(f"{self.service_name} startup timeout")
                await self.stop()
                self.status = ServiceStatus.ERROR
                self.error_message = "Startup timeout"
                
                return {
                    "success": False,
                    "message": f"{self.service_name} failed to start (timeout)",
                    "status": self.status.value,
                    "error": self.error_message
                }
        
        except Exception as e:
            logger.error(f"Failed to start {self.service_name}: {e}", exc_info=True)
            self.status = ServiceStatus.ERROR
            self.error_message = str(e)
            
            return {
                "success": False,
                "message": f"Failed to start {self.service_name}",
                "status": self.status.value,
                "error": str(e)
            }
    
    async def stop(self) -> Dict[str, Any]:
        """Stop the service subprocess."""
        if self.status == ServiceStatus.STOPPED:
            return {
                "success": True,
                "message": f"{self.service_name} is already stopped",
                "status": self.status.value
            }
        
        try:
            logger.info(f"Stopping {self.service_name}...")
            self.status = ServiceStatus.STOPPING
            
            # Cancel monitor task
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Terminate process
            if self.process:
                try:
                    if sys.platform == "win32":
                        # Windows: use taskkill with PID
                        subprocess_proc = await asyncio.create_subprocess_exec(
                            "taskkill", "/pid", str(self.process.pid), "/t", "/f",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await asyncio.wait_for(subprocess_proc.wait(), timeout=5.0)
                    else:
                        # Linux/Mac: SIGTERM then SIGKILL if needed
                        self.process.terminate()
                        try:
                            await asyncio.wait_for(self.process.wait(), timeout=self.process_stop_timeout)
                        except asyncio.TimeoutError:
                            self.process.kill()
                            await self.process.wait()
                except Exception as e:
                    logger.error(f"Error stopping {self.service_name}: {e}")
                
                self.process = None
            
            self.status = ServiceStatus.STOPPED
            self.start_time = None
            self._monitor_task = None
            
            logger.info(f"✅ {self.service_name} stopped")
            
            return {
                "success": True,
                "message": f"{self.service_name} stopped",
                "status": self.status.value
            }
        
        except Exception as e:
            logger.error(f"Unexpected error stopping {self.service_name}: {e}")
            self.status = ServiceStatus.ERROR
            self.error_message = str(e)
            
            return {
                "success": False,
                "message": f"Error stopping {self.service_name}",
                "status": self.status.value,
                "error": str(e)
            }
    
    async def restart(self, **kwargs) -> Dict[str, Any]:
        """Restart the service."""
        await self.stop()
        await asyncio.sleep(1)
        return await self.start(**kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status snapshot."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "service": self.service_name,
            "status": self.status.value,
            "pid": self.process.pid if self.process else None,
            "uptime_seconds": uptime,
            "error": self.error_message
        }
    
    async def _get_process_error(self) -> str:
        """Read stderr from process (non-blocking)"""
        if not self.process or not self.process.stderr:
            return ""
        try:
            # Try to read stderr without waiting
            stderr_data = await asyncio.wait_for(
                self.process.stderr.read(),
                timeout=1.0
            )
            return stderr_data.decode('utf-8', errors='ignore')
        except:
            return ""
    
    async def _wait_for_startup(self) -> bool:
        """
        Wait for service to start successfully.
        Override in subclass for service-specific startup verification.
        """
        if not self.process:
            return False
        
        # Wait a bit for process to initialize
        await asyncio.sleep(0.5)
        
        # Check if process is still running
        return self.process.returncode is None
    
    async def _monitor_process(self) -> None:
        """Monitor process health and detect crashes."""
        try:
            while True:
                if self.status == ServiceStatus.RUNNING and self.process:
                    # Check if process has exited
                    if self.process.returncode is not None:
                        logger.warning(f"{self.service_name} process died unexpectedly (exit code: {self.process.returncode})")
                        self.status = ServiceStatus.ERROR
                        self.error_message = f"Process exited with code {self.process.returncode}"
                        self.process = None
                        break
                    
                    # Run health check
                    try:
                        healthy = await self.health_check()
                        if not healthy:
                            logger.warning(f"{self.service_name} health check failed")
                            self.status = ServiceStatus.ERROR
                            self.error_message = "Health check failed"
                            break
                    except Exception as e:
                        logger.error(f"Error in {self.service_name} health check: {e}")
                
                await asyncio.sleep(self.process_check_interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error monitoring {self.service_name}: {e}")
