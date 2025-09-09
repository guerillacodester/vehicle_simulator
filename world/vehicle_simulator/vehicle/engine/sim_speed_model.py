# world/vehicle/engine/sim_speed_model.py
import importlib

def load_speed_model(name: str, **kwargs):
    """
    Load a speed model from world.vehicle_simulator.speed_models by name.
    Example: name="fixed" -> world.vehicle_simulator.speed_models.fixed_speed.FixedSpeed
    """
    module_name = f"world.vehicle_simulator.speed_models.{name}_speed"
    class_name = "".join([part.capitalize() for part in name.split("_")]) + "Speed"

    try:
        module = importlib.import_module(module_name)   # ❌ no package="vehicle_simulator"
        cls = getattr(module, class_name)

        # 🚨 Ignore keys that belong to vehicles, not models
        ignore_keys = {"active", "vehicle_id", "route_file", "speed_model", "route"}
        model_kwargs = {k: v for k, v in kwargs.items() if k not in ignore_keys}

        # print(f"[DEBUG] Instantiating {class_name} with: {model_kwargs}")

        return cls(**model_kwargs)

    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"Unknown speed model '{name}': {e}")
