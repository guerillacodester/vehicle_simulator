"""
Base Service Manager
====================

Abstract base class for managing long-running services as subprocesses.
Provides common functionality for start/stop/restart/status operations.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
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
    """Abstract base class for service managers"""
    
    def __init__(self, service_name: str, process_check_interval: float = 5.0, process_start_timeout: float = 30.0, process_stop_timeout: float = 10.0):
        """
        Initialize service manager
        
        Args:
            service_name: Name of the service (e.g., "simulator", "gpscentcom")
            process_check_interval: Interval to check process health (seconds)
            process_start_timeout: Timeout for process startup (seconds)
            process_stop_timeout: Timeout for process shutdown (seconds)
        """
        self.service_name = service_name
        self.process: Optional[asyncio.subprocess.Process] = None
        self.status = ServiceStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self.process_check_interval = process_check_interval
        self.process_start_timeout = process_start_timeout
        self.process_stop_timeout = process_stop_timeout
        
    @abstractmethod
    async def start(self, **kwargs) -> Dict[str, Any]:
        """
        Start the service subprocess
        
        Returns:
            Dict with success status and details
        """
        pass
    
    async def stop(self) -> Dict[str, Any]:
        """Stop the service subprocess"""
        if self.status == ServiceStatus.STOPPED:
            return {
                "success": True,
                "message": f"{self.service_name} is already stopped",
                "status": self.status.value
            }
        
        try:
            logger.info(f"Stopping {self.service_name}...")
            self.status = ServiceStatus.STOPPING
            
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            
            if self.process:
                # Send SIGTERM (graceful shutdown)
                try:
                    if sys.platform == "win32":
                        # Windows: use taskkill
                        subprocess_proc = await asyncio.create_subprocess_exec(
                            "taskkill", "/pid", str(self.process.pid), "/t", "/f",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await asyncio.wait_for(subprocess_proc.wait(), timeout=5.0)
                    else:
                        # Linux/Mac: send SIGTERM then SIGKILL
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
                "message": f"Error stopping {self.service_name}: {str(e)}",
                "status": self.status.value,
                "error": str(e)
            }
    
    async def restart(self, **kwargs) -> Dict[str, Any]:
        """Restart the service"""
        await self.stop()
        await asyncio.sleep(1)
        return await self.start(**kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "name": self.service_name,
            "status": self.status.value,
            "pid": self.process.pid if self.process else None,
            "uptime": uptime,
            "error": self.error_message
        }
    
    async def _wait_for_startup(self) -> bool:
        """
        Wait for service to start successfully
        Override in subclass if health check is needed
        """
        if not self.process:
            return False
        
        try:
            # Simple check: process still running
            return self.process.returncode is None
        except Exception:
            return False
    
    async def _monitor_process(self) -> None:
        """Monitor process health and restart if needed"""
        try:
            while True:
                if self.status == ServiceStatus.RUNNING and self.process:
                    if self.process.returncode is not None:
                        logger.warning(f"{self.service_name} process died unexpectedly")
                        self.status = ServiceStatus.ERROR
                        self.error_message = "Process exited unexpectedly"
                        self.process = None
                
                await asyncio.sleep(self.process_check_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error monitoring {self.service_name}: {e}")
