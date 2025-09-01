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

from world.vehicle.gps_device.device import GPSDevice
from world.vehicle.engine.engine_block import Engine
from world.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle.engine.sim_speed_model import load_speed_model

# Navigator (manages its own TelemetryBuffer internally)
from world.vehicle.driver.navigation.navigator import Navigator


class VehiclesDepot:
    def __init__(self, manifest_path: str = "world/vehicles.json", tick_time: float = 0.1):
        self.manifest_path = manifest_path
        self.tick_time = tick_time
        self.vehicles = {}
        self._load_manifest()
        self._load_config()  # load ws_url/auth, normalize

    # -------------------- manifest --------------------

    def _load_manifest(self):
        if not os.path.exists(self.manifest_path):
            sys.exit(f"[ERROR] vehicles manifest not found: {self.manifest_path}")

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict) or not data:
            sys.exit(f"[ERROR] vehicles manifest must be a non-empty JSON object")

        self.vehicles = data

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
        print("[INFO] Starting VehiclesDepot...")

        for vid, cfg in self.vehicles.items():
            if not cfg.get("active", False):
                print(f"[INFO] Vehicle {vid} inactive.")
                continue

            masked = (self.auth_token[:4] + "…") if self.auth_token else "(none)"
            print(f"[DEBUG] Init for {vid}: ws_url='{self.ws_url}', token={masked}")

            # ---------------- Navigator boards ----------------
            navigator = Navigator(
                vehicle_id=vid,
                route_file=cfg.get("route_file"),
                engine_buffer=None,   # set after engine below
                mode=cfg.get("mode", "geodesic"),
                direction=cfg.get("direction", "outbound"),
            )
            print(f"[INFO] Navigator boarded for {vid}")

            # ---------------- GPS device ON ----------------
            gps = GPSDevice(
                vid,
                server_url=self.ws_url,
                auth_token=self.auth_token,
                method="ws",
                interval=self.tick_time,
            )
            gps.on()
            print(f"[INFO] GPSDevice ON for {vid}")

            # ---------------- Engine start ----------------
            buffer = EngineBuffer()
            model = load_speed_model(cfg["speed_model"], **cfg)
            engine = Engine(vid, model, buffer, tick_time=self.tick_time)
            engine.on()
            print(f"[INFO] Engine started for {vid}")

            # Link engine buffer back into navigator
            navigator.engine_buffer = buffer
            navigator.on()

            # ---------------- Store references ----------------
            cfg["_gps"] = gps
            cfg["_engine"] = engine
            cfg["_engine_buffer"] = buffer
            cfg["_navigator"] = navigator
            cfg["_telemetry_buffer"] = navigator.telemetry_buffer  # ✅ pull from Navigator

    def stop(self):
        print("\n[INFO] Stopping VehiclesDepot...")
        for vid, cfg in self.vehicles.items():
            nav = cfg.get("_navigator")
            engine = cfg.get("_engine")
            gps = cfg.get("_gps")

            if nav:
                nav.off()
                print(f"[INFO] Navigator disembarked for {vid}")
                cfg["_navigator"] = None

            if engine:
                engine.off()
                print(f"[INFO] Engine stopped for {vid}")
                cfg["_engine"] = None

            if gps:
                gps.off()
                print(f"[INFO] GPSDevice OFF for {vid}")
                cfg["_gps"] = None


# ---------------------------
# Manual test support
# ---------------------------
if __name__ == "__main__":
    depot = VehiclesDepot()
    depot.start()
    time.sleep(5)
    depot.stop()
