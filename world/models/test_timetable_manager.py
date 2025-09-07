import unittest
from datetime import time
from .timetable_manager import TimetableManager
import json
import os

class TestTimetableManager(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_timetable.json"
        # Create test timetable file
        test_data = {
            "ZR1001": [
                {
                    "route_id": "1",
                    "departure_time": "09:00",
                    "terminal_id": "TERMINAL_1"
                }
            ]
        }
        with open(self.test_file, 'w') as f:
            json.dump(test_data, f)
            
    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
            
    def test_load_timetable(self):
        manager = TimetableManager()
        success = manager.load_timetable(self.test_file)
        self.assertTrue(success)
        self.assertIn("ZR1001", manager.departures)
        
    def test_get_next_departure(self):
        manager = TimetableManager()
        manager.load_timetable(self.test_file)
        departure = manager.get_next_departure("ZR1001")
        self.assertIsNotNone(departure)
        self.assertEqual(departure.vehicle_id, "ZR1001")
        self.assertEqual(departure.route_id, "1")

if __name__ == '__main__':
    unittest.main()