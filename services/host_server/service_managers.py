"""
Concrete Service Managers
=========================

Specific implementations of BaseServiceManager for each service:
- SimulatorServiceManager
- GPSCentComServiceManager
- CommuterServiceManager
- GeospatialServiceManager
"""

import sys
import asyncio
import logging
import httpx
from pathlib import Path
from typing import List, Optional
from .base_service_manager import BaseServiceManager
from .config import config

logger = logging.getLogger(__name__)


class SimulatorServiceManager(BaseServiceManager):
    """Manages the transit simulator service"""
    
    def build_command(
        self,
        api_port: Optional[int] = None,
        sim_time: Optional[str] = None,
        enable_boarding_after: Optional[float] = None,
        data_api_url: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """Build simulator startup command"""
        cmd = [
            sys.executable,
            "-m",
            config.simulator_module,
            "--mode", "depot"
        ]
        
        # API port
        cmd.extend(["--api-port", str(api_port or config.simulator_api_port)])
        
        # Fleet data API URL (use provided or fall back to Strapi from config)
        api_url = data_api_url or config.strapi_url
        cmd.extend(["--api-url", api_url])
        
        # Optional parameters
        if sim_time:
            cmd.extend(["--sim-time", sim_time])
        
        if enable_boarding_after:
            cmd.extend(["--enable-boarding-after", str(enable_boarding_after)])
        
        return cmd
    
    async def _wait_for_startup(self) -> bool:
        """Wait for simulator API to be listening"""
        if not self.process:
            return False
        
        # Try to connect to health endpoint with retries
        max_retries = 10
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"http://localhost:{config.simulator_api_port}/health")
                    if response.status_code == 200:
                        logger.info("Simulator API is responding")
                        return True
            except (httpx.ConnectError, httpx.TimeoutException, Exception):
                pass
            
            # Check if process crashed
            if self.process.returncode is not None:
                logger.error(f"Simulator process exited with code {self.process.returncode}")
                return False
            
            await asyncio.sleep(0.5)
        
        logger.error("Simulator API failed to start within timeout")
        return False


class GPSCentComServiceManager(BaseServiceManager):
    """Manages the GPSCentCom service"""
    
    def build_command(self, **kwargs) -> List[str]:
        """Build GPSCentCom startup command"""
        cmd = [
            sys.executable,
            str(config.project_root / "gpscentcom_server" / "server_main.py"),
            "--config", str(config.project_root / "gpscentcom_server" / ".config")
        ]
        return cmd
    
    async def _wait_for_startup(self) -> bool:
        """Wait for GPSCentCom API to be listening"""
        if not self.process:
            return False
        
        max_retries = 10
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"http://localhost:{config.gps_server_port}/health")
                    if response.status_code == 200:
                        logger.info("GPSCentCom API is responding")
                        return True
            except (httpx.ConnectError, httpx.TimeoutException, Exception):
                pass
            
            if self.process.returncode is not None:
                logger.error(f"GPSCentCom process exited with code {self.process.returncode}")
                return False
            
            await asyncio.sleep(0.5)
        
        logger.error("GPSCentCom API failed to start within timeout")
        return False


class CommuterServiceManager(BaseServiceManager):
    """Manages the Commuter Service"""
    
    def build_command(self, **kwargs) -> List[str]:
        """Build Commuter Service startup command"""
        cmd = [
            sys.executable,
            "-m",
            "commuter_service.main"
        ]
        return cmd
    
    async def _wait_for_startup(self) -> bool:
        """Wait for Commuter Service API to be listening"""
        if not self.process:
            return False
        
        max_retries = 10
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"http://localhost:{config.commuter_service_port}/health")
                    if response.status_code == 200:
                        logger.info("Commuter Service API is responding")
                        return True
            except (httpx.ConnectError, httpx.TimeoutException, Exception):
                pass
            
            if self.process.returncode is not None:
                logger.error(f"Commuter Service process exited with code {self.process.returncode}")
                return False
            
            await asyncio.sleep(0.5)
        
        logger.error("Commuter Service API failed to start within timeout")
        return False


class GeospatialServiceManager(BaseServiceManager):
    """Manages the Geospatial Service"""
    
    def build_command(self, **kwargs) -> List[str]:
        """Build Geospatial Service startup command"""
        cmd = [
            sys.executable,
            "-m",
            "geospatial_service"
        ]
        return cmd
    
    async def _wait_for_startup(self) -> bool:
        """Wait for Geospatial Service API to be listening"""
        if not self.process:
            return False
        
        # Geospatial service takes longer to initialize (PostGIS connection pool + stats)
        # Use 20 retries × 0.5s = 10 seconds for startup verification
        max_retries = 20
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get("http://localhost:6001/health")
                    if response.status_code == 200:
                        logger.info("Geospatial Service API is responding")
                        return True
            except (httpx.ConnectError, httpx.TimeoutException, Exception):
                pass
            
            if self.process.returncode is not None:
                # Process exited - try to capture stderr
                try:
                    stdout_data, stderr_data = await asyncio.wait_for(
                        self.process.communicate(),
                        timeout=2.0
                    )
                    error_output = stderr_data.decode('utf-8', errors='ignore') if stderr_data else stdout_data.decode('utf-8', errors='ignore')
                except:
                    error_output = ""
                
                error_msg = error_output.strip() if error_output else f"Process exited with code {self.process.returncode}"
                logger.error(f"Geospatial Service process exited with code {self.process.returncode}")
                logger.error(f"Error output: {error_msg}")
                self.error_message = error_msg
                return False
            
            await asyncio.sleep(0.5)
        
        logger.error("Geospatial Service API failed to start within timeout")
        return False
