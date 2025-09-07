from datetime import time
from .timetable import Departure

def test_departure():
    departure = Departure(
        vehicle_id="ZR1001",
        route_id="1",
        departure_time=time(9, 0),  # 9:00 AM
        terminal_id="TERMINAL_1"
    )
    assert departure.vehicle_id == "ZR1001"
    assert departure.route_id == "1"
    
if __name__ == "__main__":
    test_departure()
    print("[INFO] Timetable model test passed")