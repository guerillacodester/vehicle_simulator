import random
from .speed_model import SpeedModel

class RandomWalkSpeed(SpeedModel):
    def __init__(self, min_speed: float, max_speed: float, step: float = 2.0, **kwargs):
        super().__init__(min_speed, max_speed)
        self.step = float(step)

    def update(self, **kwargs):
        delta = random.uniform(-self.step, self.step)
        new_velocity = self.velocity + delta
        new_velocity = max(self.min_speed, min(self.max_speed, new_velocity))

        self.accel = new_velocity - self.velocity
        self.velocity = new_velocity

        # Random jitter in direction too
        self.accel_dir = random.uniform(-10, 10)   # +/- 10° wobble
        self.velocity_dir += self.accel_dir        # drift heading

        return {
            "velocity": self.velocity,
            "acceleration": self.accel,
            "velocity_dir": self.velocity_dir,
            "accel_dir": self.accel_dir
        }
