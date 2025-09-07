"""
Simulator Control Services
=========================
Business logic for simulator control operations
"""

import asyncio
import subprocess
# import psutil  # Optional for system monitoring
import os
import signal
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .models import SimulationStatus, VehicleStatus, SimulationMetrics

logger = logging.getLogger(__name__)

class SimulatorService:
    """Service class for simulator control operations"""
    
    def __init__(self):
        self.simulation_process = None
        self.simulation_start_time = None
        self.simulation_config = {}
        self.metrics = SimulationMetrics()
        self.logs = []
        
        # Path to the world vehicles simulator
        self.simulator_path = Path("../world_vehicles_simulator.py")
        if not self.simulator_path.exists():
            # Try absolute path
            project_root = Path(__file__).parent.parent.parent
            self.simulator_path = project_root / "world_vehicles_simulator.py"
    
    def is_running(self) -> bool:
        """Check if simulation is currently running"""
        if self.simulation_process is None:
            return False
        
        try:
            # Check if process is still alive
            return self.simulation_process.poll() is None
        except:
            return False
    
    async def start_simulation(
        self, 
        country: Optional[str] = None,
        duration_seconds: int = 60,
        update_interval: float = 1.0,
        gps_enabled: bool = True
    ):
        """Start the vehicle simulation"""
        try:
            if self.is_running():
                raise Exception("Simulation is already running")
            
            # Build command
            cmd = ["python", str(self.simulator_path)]
            cmd.extend(["--seconds", str(duration_seconds)])
            cmd.extend(["--tick", str(update_interval)])
            
            if not gps_enabled:
                cmd.append("--no-gps")
            
            # Note: Country filtering not supported by simulator yet
            if country:
                logger.info(f"ℹ️ Country filtering ({country}) requested but not yet supported by simulator")
            
            logger.info(f"🚀 Starting simulation with command: {' '.join(cmd)}")
            
            # Get the directory containing the simulator script
            working_dir = self.simulator_path.parent
            
            # Start the simulation process
            self.simulation_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(working_dir)
            )
            
            self.simulation_start_time = datetime.now()
            self.simulation_config = {
                "country": country,
                "duration_seconds": duration_seconds,
                "update_interval": update_interval,
                "gps_enabled": gps_enabled
            }
            
            # Reset metrics
            self.metrics = SimulationMetrics()
            
            logger.info(f"✅ Simulation started with PID: {self.simulation_process.pid}")
            
        except Exception as e:
            logger.error(f"❌ Error starting simulation: {str(e)}")
            raise e
    
    async def stop_simulation(self):
        """Stop the currently running simulation"""
        try:
            if not self.is_running():
                raise Exception("No simulation is currently running")
            
            logger.info(f"🛑 Stopping simulation PID: {self.simulation_process.pid}")
            
            # Try graceful shutdown first
            self.simulation_process.terminate()
            
            # Wait up to 5 seconds for graceful shutdown
            try:
                self.simulation_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("⚠️ Graceful shutdown failed, force killing process")
                self.simulation_process.kill()
                self.simulation_process.wait()
            
            self.simulation_process = None
            logger.info("✅ Simulation stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping simulation: {str(e)}")
            raise e
    
    async def get_status(self) -> SimulationStatus:
        """Get current simulation status"""
        try:
            is_running = self.is_running()
            
            if is_running and self.simulation_start_time:
                elapsed = (datetime.now() - self.simulation_start_time).total_seconds()
                
                return SimulationStatus(
                    is_running=True,
                    country=self.simulation_config.get("country"),
                    start_time=self.simulation_start_time,
                    duration_seconds=self.simulation_config.get("duration_seconds"),
                    elapsed_seconds=elapsed,
                    update_interval=self.simulation_config.get("update_interval"),
                    gps_enabled=self.simulation_config.get("gps_enabled", True),
                    active_vehicles=await self._count_active_vehicles(),
                    message="Simulation running"
                )
            else:
                return SimulationStatus(
                    is_running=False,
                    message="No simulation running"
                )
                
        except Exception as e:
            logger.error(f"❌ Error getting status: {str(e)}")
            return SimulationStatus(
                is_running=False,
                message=f"Error getting status: {str(e)}"
            )
    
    async def get_active_vehicles(self) -> List[VehicleStatus]:
        """Get list of currently active vehicles"""
        try:
            # This is a placeholder - in a real implementation, this would
            # connect to the database or simulation state to get vehicle info
            vehicles = []
            
            if self.is_running():
                # Mock some vehicle data for demonstration
                mock_vehicles = [
                    {
                        "vehicle_id": "BUS001",
                        "route_name": "Downtown Express",
                        "location": {"lat": 13.2810, "lon": -59.6463},
                        "speed": 45.2
                    },
                    {
                        "vehicle_id": "BUS002", 
                        "route_name": "North-South Line",
                        "location": {"lat": 13.2805, "lon": -59.6455},
                        "speed": 28.1
                    },
                    {
                        "vehicle_id": "BUS003",
                        "route_name": "East-West Connector", 
                        "location": {"lat": 13.2815, "lon": -59.6470},
                        "speed": 32.5
                    },
                    {
                        "vehicle_id": "ZR1001",
                        "route_name": "Downtown Express",
                        "location": {"lat": 13.2808, "lon": -59.6461},
                        "speed": 41.8
                    }
                ]
                
                for vehicle in mock_vehicles:
                    vehicles.append(VehicleStatus(
                        vehicle_id=vehicle["vehicle_id"],
                        is_active=True,
                        route_name=vehicle["route_name"],
                        current_location=vehicle["location"],
                        speed_kmh=vehicle["speed"],
                        last_update=datetime.now(),
                        gps_enabled=self.simulation_config.get("gps_enabled", True),
                        country=self.simulation_config.get("country", "barbados")
                    ))
            
            return vehicles
            
        except Exception as e:
            logger.error(f"❌ Error getting active vehicles: {str(e)}")
            return []
    
    async def get_vehicle_details(self, vehicle_id: str) -> Optional[Dict]:
        """Get detailed information about a specific vehicle"""
        try:
            vehicles = await self.get_active_vehicles()
            for vehicle in vehicles:
                if vehicle.vehicle_id == vehicle_id:
                    return vehicle.dict()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting vehicle details: {str(e)}")
            return None
    
    async def activate_vehicle(self, vehicle_id: str) -> Dict:
        """Activate a specific vehicle (placeholder)"""
        # TODO: Implement actual vehicle activation logic
        logger.info(f"✅ Vehicle {vehicle_id} activated")
        return {"vehicle_id": vehicle_id, "status": "activated", "timestamp": datetime.now()}
    
    async def deactivate_vehicle(self, vehicle_id: str) -> Dict:
        """Deactivate a specific vehicle (placeholder)"""
        # TODO: Implement actual vehicle deactivation logic
        logger.info(f"⏹️ Vehicle {vehicle_id} deactivated")
        return {"vehicle_id": vehicle_id, "status": "deactivated", "timestamp": datetime.now()}
    
    async def get_logs(self, lines: int = 100) -> List[str]:
        """Get recent simulation logs"""
        try:
            log_lines = []
            
            if self.simulation_process and self.simulation_process.stdout:
                # Read available output without blocking
                try:
                    # This is a simplified version - in production you'd want
                    # to properly handle log streaming
                    output = self.simulation_process.stdout.read()
                    if output:
                        log_lines = output.strip().split('\n')[-lines:]
                except:
                    pass
            
            # Add some recent internal logs
            recent_logs = [
                f"{datetime.now().isoformat()}: Simulation API active",
                f"{datetime.now().isoformat()}: Monitoring {await self._count_active_vehicles()} vehicles"
            ]
            
            return recent_logs + log_lines
            
        except Exception as e:
            logger.error(f"❌ Error getting logs: {str(e)}")
            return [f"Error getting logs: {str(e)}"]
    
    async def get_metrics(self) -> SimulationMetrics:
        """Get simulation performance metrics"""
        try:
            if self.is_running() and self.simulation_start_time:
                uptime = (datetime.now() - self.simulation_start_time).total_seconds()
                
                # Get system metrics
                try:
                    # process = psutil.Process(self.simulation_process.pid)
                    # memory_mb = process.memory_info().rss / 1024 / 1024
                    # cpu_percent = process.cpu_percent()
                    memory_mb = 0.0  # Placeholder
                    cpu_percent = 0.0  # Placeholder
                except:
                    memory_mb = 0.0
                    cpu_percent = 0.0
                
                self.metrics.uptime_seconds = uptime
                self.metrics.memory_usage_mb = memory_mb
                self.metrics.cpu_usage_percent = cpu_percent
                self.metrics.active_vehicles = await self._count_active_vehicles()
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"❌ Error getting metrics: {str(e)}")
            return SimulationMetrics()
    
    async def _count_active_vehicles(self) -> int:
        """Count currently active vehicles"""
        try:
            vehicles = await self.get_active_vehicles()
            return len([v for v in vehicles if v.is_active])
        except:
            return 0
