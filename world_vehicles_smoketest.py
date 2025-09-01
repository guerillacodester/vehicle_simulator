#!/usr/bin/env python3
"""
World Vehicles Smoke Test
-------------------------
Runs all active vehicles with GPSDevice + Engine + Navigator lifecycles.
After shutdown, you can optionally dump diagnostic buffers:

  --dump-engine      EngineBuffer only
  --dump-telemetry   TelemetryBuffer only
  --dump-all         Both EngineBuffer + TelemetryBuffer

This allows verification of physics (engine), navigation (telemetry),
or both together, without transmitting live data (RxTxBuffer is empty
once GPSDevice is OFF).
"""

import argparse
import time
from world.vehicles_factory import VehiclesFactory


def validate_engine_data(entries, cfg, tick_time=0.1, tol=1e-6):
    """
    Validate kinematic physics rules for engine data entries.
    """
    accel_limit = cfg.get("accel_limit", None)
    target = cfg.get("cruise_speed", cfg.get("speed", None))

    ok = True
    errors = []

    if not entries:
        return ok, errors

    prev_speed = entries[0]["cruise_speed"]
    prev_distance = entries[0]["distance"]

    # start validation from the 2nd entry
    for i, e in enumerate(entries[1:], start=2):
        v = e["cruise_speed"]
        d = e["distance"]

        # 1. Check acceleration step
        if accel_limit and v < target:
            expected = prev_speed + accel_limit
            if abs(v - expected) > tol:
                ok = False
                errors.append(
                    f"Tick {i}: Speed {v:.2f} vs expected {expected:.2f}"
                )

        # 2. Check distance increment
        inc = d - prev_distance
        expected_inc = (v * tick_time) / 3600
        if abs(inc - expected_inc) > tol:
            ok = False
            errors.append(
                f"Tick {i}: Distance increment {inc:.6f} vs expected {expected_inc:.6f}"
            )

        prev_speed = v
        prev_distance = d

    return ok, errors


def drain_buffer(buf):
    """Drain all entries from a buffer into a list."""
    entries = []
    if not buf:
        return entries
    while len(buf) > 0:
        entry = buf.read()
        if entry:
            entries.append(entry)
    return entries


def main():
    parser = argparse.ArgumentParser(
        description="Smoke test for world vehicles simulator (GPS + Engine + Navigator lifecycles)."
    )
    parser.add_argument(
        "--manifest", type=str, default="world/vehicles.json",
        help="Path to vehicles manifest (default: world/vehicles.json)"
    )
    parser.add_argument(
        "--tick", type=float, default=0.1,
        help="Tick interval in seconds (default: 0.1)"
    )
    parser.add_argument(
        "--seconds", type=float, default=5.0,
        help="How long to run the simulation (default: 5s)"
    )
    parser.add_argument(
        "--dump-engine", action="store_true",
        help="After shutdown, drain and print EngineBuffer diagnostics per vehicle."
    )
    parser.add_argument(
        "--dump-telemetry", action="store_true",
        help="After shutdown, drain and print TelemetryBuffer diagnostics per vehicle."
    )
    parser.add_argument(
        "--dump-all", action="store_true",
        help="After shutdown, drain and print both EngineBuffer and TelemetryBuffer."
    )
    args = parser.parse_args()

    factory = VehiclesFactory(manifest_path=args.manifest, tick_time=args.tick)

    factory.start()
    time.sleep(args.seconds)
    factory.stop()

    print(f"\nSimulation complete. Ran for {args.seconds:.1f} seconds")

    for vid, cfg in factory.vehicles.items():
        engine_buf = cfg.get("_engine_buffer")
        telem_buf = cfg.get("_telemetry_buffer")

        # --- Engine diagnostics ---
        if args.dump_engine or args.dump_all:
            entries = drain_buffer(engine_buf)
            if entries:
                print(f"\n=== Engine Data for {vid} ===")
                for e in entries:
                    dist = e["distance"]
                    if dist < 1.0:
                        display_distance = f"{dist * 1000:7.1f} m"
                    else:
                        display_distance = f"{dist:7.3f} km"

                    print(
                        f"{vid} | "
                        f"Speed: {e['cruise_speed']:6.2f} km/h | "
                        f"Heading: {e.get('heading', 0.0):6.2f}° | "
                        f"Distance: {display_distance} | "
                        f"Time: {e['time']:.2f} s"
                    )

                ok, errors = validate_engine_data(entries, cfg, tick_time=args.tick)
                if ok:
                    print(f"[OK] Physics validated for {vid}")
                else:
                    print(f"[FAIL] Physics mismatches for {vid}:")
                    for err in errors:
                        print("   -", err)

        # --- Telemetry diagnostics ---
        if args.dump_telemetry or args.dump_all:
            entries = drain_buffer(telem_buf)
            if entries:
                print(f"\n=== Telemetry Data for {vid} ===")
                for e in entries:
                    print(
                        f"{vid} | "
                        f"Lon: {e['lon']:.8f} | "
                        f"Lat: {e['lat']:.8f} | "
                        f"Bearing: {e['bearing']:.2f}° | "
                        f"Speed: {e.get('speed', 0.0):6.2f} km/h | "
                        f"Distance: {e.get('distance', 0.0):.1f} m | "
                        f"Time: {e.get('time', 0.0):.2f} s"
                    )


if __name__ == "__main__":
    main()
