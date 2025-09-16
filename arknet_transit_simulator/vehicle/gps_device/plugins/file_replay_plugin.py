#!/usr/bin/env python3
"""
File Replay Telemetry Plugin
-----------------------------
Plugin for replaying telemetry data from recorded files.
Useful for testing, debugging, and data analysis scenarios.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, TextIO
from .interface import ITelemetryPlugin

logger = logging.getLogger(__name__)


class FileReplayTelemetryPlugin(ITelemetryPlugin):
    """
    File replay plugin for GPS device.
    
    Replays previously recorded telemetry data from JSON or CSV files.
    Supports various replay modes (realtime, fast, slow).
    """
    
    def __init__(self):
        self.file_path = None
        self.file_handle: Optional[TextIO] = None
        self.device_id = None
        self.replay_speed = 1.0
        self.loop_replay = False
        self._connected = False
        self._config = {}
        self._file_data = []
        self._current_index = 0
    
    @property
    def source_type(self) -> str:
        return "file_replay"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize file replay plugin.
        
        Config format:
        {
            "file_path": "/path/to/telemetry.json",
            "device_id": "REPLAY001",
            "replay_speed": 1.0,  # 1.0 = realtime, 2.0 = 2x speed, 0.5 = half speed
            "loop_replay": true,  # Loop file when reaching end
            "file_format": "json"  # "json" or "csv"
        }
        """
        try:
            self._config = config
            self.file_path = config.get("file_path")
            self.device_id = config.get("device_id", "REPLAY001")
            self.replay_speed = config.get("replay_speed", 1.0)
            self.loop_replay = config.get("loop_replay", False)
            self.file_format = config.get("file_format", "json")
            
            if not self.file_path:
                logger.error("File replay plugin requires 'file_path' in config")
                return False
            
            # Validate file exists and load data
            if not self._load_file_data():
                return False
            
            logger.info(f"File replay plugin initialized: {self.file_path} ({len(self._file_data)} records)")
            return True
            
        except Exception as e:
            logger.error(f"File replay plugin initialization failed: {e}")
            return False
    
    def _load_file_data(self) -> bool:
        """Load telemetry data from file."""
        try:
            with open(self.file_path, 'r') as f:
                if self.file_format == "json":
                    self._file_data = json.load(f)
                elif self.file_format == "csv":
                    # TODO: Implement CSV parsing
                    logger.error("CSV format not yet implemented")
                    return False
                else:
                    logger.error(f"Unsupported file format: {self.file_format}")
                    return False
            
            if not self._file_data:
                logger.error("File contains no telemetry data")
                return False
            
            return True
            
        except FileNotFoundError:
            logger.error(f"Telemetry file not found: {self.file_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in telemetry file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading telemetry file: {e}")
            return False
    
    def start_data_stream(self) -> bool:
        """Start file replay data stream."""
        try:
            self._connected = True
            self._current_index = 0
            logger.info(f"File replay stream started: {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to start file replay: {e}")
            return False
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Get next telemetry record from file.
        
        Returns data with timing based on replay speed.
        """
        if not self._connected or not self._file_data:
            return None
        
        try:
            # Check if we've reached end of file
            if self._current_index >= len(self._file_data):
                if self.loop_replay:
                    self._current_index = 0
                    logger.info("File replay looped to beginning")
                else:
                    logger.info("File replay completed")
                    return None
            
            # Get current record
            record = self._file_data[self._current_index]
            self._current_index += 1
            
            # Format record to standard telemetry format
            return self._format_record(record)
            
        except Exception as e:
            logger.warning(f"File replay data error: {e}")
            return None
    
    def _format_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Format file record to standard telemetry format."""
        try:
            # Handle different input formats
            formatted = {
                "lat": float(record.get("lat", record.get("latitude", 0.0))),
                "lon": float(record.get("lon", record.get("longitude", 0.0))),
                "speed": float(record.get("speed", 0.0)),
                "heading": float(record.get("heading", record.get("bearing", 0.0))),
                "timestamp": record.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "device_id": self.device_id,
                "route": str(record.get("route", "REPLAY_ROUTE")),
                "vehicle_reg": record.get("vehicle_reg", self.device_id),
                "driver_id": record.get("driver_id", f"drv-{self.device_id}"),
                "driver_name": record.get("driver_name", {"first": "Replay", "last": self.device_id}),
                "extras": {
                    "source": "file_replay",
                    "plugin_version": self.plugin_version,
                    "original_record": record,
                    "replay_index": self._current_index - 1
                }
            }
            
            return formatted
            
        except (ValueError, TypeError) as e:
            logger.warning(f"File record format error: {e}")
            return None
    
    def stop_data_stream(self) -> None:
        """Stop file replay."""
        self._connected = False
        logger.info("File replay stream stopped")
    
    def is_connected(self) -> bool:
        """Check if file replay is active."""
        return self._connected and bool(self._file_data)
