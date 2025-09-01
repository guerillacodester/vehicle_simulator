from .speed_model import SpeedModel

class KinematicSpeed(SpeedModel):
    """
    Kinematic speed model:
    Accelerates or decelerates toward a target cruise speed.
    """

    def __init__(self, speed: float, accel_limit: float = 2.0, decel_limit: float = 3.0, **kwargs):
        super().__init__(initial=0.0)  # start at rest
        self.target = float(speed)
        self.accel_limit = float(accel_limit)
        self.decel_limit = float(decel_limit)

    def update(self, **kwargs):
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

        return {
            "velocity": self.velocity,
            "acceleration": self.accel,
            "velocity_dir": self.velocity_dir,
            "accel_dir": self.accel_dir,
        }
