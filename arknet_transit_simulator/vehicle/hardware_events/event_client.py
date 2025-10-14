"""
Hardware Event Client
=====================

Base client for sending hardware-triggered events to the fleet management API.
Used by both real hardware devices and simulated conductor.

Architecture:
    Hardware Device (RFID/Door/GPS) → HardwareEventClient → Fleet API → Database

Usage in Simulation:
    conductor = Conductor(vehicle)
    conductor.hardware_client = HardwareEventClient(api_url, vehicle_id)
    conductor.board_passenger(passenger_id)  # Calls same API as real hardware

Usage in Real Hardware:
    rfid_reader = RFIDReader(hardware_client)
    rfid_reader.on_card_tap(card_id)  # Calls same API as simulation
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import httpx # type: ignore


class HardwareEventClient:
    """
    Client for sending hardware events to the fleet management API.
    Both physical hardware and simulated conductor use this same interface.
    """
    
    def __init__(self, api_url: str, vehicle_id: str, device_id: Optional[str] = None):
        """
        Initialize hardware event client.
        
        Args:
            api_url: Base URL of fleet management API (e.g., http://localhost:1337)
            vehicle_id: Unique identifier for this vehicle
            device_id: Optional unique identifier for the hardware device
        """
        self.api_url = api_url.rstrip('/')
        self.vehicle_id = vehicle_id
        self.device_id = device_id or f"device_{vehicle_id}"
        self.logger = logging.getLogger(__name__)
        self.client: Optional[httpx.AsyncClient] = None
        
    async def connect(self):
        """Initialize HTTP client connection"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=10.0)
            self.logger.info(f"🔌 Hardware event client connected: vehicle={self.vehicle_id}")
    
    async def disconnect(self):
        """Close HTTP client connection"""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.logger.info(f"🔌 Hardware event client disconnected: vehicle={self.vehicle_id}")
    
    async def report_position(self, latitude: float, longitude: float, 
                             speed_kmh: float = 0.0, heading: float = 0.0) -> bool:
        """
        Report vehicle GPS position (called by GPS hardware or simulator).
        
        Args:
            latitude: Current latitude
            longitude: Current longitude
            speed_kmh: Current speed in km/h
            heading: Current heading in degrees (0-360)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            await self.connect()
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/vehicle-events/position",
                json={
                    "vehicle_id": self.vehicle_id,
                    "device_id": self.device_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "speed_kmh": speed_kmh,
                    "heading": heading,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            if response.status_code in (200, 201):
                return True
            else:
                self.logger.warning(f"⚠️ Position update failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error reporting position: {e}")
            return False
    
    async def door_event(self, door_id: str, action: str, latitude: float, longitude: float) -> bool:
        """
        Report door sensor event (called by door hardware or simulator).
        
        Args:
            door_id: Identifier for the door ("front", "rear", etc.)
            action: Door action ("opened", "closed")
            latitude: Current vehicle latitude
            longitude: Current vehicle longitude
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            await self.connect()
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/vehicle-events/door",
                json={
                    "vehicle_id": self.vehicle_id,
                    "device_id": self.device_id,
                    "door_id": door_id,
                    "action": action,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            if response.status_code in (200, 201):
                self.logger.debug(f"🚪 Door {action}: {door_id}")
                return True
            else:
                self.logger.warning(f"⚠️ Door event failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error reporting door event: {e}")
            return False
    
    async def rfid_tap(self, card_id: str, tap_type: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Report RFID card tap (called by RFID hardware or simulator).
        
        Args:
            card_id: RFID card/passenger ID
            tap_type: Type of tap ("board", "alight")
            latitude: Current vehicle latitude
            longitude: Current vehicle longitude
            
        Returns:
            Response dict with passenger info and success status
        """
        if not self.client:
            await self.connect()
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/vehicle-events/rfid-tap",
                json={
                    "vehicle_id": self.vehicle_id,
                    "device_id": self.device_id,
                    "card_id": card_id,
                    "tap_type": tap_type,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                if tap_type == "board":
                    self.logger.info(f"✅ Passenger boarded: {card_id}")
                else:
                    self.logger.info(f"✅ Passenger alighted: {card_id}")
                return result
            else:
                self.logger.warning(f"⚠️ RFID tap failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"❌ Error processing RFID tap: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_passenger_count(self, count_in: int, count_out: int, 
                                    total_onboard: int) -> bool:
        """
        Report passenger counter update (called by IR sensor hardware or simulator).
        
        Args:
            count_in: Number of passengers who entered since last update
            count_out: Number of passengers who exited since last update  
            total_onboard: Total passengers currently on board
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            await self.connect()
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/vehicle-events/passenger-count",
                json={
                    "vehicle_id": self.vehicle_id,
                    "device_id": self.device_id,
                    "count_in": count_in,
                    "count_out": count_out,
                    "total_onboard": total_onboard,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            if response.status_code in (200, 201):
                self.logger.debug(f"👥 Passenger count updated: {total_onboard} onboard (+{count_in}/-{count_out})")
                return True
            else:
                self.logger.warning(f"⚠️ Count update failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error updating passenger count: {e}")
            return False
    
    async def driver_confirm_boarding(self, passenger_ids: list[str], 
                                     latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Driver manually confirms passenger boarding via tablet/app.
        
        Args:
            passenger_ids: List of passenger IDs boarding
            latitude: Current vehicle latitude
            longitude: Current vehicle longitude
            
        Returns:
            Response dict with boarding results
        """
        if not self.client:
            await self.connect()
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/vehicle-events/driver-confirm-boarding",
                json={
                    "vehicle_id": self.vehicle_id,
                    "device_id": self.device_id,
                    "passenger_ids": passenger_ids,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                self.logger.info(f"✅ Driver confirmed {len(passenger_ids)} boarding")
                return result
            else:
                self.logger.warning(f"⚠️ Driver confirmation failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"❌ Error confirming boarding: {e}")
            return {"success": False, "error": str(e)}
    
    async def driver_confirm_alighting(self, passenger_ids: list[str],
                                      latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Driver manually confirms passenger alighting via tablet/app.
        
        Args:
            passenger_ids: List of passenger IDs alighting
            latitude: Current vehicle latitude
            longitude: Current vehicle longitude
            
        Returns:
            Response dict with alighting results
        """
        if not self.client:
            await self.connect()
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/vehicle-events/driver-confirm-alighting",
                json={
                    "vehicle_id": self.vehicle_id,
                    "device_id": self.device_id,
                    "passenger_ids": passenger_ids,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                self.logger.info(f"✅ Driver confirmed {len(passenger_ids)} alighting")
                return result
            else:
                self.logger.warning(f"⚠️ Driver confirmation failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"❌ Error confirming alighting: {e}")
            return {"success": False, "error": str(e)}
    
    async def arrive_at_stop(self, stop_id: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Report vehicle arrival at stop (GPS geofence trigger).
        
        Args:
            stop_id: Identifier for the bus stop
            latitude: Stop latitude
            longitude: Stop longitude
            
        Returns:
            Response dict with nearby waiting passengers
        """
        if not self.client:
            await self.connect()
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/vehicle-events/arrive-stop",
                json={
                    "vehicle_id": self.vehicle_id,
                    "device_id": self.device_id,
                    "stop_id": stop_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                waiting_count = result.get('waiting_passengers', 0)
                self.logger.info(f"🚏 Arrived at stop {stop_id}: {waiting_count} waiting")
                return result
            else:
                self.logger.warning(f"⚠️ Stop arrival failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"❌ Error reporting stop arrival: {e}")
            return {"success": False, "error": str(e)}
    
    async def depart_from_stop(self, stop_id: str) -> bool:
        """
        Report vehicle departure from stop.
        
        Args:
            stop_id: Identifier for the bus stop
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            await self.connect()
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/vehicle-events/depart-stop",
                json={
                    "vehicle_id": self.vehicle_id,
                    "device_id": self.device_id,
                    "stop_id": stop_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            if response.status_code in (200, 201):
                self.logger.info(f"🚏 Departed from stop {stop_id}")
                return True
            else:
                self.logger.warning(f"⚠️ Stop departure failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error reporting stop departure: {e}")
            return False
