"""
Simulator Control API Endpoints
===============================
Control the world vehicle simulator from the fleet management UI
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import subprocess
import threading
import logging
import time
import os
import signal

logger = logging.getLogger(__name__)
router = APIRouter()

class SimulatorConfig(BaseModel):
    tick: float = 1.0
    seconds: int = 300  # 5 minutes default
    debug: bool = False
    no_gps: bool = False

class SimulatorStatus(BaseModel):
    running: bool
    start_time: Optional[float] = None
    config: Optional[SimulatorConfig] = None
    process_id: Optional[int] = None

# Global simulator state
simulator_state = {
    "process": None,
    "start_time": None,
    "config": None,
    "running": False
}

@router.get("/status", response_model=SimulatorStatus)
async def get_simulator_status():
    """Get current simulator status"""
    return SimulatorStatus(
        running=simulator_state["running"],
        start_time=simulator_state["start_time"],
        config=simulator_state["config"],
        process_id=simulator_state["process"].pid if simulator_state["process"] else None
    )

@router.post("/start")
async def start_simulator(
    background_tasks: BackgroundTasks,
    config: SimulatorConfig
):
    """Start the world vehicle simulator"""
    if simulator_state["running"]:
        raise HTTPException(status_code=400, detail="Simulator is already running")
    
    try:
        # Build command arguments
        cmd = ["python", "world_vehicles_simulator.py"]
        cmd.extend(["--tick", str(config.tick)])
        cmd.extend(["--seconds", str(config.seconds)])
        
        if config.debug:
            cmd.append("--debug")
        if config.no_gps:
            cmd.append("--no-gps")
        
        logger.info(f"Starting simulator with command: {' '.join(cmd)}")
        
        # Start simulator process
        process = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Update state
        simulator_state["process"] = process
        simulator_state["start_time"] = time.time()
        simulator_state["config"] = config
        simulator_state["running"] = True
        
        # Monitor process in background
        background_tasks.add_task(monitor_simulator_process, process)
        
        return {
            "status": "started",
            "process_id": process.pid,
            "message": f"Simulator started for {config.seconds} seconds"
        }
        
    except Exception as e:
        logger.error(f"Failed to start simulator: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start simulator: {str(e)}")

@router.post("/stop")
async def stop_simulator():
    """Stop the world vehicle simulator"""
    if not simulator_state["running"]:
        raise HTTPException(status_code=400, detail="Simulator is not running")
    
    try:
        process = simulator_state["process"]
        if process and process.poll() is None:
            # Terminate the process gracefully
            process.terminate()
            
            # Wait a bit for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                process.kill()
                process.wait()
        
        # Reset state
        simulator_state["process"] = None
        simulator_state["start_time"] = None
        simulator_state["config"] = None
        simulator_state["running"] = False
        
        return {
            "status": "stopped",
            "message": "Simulator stopped successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to stop simulator: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop simulator: {str(e)}")

async def monitor_simulator_process(process):
    """Monitor the simulator process and update state when it finishes"""
    try:
        # Wait for process to complete
        stdout, stderr = process.communicate()
        
        logger.info(f"Simulator process finished with return code: {process.returncode}")
        if stdout:
            logger.info(f"Simulator stdout: {stdout}")
        if stderr:
            logger.error(f"Simulator stderr: {stderr}")
            
    except Exception as e:
        logger.error(f"Error monitoring simulator process: {e}")
    finally:
        # Reset state when process finishes
        simulator_state["process"] = None
        simulator_state["start_time"] = None
        simulator_state["config"] = None
        simulator_state["running"] = False
