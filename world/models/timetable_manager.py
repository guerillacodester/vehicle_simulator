from datetime import datetime, time
from typing import List, Dict, Optional
from .timetable import Departure
import json
import logging

logger = logging.getLogger(__name__)

class TimetableManager:
    def __init__(self):
        self.departures: Dict[str, List[Departure]] = {}
    
    def load_timetable(self, filepath: str) -> bool:
        """Load timetable from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            for vehicle_id, schedules in data.items():
                self.departures[vehicle_id] = [
                    Departure(
                        vehicle_id=vehicle_id,
                        route_id=s['route_id'],
                        departure_time=datetime.strptime(s['departure_time'], '%H:%M').time(),
                        terminal_id=s.get('terminal_id', 'TERMINAL_1')
                    ) for s in schedules
                ]
            logger.debug(f"Loaded timetable for {len(self.departures)} vehicles")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load timetable: {e}")
            return False
    
    def get_next_departure(self, vehicle_id: str) -> Optional[Departure]:
        """Get next departure for vehicle"""
        if vehicle_id not in self.departures:
            return None
            
        current_time = datetime.now().time()
        departures = self.departures[vehicle_id]
        
        # Return first departure if found
        if departures:
            return departures[0]
            
        return None