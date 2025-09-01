from config_loader import load_config
from world.fleet_manifest import get_vehicle_config
from engine.simulator import simulate_movement


def main():
    config = load_config()
    assignment_file = config["files"]["assignment_file"]
    vehicle_cfg = get_vehicle_config(assignment_file)

    print(f"[INFO] Vehicle: {vehicle_cfg['vehicle_id']}")
    for k, v in vehicle_cfg.items():
        print(f"  {k}: {v}")

    tick = float(vehicle_cfg.get("tick", 0.1))
    speed_model = vehicle_cfg["speed_model"]

    # ✅ Now route_file stays inside vehicle_cfg, simulator reads it
    simulate_movement(tick, speed_model, **vehicle_cfg)


if __name__ == "__main__":
    main()
