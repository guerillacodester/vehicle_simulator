from .speed_model import SpeedModel


class KinematicSpeed(SpeedModel):
    """
    Kinematic speed model:
    - Accelerates or decelerates toward a target cruise speed
    - Target speed can be specified in config as 'cruise_speed'
    - Otherwise defaults to midpoint between min_speed and max_speed
    """

    def __init__(
        self,
        min_speed: float,
        max_speed: float,
        accel_limit: float = 2.0,
        decel_limit: float = 3.0,
        cruise_speed: float = None,
        **kwargs
    ):
        super().__init__(min_speed, max_speed)
        self.accel_limit = float(accel_limit)
        self.decel_limit = float(decel_limit)

        # ✅ target speed is either cruise_speed from config, or midpoint
        if cruise_speed is not None:
            self.target = max(self.min_speed, min(self.max_speed, float(cruise_speed)))
        else:
            self.target = (self.min_speed + self.max_speed) / 2

    def update(self, **kwargs) -> dict:
        # Adjust velocity toward target
        if self.velocity < self.target:
            new_velocity = min(self.velocity + self.accel_limit, self.target)
        elif self.velocity > self.target:
            new_velocity = max(self.velocity - self.decel_limit, self.target)
        else:
            new_velocity = self.velocity

        self.accel = new_velocity - self.velocity
        self.velocity = new_velocity

        # Directions are straight-line defaults (extendable later)
        self.velocity_dir = 0.0
        self.accel_dir = 0.0 if self.accel == 0 else self.velocity_dir

        return {
            "velocity": self.velocity,
            "acceleration": self.accel,
            "velocity_dir": self.velocity_dir,
            "accel_dir": self.accel_dir
        }
