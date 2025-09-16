from .speed_model import SpeedModel

class FixedSpeed(SpeedModel):
    """
    Fixed speed model:
    Always drives at the configured constant speed.
    """

    def __init__(self, speed: float, **kwargs):
        super().__init__(initial=speed)

    def update(self, **kwargs):
        self.accel = 0.0
        self.accel_dir = 0.0
        self.velocity_dir = 0.0
        return {
            "velocity": self.velocity,
            "acceleration": self.accel,
            "velocity_dir": self.velocity_dir,
            "accel_dir": self.accel_dir,
        }
