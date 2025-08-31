import random
from .speed_model import SpeedModel

class AggressiveSpeed(SpeedModel):
    def __init__(self, min_speed: float, max_speed: float, **kwargs):
        super().__init__(min_speed, max_speed)

    def update(self, **kwargs):
        # Aggressive: sharp jumps between extremes
        new_velocity = random.choice([self.min_speed, self.max_speed])
        self.accel = new_velocity - self.velocity
        self.velocity = new_velocity

        # Aggressive driver swerves directions too
        self.accel_dir = random.uniform(-45, 45)   # sharp steering
        self.velocity_dir += self.accel_dir

        return {
            "velocity": self.velocity,
            "acceleration": self.accel,
            "velocity_dir": self.velocity_dir,
            "accel_dir": self.accel_dir
        }
