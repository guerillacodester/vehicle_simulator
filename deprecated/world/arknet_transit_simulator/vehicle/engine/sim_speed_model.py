# world/vehicle/engine/sim_speed_model.py
import importlib


PHYSICS_MODEL_NAME = "physics"

def load_speed_model(name: str, **kwargs):
    """
    Load a speed model from world.arknet_transit_simulator.models.speed_models by name.
    Example: name="fixed" -> world.arknet_transit_simulator.models.speed_models.fixed_speed.FixedSpeed
    """
    # Special-case physics kernel adapter (lives in vehicle.physics)
    if name == PHYSICS_MODEL_NAME:
        try:
            module = importlib.import_module("world.arknet_transit_simulator.vehicle.physics.physics_speed_model")
            cls = getattr(module, "PhysicsSpeedModel")
            ignore_keys = {"active", "vehicle_id", "route_file", "speed_model", "route"}
            model_kwargs = {k: v for k, v in kwargs.items() if k not in ignore_keys}
            return cls(**model_kwargs)
        except (ImportError, AttributeError) as e:
            raise RuntimeError(f"Failed to load physics speed model: {e}")

    module_name = f"world.arknet_transit_simulator.models.speed_models.{name}_speed"
    class_name = "".join([part.capitalize() for part in name.split("_")]) + "Speed"

    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)

        # 🚨 Ignore keys that belong to vehicles, not models
        ignore_keys = {"active", "vehicle_id", "route_file", "speed_model", "route"}
        model_kwargs = {k: v for k, v in kwargs.items() if k not in ignore_keys}

        # print(f"[DEBUG] Instantiating {class_name} with: {model_kwargs}")

        return cls(**model_kwargs)

    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"Unknown speed model '{name}': {e}")
