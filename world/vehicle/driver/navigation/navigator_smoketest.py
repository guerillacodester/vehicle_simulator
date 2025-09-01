#!/usr/bin/env python3
"""
Navigator Smoke Test
--------------------
Runs all active vehicles from vehicles.json with their GPSDevice + Engine + Navigator
for a fixed duration. Output is controlled by dump flags.

IMPORTANT: This test reads from Navigator.telemetry_buffer (NOT RxTxBuffer).
Engine figures can be printed from telemetry entries (speed/time/distance).
"""

import os
import sys
import time
import json
import argparse

# Allow running this file directly: ./world/vehicle/driver/navigation/navigator_smoketest.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from world.vehicle.engine.engine_block import Engine
from world.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle.engine.sim_speed_model import load_speed_model
from world.vehicle.driver.navigation.navigator import Navigator
from world.vehicle.gps_device.device import GPSDevice


def main():
    parser = argparse.ArgumentParser(
        description="Navigator smoke test: run active vehicles with selectable interpolation mode."
    )
    parser.add_argument(
        "--seconds", type=float, default=5.0,
        help="Duration to run the simulation (default: 5s)"
    )
    parser.add_argument(
        "--engine-dump", action="store_true",
        help="Dump engine-like figures (speed/time/distance) from telemetry"
    )
    parser.add_argument(
        "--dump-telemetry", action="store_true",
        help="Dump interpolated GPS telemetry (lon/lat/bearing)"
    )
    parser.add_argument(
        "--dump-all", action="store_true",
        help="Dump combined engine + telemetry data"
    )
    parser.add_argument(
        "--mode", choices=["linear", "geodesic"], default="geodesic",
        help="Navigator interpolation mode: 'linear' = legacy, 'geodesic' = improved (default)"
    )
    parser.add_argument(
        "--direction", choices=["inbound", "outbound"], default="outbound",
        help="Route travel direction (default: outbound)"
    )

    args = parser.parse_args()

    # Load manifest
    with open("world/vehicles.json", "r", encoding="utf-8") as f:
        vehicles = json.load(f)

    engines, navigators, gps_devices = {}, {}, {}

    print("[INFO] Starting Navigator smoke test...")

    # Start GPS + Engine + Navigator for active vehicles
    for vid, cfg in vehicles.items():
        if not cfg.get("active", False):
            print(f"[INFO] Vehicle {vid} inactive.")
            continue

        gps = GPSDevice(
            vid,
            os.getenv("WS_URL", "ws://localhost:5000/"),
            os.getenv("AUTH_TOKEN", "supersecrettoken"),
            method="ws",
            interval=0.5
        )
        gps.on()

        eng_buf = EngineBuffer()
        model = load_speed_model(cfg["speed_model"], **cfg)
        engine = Engine(vid, model, eng_buf, tick_time=0.1)

        navigator = Navigator(
            vehicle_id=vid,
            route_file=cfg["route_file"],
            engine_buffer=eng_buf,
            tick_time=0.1,
            mode=args.mode,
            direction=args.direction,   # 👈 new param wired in
        )

        engine.on()
        navigator.on()

        gps_devices[vid] = gps
        engines[vid] = (engine, eng_buf)
        navigators[vid] = navigator

    # Run for N seconds
    time.sleep(args.seconds)

    # Shut down
    for engine, _ in engines.values():
        engine.off()
    for nav in navigators.values():
        nav.off()
    for gps in gps_devices.values():
        gps.off()

    print(f"\n[INFO] Stopping Navigator smoke test... Ran for {args.seconds:.1f} seconds\n")

    # Dump results (from Navigator.telemetry_buffer)
    for vid, nav in navigators.items():
        tel_buf = nav.telemetry_buffer

        if args.engine_dump:
            print(f"=== Vehicle {vid} Engine (from Telemetry) ===")
            while len(tel_buf) > 0:
                e = tel_buf.read()
                if not e:
                    continue
                print(
                    f"{vid} | "
                    f"Speed: {e['speed']:6.2f} km/h | "
                    f"Distance: {e['distance']*1000:7.1f} m | "
                    f"Time: {e['time']:.2f} s"
                )
            print()

        elif args.dump_telemetry:
            print(f"=== Vehicle {vid} Telemetry (mode={args.mode}, dir={args.direction}) ===")
            while len(tel_buf) > 0:
                e = tel_buf.read()
                if not e:
                    continue
                print(
                    f"{vid} | "
                    f"Lon: {e['lon']:.8f} | "
                    f"Lat: {e['lat']:.8f} | "
                    f"Bearing: {e['bearing']:6.2f}°"
                )
            print()

        elif args.dump_all:
            print(f"=== Vehicle {vid} Engine + Telemetry (mode={args.mode}, dir={args.direction}) ===")
            while len(tel_buf) > 0:
                e = tel_buf.read()
                if not e:
                    continue
                print(
                    f"{vid} | "
                    f"Speed: {e['speed']:6.2f} km/h | "
                    f"Distance: {e['distance']*1000:7.1f} m | "
                    f"Time: {e['time']:.2f} s | "
                    f"Lon: {e['lon']:.8f} | "
                    f"Lat: {e['lat']:.8f} | "
                    f"Bearing: {e['bearing']:6.2f}°"
                )
            print()


if __name__ == "__main__":
    main()
