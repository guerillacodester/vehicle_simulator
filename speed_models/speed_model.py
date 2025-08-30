class SpeedModel:
    def __init__(self, min_speed: float, max_speed: float, initial: float = None):
        self.min_speed = float(min_speed)
        self.max_speed = float(max_speed)
        self.velocity = float(initial) if initial is not None else self.min_speed
        self.accel = 0.0
        self.velocity_dir = 0.0   # default heading (east)
        self.accel_dir = 0.0      # default accel direction (same as velocity)

    def update(self, **kwargs) -> dict:
        raise NotImplementedError("Subclasses must implement update()")

    def clamp_velocity(self):
        self.velocity = max(self.min_speed, min(self.max_speed, self.velocity))
