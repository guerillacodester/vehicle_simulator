# speed_models/aggressive_speed.py
import random

# Robust import: absolute, then relative; stub fallback
try:
    from speed_model import SpeedModel
except Exception:
    try:
        from .speed_model import SpeedModel
    except Exception:
        class SpeedModel:
            pass

class AggressiveSpeed(SpeedModel):
    """
    Aggressive ZR van driver:
    - Higher acceleration/deceleration
    - Limited slowdown in corners
    - Quick recovery, plus jitter to avoid robotic output
    """

    def __init__(self,
                 min_speed=20,
                 max_speed=70,
                 cruise_speed=50,
                 accel_limit=3,
                 decel_limit=4,
                 corner_slowdown=30,
                 corner_threshold_deg=40,
                 release_threshold_deg=12,
                 release_ticks=3,
                 **kwargs):

        self.min_speed = float(min_speed)
        self.max_speed = float(max_speed)
        self.cruise_speed = float(cruise_speed)
        self.accel_limit = float(accel_limit)
        self.decel_limit = float(decel_limit)
        self.corner_slowdown = float(corner_slowdown)
        self.corner_threshold_deg = float(corner_threshold_deg)
        self.release_threshold_deg = float(release_threshold_deg)
        self.release_ticks = int(release_ticks)

        self.speed = random.uniform(self.min_speed, self.cruise_speed)
        self.cornering = False
        self.release_counter = 0

    def update(self,
               distance_to_next=None,
               turn_angle=None,
               heading_change=None,
               **_):
        # Resolve turn angle; support both names
        angle = turn_angle if turn_angle is not None else heading_change if heading_change is not None else 0.0
        try:
            angle = abs(float(angle))
        except Exception:
            angle = 0.0
        if angle > 180.0:
            angle = 360.0 - angle

        # Corner detection
        if angle >= self.corner_threshold_deg:
            self.cornering = True
            self.release_counter = 0
            target = min(self.cruise_speed, self.corner_slowdown)
        else:
            if self.cornering:
                if angle <= self.release_threshold_deg:
                    self.release_counter += 1
                if self.release_counter >= self.release_ticks:
                    self.cornering = False
            target = self.cruise_speed

        # Aggressive accel/brake toward target
        if self.speed < target:
            self.speed = min(self.speed + self.accel_limit, target)
        elif self.speed > target:
            self.speed = max(self.speed - self.decel_limit, target)

        # Add jitter and clamp
        self.speed += random.uniform(-0.8, 0.8)
        self.speed = max(self.min_speed, min(self.speed, self.max_speed))
        return float(self.speed)
