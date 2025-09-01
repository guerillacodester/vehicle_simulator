"""
World Vehicles Simulator Entrypoint
Thin bootstrapper: load config, init factory, run briefly, then exit.
"""

import time
from config_loader import load_config
from world.fleet_manifest import FleetManifest
from world.vehicles_factory import VehiclesFactory


def main():
    # Load config
    config = load_config()
    manifest_path = config["files"]["assignment_file"]

    # Prepare manifest + factory
    mf = FleetManifest(manifest_path)
    vf = VehiclesFactory(
        manifest=mf,
        server_url=config["server"]["ws_url"],
        token="",                # TODO: hook in AUTH_TOKEN later
        default_interval=1.0,
        start_active=True,
    )

    print("[INFO] Starting VehiclesFactory...")
    vf.open()

    # Demo: run for a few seconds
    time.sleep(5)

    print("[INFO] Stopping VehiclesFactory...")
    vf.close()


if __name__ == "__main__":
    main()
