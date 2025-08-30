from .speed_model import SpeedModel

class KinematicSpeed(SpeedModel):
    """
    Deterministic kinematic speed model.
    - Linearly accelerates until reaching max_speed.
    - Slows down in corners, then resumes acceleration.
    """

    def __init__(
        self,
        min_speed: float = 30.0,
        max_speed: float = 80.0,
        initial: float = None,
        accel_limit: float = 2.0,
        decel_limit: float = 3.0,
        corner_slowdown: float = 25.0,
        cruise_speed: float = None,
        corner_threshold_deg: float = 35.0,
        release_threshold_deg: float = 12.0,
        release_ticks: int = 3,
    ):
        super().__init__(min_speed, max_speed, initial)

        self.accel_limit = float(accel_limit)
        self.decel_limit = float(decel_limit)
        self.corner_slowdown = float(corner_slowdown)

        self.corner_threshold_deg = float(corner_threshold_deg)
        self.release_threshold_deg = float(release_threshold_deg)
        self.release_ticks = int(release_ticks)

        # Cruise = default long-term target
        self.cruise_speed = float(cruise_speed) if cruise_speed is not None else self.max_speed
        self.target_speed = self.cruise_speed

        # Corner state
        self._in_corner = False
        self._straight_ticks = 0

    def update(self, heading_change: float = 0.0) -> float:
        hc = abs(float(heading_change))

        # --- Corner logic ---
        if hc > self.corner_threshold_deg:
            # Enter/continue corner → slow down
            self._in_corner = True
            self._straight_ticks = 0
            self.target_speed = min(self.corner_slowdown, self.cruise_speed)
        else:
            if self._in_corner:
                # Count straight ticks before exiting corner
                if hc <= self.release_threshold_deg:
                    self._straight_ticks += 1
                    if self._straight_ticks >= self.release_ticks:
                        self._in_corner = False
                        self.target_speed = self.cruise_speed
                else:
                    self._straight_ticks = 0
            else:
                # On straight → always accelerate toward cruise
                self.target_speed = self.cruise_speed

        # --- Smooth accel/decel toward target ---
        if self.speed < self.target_speed:
            self.speed = min(self.speed + self.accel_limit, self.target_speed)
        elif self.speed > self.target_speed:
            self.speed = max(self.speed - self.decel_limit, self.target_speed)

        # Clamp
        self.speed = max(self.min_speed, min(self.max_speed, self.speed))
        return self.speed
