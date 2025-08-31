from config_loader import load_config
from vehicle_store import get_vehicle_config
from simulation_engine.simulator import simulate_movement


def main():
    config = load_config()
    vehicle_storage = config["files"]["vehicle_storage"]
    vehicle_cfg = get_vehicle_config(vehicle_storage)

    print(f"[INFO] Vehicle: {vehicle_cfg['vehicle_id']}")
    for k, v in vehicle_cfg.items():
        print(f"  {k}: {v}")

    tick = float(vehicle_cfg.get("tick", 0.1))
    speed_model = vehicle_cfg["speed_model"]

    # ✅ Now route_file stays inside vehicle_cfg, simulator reads it
    simulate_movement(tick, speed_model, **vehicle_cfg)


if __name__ == "__main__":
    main()
