#!/usr/bin/env python3
"""
World Vehicles Smoke Test
-------------------------
Smoke test for world vehicles simulator (GPS + Engine lifecycle).
Runs all active vehicles from the manifest for N seconds, then shuts down
and optionally dumps engine diagnostics grouped by vehicle with validation.
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

    prev_speed = 0.0
    prev_distance = 0.0
    ok = True
    errors = []

    for i, e in enumerate(entries, start=1):
        v = e["cruise_speed"]
        d = e["distance"]
        t = e["time"]

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


def main():
    parser = argparse.ArgumentParser(
        description="Smoke test for world vehicles simulator (GPS + Engine lifecycle)."
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
        help="After shutdown, drain and print formatted engine diagnostics per vehicle."
    )
    args = parser.parse_args()

    factory = VehiclesFactory(manifest_path=args.manifest, tick_time=args.tick)

    factory.start()
    time.sleep(args.seconds)
    factory.stop()

    print(f"\nSimulation complete. Ran for {args.seconds:.1f} seconds")

    if args.dump_engine:
        for vid, cfg in factory.vehicles.items():
            buf = cfg.get("_engine_buffer")
            if not buf:
                continue

            # drain buffer
            entries = []
            while len(buf) > 0:
                entry = buf.read()
                if entry:
                    entries.append(entry)

            if not entries:
                continue

            # print diagnostics
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

            # validation
            ok, errors = validate_engine_data(entries, cfg, tick_time=args.tick)
            if ok:
                print(f"[OK] Physics validated for {vid}")
            else:
                print(f"[FAIL] Physics mismatches for {vid}:")
                for err in errors:
                    print("   -", err)


if __name__ == "__main__":
    main()
