import random
from .speed_model import SpeedModel

class RandomWalkSpeed(SpeedModel):
    """
    Random-walk speed model:
    Small random step changes around base speed, with bounded variance.
    """

    def __init__(self, speed: float, step: float = 2.0, variance: float = 10.0, **kwargs):
        super().__init__(initial=speed)
        self.base_speed = float(speed)
        self.step = float(step)
        self.variance = float(variance)

    def update(self, **kwargs):
        delta = random.uniform(-self.step, self.step)
        new_velocity = self.velocity + delta

        lower = max(0.0, self.base_speed - self.variance)
        upper = self.base_speed + self.variance
        new_velocity = max(lower, min(upper, new_velocity))

        self.accel = new_velocity - self.velocity
        self.velocity = new_velocity

        self.accel_dir = random.uniform(-10, 10)   # gentle wobble
        self.velocity_dir += self.accel_dir

        return {
            "velocity": self.velocity,
            "acceleration": self.accel,
            "velocity_dir": self.velocity_dir,
            "accel_dir": self.accel_dir,
        }
