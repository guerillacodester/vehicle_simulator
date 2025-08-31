from .speed_model import SpeedModel

class FixedSpeed(SpeedModel):
    def __init__(self, min_speed: float, max_speed: float, **kwargs):
        super().__init__(min_speed, max_speed, (min_speed + max_speed) / 2)

    def update(self, **kwargs):
        self.accel = 0.0
        self.velocity_dir = 0.0
        self.accel_dir = 0.0
        return {
            "velocity": self.velocity,
            "acceleration": self.accel,
            "velocity_dir": self.velocity_dir,
            "accel_dir": self.accel_dir
        }
