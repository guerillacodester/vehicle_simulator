import random
from .speed_model import SpeedModel

class AggressiveSpeed(SpeedModel):
    """
    Aggressive speed model:
    Jumps speed around the base value with wide variance.
    Adds strong steering swings.
    """

    def __init__(self, speed: float, variance: float = 20.0, **kwargs):
        super().__init__(initial=speed)
        self.base_speed = float(speed)
        self.variance = float(variance)

    def update(self, **kwargs):
        new_velocity = random.uniform(
            max(0.0, self.base_speed - self.variance),
            self.base_speed + self.variance
        )

        self.accel = new_velocity - self.velocity
        self.velocity = new_velocity

        self.accel_dir = random.uniform(-45, 45)   # big swings
        self.velocity_dir += self.accel_dir

        return {
            "velocity": self.velocity,
            "acceleration": self.accel,
            "velocity_dir": self.velocity_dir,
            "accel_dir": self.accel_dir,
        }
