#!/usr/bin/env python3
"""
VehiclesDepot
---------------
Responsible for instantiating and managing Navigator, GPSDevice, and EngineBlock
for all vehicles defined in vehicles.json.
"""

import json
import os
import sys
import time
import configparser
import logging
from datetime import datetime
from typing import Optional

# Note: TimetableManager removed - was part of old coupled system
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.engine.engine_block import Engine
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle_simulator.vehicle.engine.sim_speed_model import load_speed_model
# FleetDispatcher removed - plugin architecture handles telemetry processing
from world.vehicle_simulator.vehicle.gps_device.rxtx_buffer import RxTxBuffer
# Navigator (manages its own TelemetryBuffer internally)
from world.vehicle_simulator.vehicle.driver.navigation.navigator import Navigator
from world.vehicle_simulator.vehicle.vahicle_object import VehicleState

# Create logger for this module
logger = logging.getLogger(__name__)

class VehiclesDepot:
    def __init__(self, manifest_path: str = "world/vehicle_simulator/config/vehicles.json", 
                 tick_time: float = 0.1, 
                 timetable_path: Optional[str] = None,
                 route_provider=None):
        # Initialize basic properties
        self.manifest_path = manifest_path
        self.tick_time = tick_time
        self.vehicles = {}
        self.route_provider = route_provider
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Load configurations
        self._load_manifest()
        self._load_config()
        
        # Initialize timetable
        # Note: TimetableManager removed - standalone mode doesn't need complex timetabling
        self.timetable_manager = None  # Simplified timetable management
        if timetable_path and os.path.exists(timetable_path):
            # Note: Timetable loading simplified for standalone mode
            self.logger.debug(f"Timetable file found: {timetable_path} (simplified loading)")

    # -------------------- manifest --------------------

    def _resolve_manifest_path(self):
        """Resolve the manifest path from various potential locations."""
        from pathlib import Path
        
        # Convert to Path object for easier manipulation
        manifest_path = Path(self.manifest_path)
        
        # Strategy 1: Try the original path as-is
        if manifest_path.exists():
            self.logger.debug(f"Found manifest at original path: {manifest_path}")
            return str(manifest_path)
        
        # Strategy 2: Try relative to current working directory
        cwd_path = Path.cwd() / manifest_path
        if cwd_path.exists():
            self.logger.debug(f"Found manifest relative to CWD: {cwd_path}")
            return str(cwd_path)
        
        # Strategy 3: Try going up directories to find the manifest
        current_dir = Path.cwd()
        for _ in range(3):  # Look up to 3 levels up
            candidate = current_dir / manifest_path.name  # Just the filename
            if candidate.exists():
                self.logger.debug(f"Found manifest going up directories: {candidate}")
                return str(candidate)
            
            # Also try the full relative path from each parent
            candidate = current_dir / manifest_path
            if candidate.exists():
                self.logger.debug(f"Found manifest with full path from parent: {candidate}")
                return str(candidate)
            
            current_dir = current_dir.parent
        
        # Strategy 4: Try from the project root (look for world/vehicle_simulator/config/vehicles.json pattern)
        current_dir = Path.cwd()
        while current_dir.parent != current_dir:  # Until we reach the root
            candidate = current_dir / "world" / "vehicle_simulator" / "config" / "vehicles.json"
            if candidate.exists():
                self.logger.debug(f"Found manifest in vehicle_simulator config directory: {candidate}")
                return str(candidate)
            current_dir = current_dir.parent
        
        self.logger.error(f"Could not resolve manifest path: {self.manifest_path}")
        return None

    def _load_manifest(self):
        # Resolve manifest path similar to route resolution
        manifest_path = self._resolve_manifest_path()
        if not manifest_path or not os.path.exists(manifest_path):
            sys.exit(f"[ERROR] vehicles manifest not found: {self.manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict) or not data:
            sys.exit(f"[ERROR] vehicles manifest must be a non-empty JSON object")

        # Initialize vehicles dictionary
        self.vehicles = {}
        
        # Process individual vehicle configurations (like ZR1001)
        for key, value in data.items():
            if key != "vehicles" and isinstance(value, dict):
                self.vehicles[key] = value
        
        # Process vehicles array if it exists
        if "vehicles" in data and isinstance(data["vehicles"], list):
            for vehicle in data["vehicles"]:
                if isinstance(vehicle, dict) and "id" in vehicle:
                    # Convert array format to configuration format
                    vehicle_id = vehicle["id"]
                    self.vehicles[vehicle_id] = {
                        "active": vehicle.get("status") == "active",
                        "route": vehicle.get("route_id", ""),
                        "speed_model": vehicle.get("speed_model", "kinematic"),
                        "speed": vehicle.get("speed", 60),
                        "accel_limit": vehicle.get("accel_limit", 3),
                        "decel_limit": vehicle.get("decel_limit", 4),
                        "corner_slowdown": vehicle.get("corner_slowdown", 1),
                        "release_ticks": vehicle.get("release_ticks", 3),
                        "initial_position": vehicle.get("position", {}),
                        "heading": vehicle.get("heading", 0),
                        "capacity": vehicle.get("capacity", 40),
                        "passengers": vehicle.get("passengers", 0)
                    }

    # -------------------- config --------------------

    def _load_config(self):
        """
        Load server URL and optional auth token from config.ini (project root).
        Normalize ws_url to avoid DNS errors (strip, rstrip('/'), http->ws, https->wss).
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cfg_path = os.path.join(project_root, "config.ini")

        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)

        raw_ws = cfg.get("server", "ws_url", fallback="ws://localhost:5000")
        ws = raw_ws.strip().rstrip("/")
        if ws.startswith("http://"):
            ws = "ws://" + ws[len("http://"):]
        elif ws.startswith("https://"):
            ws = "wss://" + ws[len("https://"):]
        self.ws_url = ws

        self.auth_token = cfg.get("auth", "token", fallback=os.getenv("AUTH_TOKEN", ""))

    # -------------------- lifecycle --------------------

    def start(self):
        """Start all active vehicles"""
        self.logger.info("Starting depot operations")
        print("[INFO] Depot OPERATIONAL...")

        for vid, cfg in self.vehicles.items():
            if not cfg.get("active", False):
                print(f"[INFO] Vehicle {vid} inactive.")
                continue

            # Initial state
            logger.debug(f"Vehicle {vid} initial state: {VehicleState.AT_TERMINAL}")

            # After navigator boards - preparing state
            navigator = Navigator(
                vehicle_id=vid,
                route_file=cfg.get("route_file"),
                route=cfg.get("route"),
                engine_buffer=None,   # set after engine below
                mode=cfg.get("mode", "geodesic"),
                direction=cfg.get("direction", "outbound"),
                route_provider=self.route_provider,  # Use the injected route provider
            )
            print(f"[INFO] Navigator boarded for {vid}")
            logger.debug(f"Vehicle {vid} state: {VehicleState.STARTING}")

            # --- GPSDevice ON ---
            # Create WebSocket transmitter for new plugin architecture
            from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
            from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
            
            transmitter = WebSocketTransmitter(
                server_url=self.ws_url,
                token=self.auth_token,
                device_id=vid,
                codec=PacketCodec()
            )
            
            # Configure Navigator plugin to use Navigator telemetry
            plugin_config = {
                "type": "navigator_telemetry", 
                "device_id": vid,
                "navigator": navigator,  # Pass navigator reference
                "update_interval": self.tick_time
            }
            
            gps = GPSDevice(
                device_id=vid,
                ws_transmitter=transmitter,
                plugin_config=plugin_config
            )
            gps.on()
            print(f"[INFO] GPSDevice ON for {vid}")

            # 👉 Use the RxTxBuffer that GPSDevice actually owns
            rxtx_buffer = gps.rxtx_buffer

            # --- Engine start ---
            engine_buffer = EngineBuffer()
            model = load_speed_model(cfg["speed_model"], **cfg)
            engine = Engine(vid, model, engine_buffer, tick_time=self.tick_time)
            engine.on()
            print(f"[INFO] Engine started for {vid}")

            # FleetDispatcher removed - plugin architecture handles telemetry processing
            logger.debug(f"Vehicle {vid} state: {VehicleState.ACTIVE}")

            # Link engine buffer back into navigator BEFORE starting navigator
            navigator.engine_buffer = engine_buffer
            navigator.on()  # Start navigator AFTER engine_buffer is set

            # --- Store references ---
            cfg["_gps"] = gps
            cfg["_engine"] = engine
            cfg["_engine_buffer"] = engine_buffer
            cfg["_navigator"] = navigator
            cfg["_telemetry_buffer"] = navigator.telemetry_buffer
            cfg["_rxtx_buffer"] = rxtx_buffer

    def stop(self):
        """Stop all active vehicles"""
        for vid, cfg in self.vehicles.items():
            if cfg.get("active", False):
                # Start shutdown process
                logger.debug(f"Vehicle {vid} state: {VehicleState.STOPPED}")

            nav = cfg.get("_navigator")
            engine = cfg.get("_engine")
            gps = cfg.get("_gps")

            # Add a clean blank line before shutting down an active vehicle
            if any([nav, engine, gps]):
                print("")

            if engine:
                engine.off()
                print(f"[INFO] Engine stopped for {vid}")
                cfg["_engine"] = None

            if gps:
                gps.off()
                print(f"[INFO] GPSDevice OFF for {vid}")
                cfg["_gps"] = None

            if nav:
                nav.off()
                print(f"[INFO] Navigator disembarked for {vid}")
                cfg["_navigator"] = None

            logger.debug(f"Vehicle {vid} stopping from state: {VehicleState.ACTIVE}")
            logger.debug(f"Vehicle {vid} final state: {VehicleState.AT_TERMINAL}")

        print("[INFO] Depot UNOPERATIONAL")
    
    def check_departures(self):
        """Check if vehicles should depart based on timetable"""
        current_time = datetime.now().time()
        for vid, cfg in self.vehicles.items():
            if not cfg.get("active", False):
                continue
                
            # Note: Simplified departure scheduling for standalone mode
            departure = None  # No complex timetabling in standalone mode
            if departure and current_time >= departure.departure_time:
                self.logger.debug(f"Vehicle {vid} scheduled departure at {departure.departure_time}")
                if not cfg.get("_engine"):  # Only start if not already running
                    self.start_vehicle(vid)

    def start_vehicle(self, vid):
        """Start a specific vehicle"""
        if vid not in self.vehicles:
            return
            
        cfg = self.vehicles[vid]
        if not cfg.get("active", False):
            return
            
        self.logger.debug(f"Vehicle {vid} initial state: {VehicleState.AT_TERMINAL}")

        # After navigator boards - preparing state
        navigator = Navigator(
            vehicle_id=vid,
            route_file=cfg.get("route_file"),
            route=cfg.get("route"),
            engine_buffer=None,   # set after engine below
            mode=cfg.get("mode", "geodesic"),
            direction=cfg.get("direction", "outbound"),
            route_provider=self.route_provider,  # Use the injected route provider
        )
        print(f"[INFO] Navigator boarded for {vid}")
        logger.debug(f"Vehicle {vid} state: {VehicleState.STARTING}")

        # --- GPSDevice ON ---
        gps = GPSDevice(
            vid,
            server_url=self.ws_url,
            auth_token=self.auth_token,
            method="ws",
            interval=self.tick_time,
        )
        gps.on()
        print(f"[INFO] GPSDevice ON for {vid}")

        # 👉 Use the RxTxBuffer that GPSDevice actually owns
        rxtx_buffer = gps.buffer

        # --- Engine start ---
        engine_buffer = EngineBuffer()
        model = load_speed_model(cfg["speed_model"], **cfg)
        engine = Engine(vid, model, engine_buffer, tick_time=self.tick_time)
        engine.on()
        print(f"[INFO] Engine started for {vid}")

        # FleetDispatcher removed - plugin architecture handles telemetry processing
        logger.debug(f"Vehicle {vid} state: {VehicleState.ACTIVE}")

        # Link engine buffer back into navigator
        navigator.engine_buffer = engine_buffer
        navigator.on()

        # --- Store references ---
        cfg["_gps"] = gps
        cfg["_engine"] = engine
        cfg["_engine_buffer"] = engine_buffer
        cfg["_navigator"] = navigator
        cfg["_telemetry_buffer"] = navigator.telemetry_buffer
        cfg["_rxtx_buffer"] = rxtx_buffer

# ---------------------------
# Manual test support
# ---------------------------
if __name__ == "__main__":
    depot = VehiclesDepot()
    depot.start()
    time.sleep(5)
    depot.stop()
