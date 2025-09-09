"""
Real Telemetry Data Injector
----------------------------
Simple adapters to inject real telemetry data into existing RxTx buffer.
The GPS device handles all network transmission automatically.
"""

import serial
import json
import time
import threading
from datetime import datetime, timezone
from typing import Optional, Callable


class SerialDataInjector:
    """
    Reads real GPS data from serial port and injects into RxTx buffer.
    Ultra-simple - just replaces the simulated data source.
    """
    
    def __init__(self, 
                 rxtx_buffer,  # Pass in the existing buffer
                 port: str = "COM3",  # Windows: "COM3", Linux: "/dev/ttyUSB0"
                 baudrate: int = 9600,
                 device_id: str = "REAL_GPS"):
        
        self.buffer = rxtx_buffer
        self.port = port
        self.baudrate = baudrate
        self.device_id = device_id
        
        self.serial_conn = None
        self.running = False
        self.thread = None
        
    def start(self):
        """Start injecting real data into buffer"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._read_and_inject, daemon=True)
            self.thread.start()
            print(f"📡 Real telemetry injection started on {self.port}")
            
        except Exception as e:
            print(f"❌ Serial connection failed: {e}")
            
    def _read_and_inject(self):
        """Read serial data and inject into buffer"""
        while self.running:
            try:
                line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
                
                if line:
                    # Parse the line and create GPS data
                    gps_data = self._parse_line(line)
                    if gps_data:
                        # Inject directly into existing buffer
                        self.buffer.write(gps_data)
                        
            except Exception as e:
                print(f"⚠️ Read error: {e}")
                time.sleep(0.1)
                
    def _parse_line(self, line: str) -> Optional[dict]:
        """Parse incoming data line"""
        try:
            # Option 1: JSON format
            if line.startswith('{'):
                data = json.loads(line)
                return {
                    "lat": data.get("lat", 0.0),
                    "lon": data.get("lon", 0.0),
                    "speed": data.get("speed", 0.0),
                    "heading": data.get("heading", 0.0),
                    "route": data.get("route", "R001"),
                    "vehicle_reg": data.get("vehicle_id", self.device_id),
                    "driver_id": f"drv-{self.device_id}",
                    "driver_name": {"first": "Real", "last": "Driver"},
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                
            # Option 2: CSV format (lat,lon,speed,heading)
            elif ',' in line:
                parts = line.split(',')
                if len(parts) >= 4:
                    return {
                        "lat": float(parts[0]),
                        "lon": float(parts[1]),
                        "speed": float(parts[2]),
                        "heading": float(parts[3]),
                        "route": "R001",
                        "vehicle_reg": self.device_id,
                        "driver_id": f"drv-{self.device_id}",
                        "driver_name": {"first": "Real", "last": "Driver"},
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                    
        except Exception as e:
            print(f"⚠️ Parse error: {e}")
            
        return None
        
    def stop(self):
        """Stop injection"""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()


class FileDataInjector:
    """
    Reads telemetry data from file and injects into buffer.
    Useful for testing with logged GPS data.
    """
    
    def __init__(self, rxtx_buffer, file_path: str, replay_speed: float = 1.0):
        self.buffer = rxtx_buffer
        self.file_path = file_path
        self.replay_speed = replay_speed
        self.running = False
        self.thread = None
        
    def start(self):
        """Start file replay"""
        self.running = True
        self.thread = threading.Thread(target=self._replay_file, daemon=True)
        self.thread.start()
        print(f"📁 File replay started: {self.file_path}")
        
    def _replay_file(self):
        """Replay file data into buffer"""
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    if not self.running:
                        break
                        
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            # Assume JSON format
                            gps_data = json.loads(line)
                            self.buffer.write(gps_data)
                            time.sleep(1.0 / self.replay_speed)  # Control replay speed
                            
                        except Exception as e:
                            print(f"⚠️ Line parse error: {e}")
                            
        except Exception as e:
            print(f"❌ File replay error: {e}")
            
    def stop(self):
        """Stop replay"""
        self.running = False


class NetworkDataInjector:
    """
    Receives telemetry data from network (UDP/TCP) and injects into buffer.
    For receiving data from external GPS tracking systems.
    """
    
    def __init__(self, rxtx_buffer, port: int = 5555):
        self.buffer = rxtx_buffer
        self.port = port
        self.running = False
        self.thread = None
        
    def start(self):
        """Start network listener"""
        self.running = True
        self.thread = threading.Thread(target=self._listen_udp, daemon=True)
        self.thread.start()
        print(f"🌐 Network listener started on port {self.port}")
        
    def _listen_udp(self):
        """Listen for UDP telemetry packets"""
        import socket
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('0.0.0.0', self.port))
            sock.settimeout(1.0)
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    message = data.decode('utf-8')
                    
                    # Parse and inject
                    gps_data = json.loads(message)
                    self.buffer.write(gps_data)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"⚠️ Network error: {e}")
                    
        except Exception as e:
            print(f"❌ Network setup error: {e}")
            
    def stop(self):
        """Stop listener"""
        self.running = False
