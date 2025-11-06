"""
Simulator Process Manager
==========================

Manages the transit simulator as a subprocess.
Handles start, stop, restart, and health monitoring.
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path
from typing import Optional, Dict, Any
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


class SimulatorManager:
    """Manages the transit simulator subprocess"""
    
    def __init__(self):
        """Initialize simulator manager"""
        self.process: Optional[asyncio.subprocess.Process] = None
        self.status = ServiceStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start(
        self,
        api_port: Optional[int] = None,
        sim_time: Optional[str] = None,
        enable_boarding_after: Optional[float] = None,
        data_api_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start the simulator subprocess
        
        Args:
            api_port: Override API port (default from config)
            sim_time: Simulation time (ISO or HH:MM)
            enable_boarding_after: Auto-enable boarding delay
            data_api_url: URL to fleet data API (vehicles/drivers/routes). Default: http://localhost:1337
            
        Returns:
            Dict with success status and details
        """
        if self.status in [ServiceStatus.RUNNING, ServiceStatus.STARTING]:
            return {
                "success": False,
                "message": f"Simulator is already {self.status.value}",
                "status": self.status.value
            }
        
        try:
            logger.info("Starting simulator subprocess...")
            self.status = ServiceStatus.STARTING
            self.error_message = None
            
            # Build command
            python_exe = sys.executable
            cmd = [
                python_exe,
                "-m",
                config.simulator_module,
                "--mode", "depot"
            ]
            
            # Add optional arguments
            if api_port:
                cmd.extend(["--api-port", str(api_port)])
            else:
                cmd.extend(["--api-port", str(config.simulator_api_port)])
            
            # Add data API URL (fleet data source)
            # Use provided URL or fall back to Strapi from config
            api_url = data_api_url or config.strapi_url
            cmd.extend(["--api-url", api_url])
            logger.info(f"Using fleet data API: {api_url}")
            
            if sim_time:
                cmd.extend(["--sim-time", sim_time])
            
            if enable_boarding_after:
                cmd.extend(["--enable-boarding-after", str(enable_boarding_after)])
            
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
                    timeout=config.process_start_timeout
                )
                
                self.status = ServiceStatus.RUNNING
                self.start_time = datetime.now()
                
                # Start monitoring task
                self._monitor_task = asyncio.create_task(self._monitor_process())
                
                logger.info(f"✅ Simulator started successfully (PID: {self.process.pid})")
                
                return {
                    "success": True,
                    "message": "Simulator started successfully",
                    "status": self.status.value,
                    "pid": self.process.pid,
                    "start_time": self.start_time.isoformat(),
                    "api_url": f"http://localhost:{api_port or config.simulator_api_port}"
                }
                
            except asyncio.TimeoutError:
                logger.error("Simulator startup timeout")
                await self.stop()
                self.status = ServiceStatus.ERROR
                self.error_message = "Startup timeout"
                
                return {
                    "success": False,
                    "message": "Simulator failed to start (timeout)",
                    "status": self.status.value,
                    "error": self.error_message
                }
                
        except Exception as e:
            logger.error(f"Failed to start simulator: {e}", exc_info=True)
            self.status = ServiceStatus.ERROR
            self.error_message = str(e)
            
            return {
                "success": False,
                "message": f"Failed to start simulator: {e}",
                "status": self.status.value,
                "error": self.error_message
            }
    
    async def stop(self) -> Dict[str, Any]:
        """
        Stop the simulator subprocess
        
        Returns:
            Dict with success status
        """
        if self.status == ServiceStatus.STOPPED:
            return {
                "success": False,
                "message": "Simulator is already stopped",
                "status": self.status.value
            }
        
        try:
            logger.info("Stopping simulator...")
            self.status = ServiceStatus.STOPPING
            
            # Cancel monitor task
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None
            
            if self.process:
                # Send SIGTERM (graceful shutdown)
                try:
                    self.process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        await asyncio.wait_for(
                            self.process.wait(),
                            timeout=config.process_stop_timeout
                        )
                    except asyncio.TimeoutError:
                        # Force kill if timeout
                        logger.warning("Graceful shutdown timeout, forcing kill...")
                        self.process.kill()
                        await self.process.wait()
                    
                except ProcessLookupError:
                    # Process already dead
                    pass
                
                self.process = None
            
            self.status = ServiceStatus.STOPPED
            self.start_time = None
            
            logger.info("✅ Simulator stopped")
            
            return {
                "success": True,
                "message": "Simulator stopped successfully",
                "status": self.status.value
            }
            
        except Exception as e:
            logger.error(f"Error stopping simulator: {e}", exc_info=True)
            self.status = ServiceStatus.ERROR
            self.error_message = str(e)
            
            return {
                "success": False,
                "message": f"Error stopping simulator: {e}",
                "status": self.status.value,
                "error": self.error_message
            }
    
    async def restart(self, **kwargs) -> Dict[str, Any]:
        """
        Restart the simulator
        
        Args:
            **kwargs: Arguments passed to start()
            
        Returns:
            Dict with success status
        """
        logger.info("Restarting simulator...")
        
        # Stop if running
        if self.status != ServiceStatus.STOPPED:
            stop_result = await self.stop()
            if not stop_result["success"]:
                return stop_result
        
        # Wait briefly before restart
        await asyncio.sleep(2)
        
        # Start again
        return await self.start(**kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status
        
        Returns:
            Dict with status details
        """
        uptime = None
        if self.start_time and self.status == ServiceStatus.RUNNING:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "status": self.status.value,
            "pid": self.process.pid if self.process else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": uptime,
            "error": self.error_message,
            "api_url": f"http://localhost:{config.simulator_api_port}" if self.status == ServiceStatus.RUNNING else None
        }
    
    async def _wait_for_startup(self):
        """Wait for simulator to start (checks if process is alive)"""
        for _ in range(10):  # Check 10 times over ~5 seconds
            if self.process.returncode is not None:
                # Process died during startup
                stdout, stderr = await self.process.communicate()
                error_msg = stderr.decode() if stderr else stdout.decode()
                raise RuntimeError(f"Simulator process died during startup: {error_msg}")
            
            await asyncio.sleep(0.5)
    
    async def _monitor_process(self):
        """Monitor subprocess and update status if it dies"""
        try:
            while True:
                if self.process:
                    returncode = self.process.returncode
                    if returncode is not None:
                        # Process died unexpectedly
                        logger.error(f"Simulator process died unexpectedly (exit code: {returncode})")
                        
                        # Read stdout/stderr for error details
                        try:
                            stdout, stderr = await asyncio.wait_for(
                                self.process.communicate(),
                                timeout=1.0
                            )
                            error_output = stderr.decode() if stderr else stdout.decode()
                            logger.error(f"Process output: {error_output[-500:]}")  # Last 500 chars
                        except:
                            pass
                        
                        self.status = ServiceStatus.ERROR
                        self.error_message = f"Process died with exit code {returncode}"
                        break
                
                await asyncio.sleep(config.process_check_interval)
                
        except asyncio.CancelledError:
            # Monitor task cancelled (normal during shutdown)
            pass
        except Exception as e:
            logger.error(f"Error in process monitor: {e}", exc_info=True)


# Global manager instance
simulator_manager = SimulatorManager()
