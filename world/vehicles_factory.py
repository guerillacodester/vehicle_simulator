#!/usr/bin/env python3
"""
VehiclesFactory
---------------
Responsible for instantiating and managing GPSDevice and EngineBlock
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


class VehiclesFactory:
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
        # Resolve project root (parent of 'world/')
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cfg_path = os.path.join(project_root, "config.ini")

        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)

        raw_ws = cfg.get("server", "ws_url", fallback="ws://localhost:5000")
        ws = raw_ws.strip()
        ws = ws.rstrip("/")  # avoid //device
        if ws.startswith("http://"):   # tolerate http -> ws
            ws = "ws://" + ws[len("http://"):]
        elif ws.startswith("https://"):  # tolerate https -> wss
            ws = "wss://" + ws[len("https://"):]
        self.ws_url = ws

        # token can come from config or ENV (AUTH_TOKEN)
        self.auth_token = cfg.get("auth", "token", fallback=os.getenv("AUTH_TOKEN", ""))

    # -------------------- lifecycle --------------------

    def start(self):
        print("[INFO] Starting VehiclesFactory...")

        for vid, cfg in self.vehicles.items():
            if not cfg.get("active", False):
                print(f"[INFO] Vehicle {vid} inactive.")
                continue

            # Debug: show connection params
            masked = (self.auth_token[:4] + "…") if self.auth_token else "(none)"
            print(f"[DEBUG] GPS init for {vid}: ws_url='{self.ws_url}', token={masked}")

            # Start GPS device (uses real config)
            gps = GPSDevice(
                vid,
                server_url=self.ws_url,
                auth_token=self.auth_token,
                method="ws",
                interval=self.tick_time,
            )
            gps.on()

            # Start Engine
            buffer = EngineBuffer()
            model = load_speed_model(cfg["speed_model"], **cfg)
            engine = Engine(vid, model, buffer, tick_time=self.tick_time)
            engine.on()

            # Store references so we can stop later
            cfg["_gps"] = gps
            cfg["_engine"] = engine
            cfg["_engine_buffer"] = buffer

    def stop(self):
        print("\n[INFO] Stopping VehiclesFactory...")
        for vid, cfg in self.vehicles.items():
            gps = cfg.get("_gps")
            engine = cfg.get("_engine")

            if gps:
                gps.off()
                cfg["_gps"] = None
            if engine:
                engine.off()
                cfg["_engine"] = None


# ---------------------------
# Manual test support
# ---------------------------
if __name__ == "__main__":
    factory = VehiclesFactory()
    factory.start()
    time.sleep(5)
    factory.stop()
