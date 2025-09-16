import time
from .sim_speed_model import load_speed_model


def simulate_movement(tick: float, speed_model_name: str, **vehicle_cfg):
    """
    Dumb simulator loop.
    - Models produce physics (velocity, acceleration, directions).
    - Simulator only enacts them: integrates distance & time.
    """

    # Load the speed model dynamically
    speed_model = load_speed_model(speed_model_name, **vehicle_cfg)

    total_distance = 0.0  # km
    total_time = 0.0      # seconds

    print(f"[INFO] Running model '{speed_model_name}' with tick={tick:.2f}s")
    print(f"[DEBUG] Vehicle parameters: {vehicle_cfg}")

    # Main simulation loop
    for step in range(100):  # simulate 100 ticks (or make configurable)
        # Ask the model what the state is this tick
        state = speed_model.update()

        velocity = state.get("velocity", 0.0)         # km/h
        accel = state.get("acceleration", 0.0)       # km/h/s
        vdir = state.get("velocity_dir", 0.0)        # degrees (or vector)
        adir = state.get("accel_dir", 0.0)           # degrees (or vector)

        # Integrate distance (simple: v * Δt)
        distance_moved = velocity * (tick / 3600.0)  # km
        total_distance += distance_moved
        total_time += tick

        # Telemetry output
        print(
            f"T+{total_time:.1f}s | "
            f"Vel: {velocity:.2f} km/h @ {vdir:.1f}° | "
            f"Accel: {accel:.2f} km/h/s @ {adir:.1f}° | "
            f"StepDist: {distance_moved:.4f} km | TotDist: {total_distance:.3f} km"
        )

        time.sleep(tick)

    print(
        f"\n[INFO] Simulation finished | "
        f"Total Time: {total_time:.1f}s | Total Distance: {total_distance:.3f} km"
    )
