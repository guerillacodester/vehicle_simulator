"""
Real Telemetry Data Adapter - Serial/UART Interface
--------------------------------------------------
Reads NMEA sentences or custom telemetry from serial GPS device
and feeds into the existing RxTx buffer system.
"""

import serial
import time
import threading
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import pynmea2  # For NMEA parsing

from world.vehicle_simulator.vehicle.gps_device.rxtx_buffer import RxTxBuffer

class SerialTelemetryAdapter:
    """
    Reads real GPS data from serial port and feeds into RxTx buffer.
    Maintains compatibility with existing GPS device architecture.
    """
    
    def __init__(self, 
                 port: str = "/dev/ttyUSB0",  # Windows: "COM3", Linux: "/dev/ttyUSB0" 
                 baudrate: int = 9600,
                 device_id: str = "REAL_GPS_001",
                 vehicle_id: str = "BUS001",
                 route_id: str = "R001"):
        
        self.port = port
        self.baudrate = baudrate
        self.device_id = device_id
        self.vehicle_id = vehicle_id
        self.route_id = route_id
        
        # Use existing RxTx buffer system
        self.buffer = RxTxBuffer()
        
        self.serial_conn = None
        self.running = False
        self.reader_thread = None
        
    def start(self):
        """Start reading from serial GPS device"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            
            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_serial_data, daemon=True)
            self.reader_thread.start()
            
            print(f"📡 Real GPS telemetry started on {self.port}")
            
        except Exception as e:
            print(f"❌ Failed to start GPS telemetry: {e}")
            
    def _read_serial_data(self):
        """Read and parse GPS data from serial port"""
        while self.running and self.serial_conn:
            try:
                line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
                
                if line.startswith('$GP'):  # NMEA sentences
                    self._parse_nmea(line)
                elif line.startswith('{'):  # Custom JSON telemetry
                    self._parse_json(line)
                    
            except Exception as e:
                print(f"⚠️ Serial read error: {e}")
                time.sleep(0.1)
                
    def _parse_nmea(self, nmea_sentence: str):
        """Parse NMEA sentence and extract GPS data"""
        try:
            msg = pynmea2.parse(nmea_sentence)
            
            # Only process GGA (position) sentences
            if isinstance(msg, pynmea2.GGA) and msg.latitude and msg.longitude:
                gps_data = {
                    "lat": float(msg.latitude),
                    "lon": float(msg.longitude),
                    "speed": 0.0,  # GGA doesn't have speed, use RMC for speed
                    "heading": 0.0,
                    "route": self.route_id,
                    "vehicle_reg": self.vehicle_id,
                    "driver_id": f"drv-{self.vehicle_id}",
                    "driver_name": {"first": "Real", "last": "Driver"},
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "altitude": float(msg.altitude) if msg.altitude else 0.0,
                    "satellites": int(msg.num_sats) if msg.num_sats else 0
                }
                
                # Feed into existing buffer system
                self.buffer.write(gps_data)
                
        except Exception as e:
            print(f"⚠️ NMEA parse error: {e}")
            
    def _parse_json(self, json_line: str):
        """Parse custom JSON telemetry"""
        try:
            data = json.loads(json_line)
            
            # Convert to standard format
            gps_data = {
                "lat": data.get("latitude", 0.0),
                "lon": data.get("longitude", 0.0), 
                "speed": data.get("speed", 0.0),
                "heading": data.get("bearing", 0.0),
                "route": self.route_id,
                "vehicle_reg": self.vehicle_id,
                "driver_id": f"drv-{self.vehicle_id}",
                "driver_name": {"first": "Real", "last": "Driver"},
                "ts": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }
            
            # Add any custom fields
            for key, value in data.items():
                if key not in gps_data:
                    gps_data[key] = value
                    
            self.buffer.write(gps_data)
            
        except Exception as e:
            print(f"⚠️ JSON parse error: {e}")
            
    def stop(self):
        """Stop reading telemetry"""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()
        print("🛑 Real GPS telemetry stopped")
