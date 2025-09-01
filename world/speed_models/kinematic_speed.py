from .speed_model import SpeedModel

class KinematicSpeed(SpeedModel):
    """
    Kinematic speed model:
    Accelerates or decelerates toward a target cruise speed.
    Internally, velocity is tracked in m/s but returned as km/h
    for consistency with the engine/telemetry pipeline.
    """

    def __init__(self, speed: float, accel_limit: float = 2.0, decel_limit: float = 3.0, **kwargs):
        super().__init__(initial=0.0)  # start at rest (m/s)
        # Treat manifest "speed" value as km/h, convert to m/s internally
        self.target = float(speed) / 3.6
        self.accel_limit = float(accel_limit) / 3.6   # convert km/h per tick → m/s per tick
        self.decel_limit = float(decel_limit) / 3.6

    def update(self, **kwargs):
        # accelerate or decelerate toward target (in m/s)
        if self.velocity < self.target:
            new_velocity = min(self.velocity + self.accel_limit, self.target)
        elif self.velocity > self.target:
            new_velocity = max(self.velocity - self.decel_limit, self.target)
        else:
            new_velocity = self.velocity

        self.accel = new_velocity - self.velocity
        self.velocity = new_velocity

        self.velocity_dir = 0.0
        self.accel_dir = 0.0 if self.accel == 0 else self.velocity_dir

        # Convert back to km/h for engine/telemetry
        velocity_kmh = self.velocity * 3.6
        accel_kmh = self.accel * 3.6

        return {
            "velocity": velocity_kmh,
            "acceleration": accel_kmh,
            "velocity_dir": self.velocity_dir,
            "accel_dir": self.accel_dir,
        }
