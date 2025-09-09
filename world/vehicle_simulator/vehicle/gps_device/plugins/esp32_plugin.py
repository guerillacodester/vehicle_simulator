#!/usr/bin/env python3
"""
ESP32 Hardware Telemetry Plugin
-------------------------------
Plugin for real ESP32 hardware with secure boot telemetry.
Handles encrypted GPS data from ESP32 devices connected via serial/USB.
"""

import time
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .interface import ITelemetryPlugin

logger = logging.getLogger(__name__)

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logger.warning("pyserial not available - ESP32 plugin will not function")


class ESP32TelemetryPlugin(ITelemetryPlugin):
    """
    ESP32 hardware plugin for GPS device.
    
    Handles secure boot encrypted telemetry from ESP32 devices.
    Supports serial/USB communication with decryption capabilities.
    """
    
    def __init__(self):
        self.serial_port = None
        self.baud_rate = 115200
        self.encryption_key = None
        self.device_id = None
        self.serial_conn = None
        self._connected = False
        self._config = {}
    
    @property
    def source_type(self) -> str:
        return "esp32_hardware"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize ESP32 hardware plugin.
        
        Config format:
        {
            "serial_port": "/dev/ttyUSB0",
            "baud_rate": 115200,
            "encryption_key": "secure_key_here",
            "device_id": "BUS001",
            "timeout": 5.0
        }
        """
        try:
            if not SERIAL_AVAILABLE:
                logger.error("ESP32 plugin requires pyserial: pip install pyserial")
                return False
            
            self._config = config
            self.serial_port = config.get("serial_port", "/dev/ttyUSB0")
            self.baud_rate = config.get("baud_rate", 115200)
            self.encryption_key = config.get("encryption_key")
            self.device_id = config.get("device_id", "ESP32_001")
            self.timeout = config.get("timeout", 5.0)
            
            if not self.encryption_key:
                logger.warning("ESP32 plugin: No encryption key provided")
            
            logger.info(f"ESP32 plugin initialized for device: {self.device_id} on {self.serial_port}")
            return True
            
        except Exception as e:
            logger.error(f"ESP32 plugin initialization failed: {e}")
            return False
    
    def start_data_stream(self) -> bool:
        """Start ESP32 serial connection."""
        try:
            if not SERIAL_AVAILABLE:
                return False
            
            self.serial_conn = serial.Serial(
                self.serial_port,
                self.baud_rate,
                timeout=self.timeout
            )
            
            # Test connection
            if self.serial_conn.is_open:
                self._connected = True
                logger.info(f"ESP32 serial connection established: {self.serial_port}")
                return True
            else:
                logger.error("ESP32 serial connection failed to open")
                return False
                
        except Exception as e:
            logger.error(f"ESP32 connection failed: {e}")
            return False
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Get telemetry data from ESP32 device.
        
        Reads encrypted data, decrypts it, and returns in standard format.
        """
        if not self._connected or not self.serial_conn:
            return None
        
        try:
            # Read line from ESP32
            if self.serial_conn.in_waiting > 0:
                raw_data = self.serial_conn.readline().decode('utf-8').strip()
                
                if raw_data:
                    # Parse JSON data from ESP32
                    esp32_data = json.loads(raw_data)
                    
                    # Decrypt if encrypted
                    if self.encryption_key and esp32_data.get("encrypted"):
                        esp32_data = self._decrypt_esp32_data(esp32_data)
                    
                    # Convert to standard telemetry format
                    return self._format_gps_data(esp32_data)
            
            return None
            
        except json.JSONDecodeError as e:
            logger.warning(f"ESP32 JSON decode error: {e}")
            return None
        except Exception as e:
            logger.warning(f"ESP32 data read error: {e}")
            return None
    
    def _decrypt_esp32_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt secure boot data from ESP32.
        
        TODO: Implement actual encryption/decryption based on ESP32 secure boot.
        This is a placeholder for the real implementation.
        """
        # Placeholder - implement actual decryption
        logger.info("ESP32 decryption placeholder - implement real decryption")
        return encrypted_data.get("payload", encrypted_data)
    
    def _format_gps_data(self, esp32_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ESP32 format to standard telemetry format."""
        try:
            return {
                "lat": float(esp32_data.get("latitude", 0.0)),
                "lon": float(esp32_data.get("longitude", 0.0)),
                "speed": float(esp32_data.get("speed_kmh", 0.0)),
                "heading": float(esp32_data.get("bearing", 0.0)),
                "timestamp": esp32_data.get("gps_timestamp", datetime.now(timezone.utc).isoformat()),
                "device_id": self.device_id,
                "route": str(esp32_data.get("route", "HW_ROUTE")),
                "vehicle_reg": self.device_id,
                "driver_id": esp32_data.get("driver_id", f"drv-{self.device_id}"),
                "driver_name": esp32_data.get("driver_name", {"first": "Hardware", "last": self.device_id}),
                "extras": {
                    "source": "esp32_hardware",
                    "plugin_version": self.plugin_version,
                    "security_hash": esp32_data.get("secure_hash"),
                    "hardware_info": esp32_data.get("hardware_info")
                }
            }
        except (ValueError, TypeError) as e:
            logger.warning(f"ESP32 data format error: {e}")
            return None
    
    def stop_data_stream(self) -> None:
        """Stop ESP32 serial connection."""
        self._connected = False
        if self.serial_conn:
            try:
                self.serial_conn.close()
                logger.info(f"ESP32 serial connection closed: {self.serial_port}")
            except Exception as e:
                logger.warning(f"Error closing ESP32 connection: {e}")
            finally:
                self.serial_conn = None
    
    def is_connected(self) -> bool:
        """Check if ESP32 is connected and responding."""
        return (self._connected and 
                self.serial_conn and 
                self.serial_conn.is_open)
