import os
import time
import threading
import asyncio
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from .rxtx_buffer import RxTxBuffer
from .radio_module.transmitter import WebSocketTransmitter
from .radio_module.packet import TelemetryPacket, PacketCodec, make_packet
from .plugins.manager import PluginManager

load_dotenv()
logger = logging.getLogger(__name__)


class GPSDevice:
    """
    Plugin-based GPS device with agnostic data sources.
    
    Supports multiple telemetry sources:
    - Simulation data for development
    - ESP32 hardware with secure boot
    - File replay for testing
    - Any future sources via plugins
    
    Architecture:
      - Plugin provides telemetry data
      - Internal worker polls plugin and writes to buffer
      - Transmitter reads from buffer and sends to server
    """

    def __init__(
        self, 
        device_id: str, 
        ws_transmitter: WebSocketTransmitter,
        plugin_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize GPS device with plugin system.
        
        Args:
            device_id: Unique identifier for this device
            ws_transmitter: WebSocket transmitter for sending data
            plugin_config: Configuration for telemetry plugin
        """
        self.device_id = device_id
        self.transmitter = ws_transmitter
        
        # Buffer for data exchange
        self.rxtx_buffer = RxTxBuffer()
        
        # Thread management
        self._stop = threading.Event()
        self.transmitter_thread = None
        self.data_thread = None
        
        # Plugin management
        self.plugin_manager = PluginManager()
        
        # Set up plugin if config provided
        if plugin_config:
            if not self._setup_plugin(plugin_config):
                logger.warning(f"Failed to setup plugin for device {device_id}")
        
        logger.info(f"GPSDevice {device_id} initialized")
    
    def _setup_plugin(self, plugin_config: Dict[str, Any]) -> bool:
        """
        Set up the telemetry plugin based on configuration.
        
        Args:
            plugin_config: Configuration dictionary containing plugin type and parameters
            
        Returns:
            bool: True if plugin setup successful, False otherwise
        """
        try:
            plugin_type = plugin_config.get("type", "simulation")
            
            # Load plugin based on type
            if self.plugin_manager.load_plugin(plugin_type, plugin_config):
                logger.info(f"Loaded {plugin_type} plugin for device {self.device_id}")
                return True
            else:
                logger.error(f"Failed to load {plugin_type} plugin for device {self.device_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up plugin for device {self.device_id}: {e}")
            return False

    # -------------------- Data Collection Worker --------------------
    
    def _data_worker(self):
        """Worker thread that collects data from plugin and writes to buffer."""
        logger.info(f"GPS device {self.device_id} data worker started")
        
        while not self._stop.is_set():
            try:
                # Get data from active plugin
                telemetry_data = self.plugin_manager.get_data()
                
                if telemetry_data:
                    # Write to buffer for transmission
                    self.rxtx_buffer.write(telemetry_data)
                
                # Get interval from plugin, fallback to 1.0 seconds
                interval = 1.0
                if self.plugin_manager.active_plugin and hasattr(self.plugin_manager.active_plugin, 'update_interval'):
                    interval = getattr(self.plugin_manager.active_plugin, 'update_interval', 1.0)
                
                # Sleep according to plugin interval
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in data worker for {self.device_id}: {e}")
                time.sleep(1.0)  # Wait longer on error
        
        logger.info(f"GPS device {self.device_id} data worker stopped")

    # -------------------- Transmitter Worker --------------------
    
    def _transmitter_worker(self):
        """Worker thread that runs asyncio loop for WebSocket transmission."""
        asyncio.run(self._async_transmitter())

    async def _async_transmitter(self):
        """Async worker: connect once, then send packets."""
        try:
            # Connect the existing transmitter
            await self.transmitter.connect()
            logger.info(f"GPS device {self.device_id} transmitter connected")

            # Continuously read from buffer and send
            while not self._stop.is_set():
                try:
                    # Read data from buffer with timeout
                    data = await asyncio.to_thread(self.rxtx_buffer.read, timeout=1.0)
                    
                    if self._stop.is_set():
                        break
                    
                    if data:
                        # Convert dictionary data to TelemetryPacket
                        from .radio_module.packet import make_packet
                        
                        if isinstance(data, dict):
                            # Create packet from dictionary data
                            packet = make_packet(
                                device_id=data.get("device_id", self.device_id),
                                lat=float(data.get("lat", 0.0)),
                                lon=float(data.get("lon", 0.0)),
                                speed=float(data.get("speed", 0.0)),
                                heading=float(data.get("heading", 0.0)),
                                route=str(data.get("route", "0")),
                                vehicle_reg=data.get("vehicle_reg", self.device_id),
                                driver_id=data.get("driver_id", f"sim-{self.device_id}"),
                                driver_name=data.get("driver_name", {"first": "Sim", "last": self.device_id}),
                                ts=data.get("timestamp")
                            )
                            # Send packet via transmitter
                            await self.transmitter.send(packet)
                        else:
                            # Assume it's already a TelemetryPacket
                            await self.transmitter.send(data)
                        
                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    continue
                except Exception as e:
                    logger.error(f"Error in transmitter for {self.device_id}: {e}")
                    await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"Transmitter connection failed for {self.device_id}: {e}")
        
        finally:
            try:
                await self.transmitter.close()
                logger.info(f"GPS device {self.device_id} transmitter disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting transmitter for {self.device_id}: {e}")

    # -------------------- Lifecycle --------------------

    def on(self):
        """Turn on device (start plugin, data worker, and transmitter)."""
        if (self.transmitter_thread and self.transmitter_thread.is_alive()) or \
           (self.data_thread and self.data_thread.is_alive()):
            return
        
        try:
            # Start plugin data stream
            if not self.plugin_manager.start_data_stream():
                logger.error(f"Failed to start plugin data stream for {self.device_id}")
                return
            
            self._stop.clear()
            
            # Start data collection worker
            self.data_thread = threading.Thread(target=self._data_worker, daemon=True)
            self.data_thread.start()
            
            # Start transmitter worker
            self.transmitter_thread = threading.Thread(target=self._transmitter_worker, daemon=True)
            self.transmitter_thread.start()
            
            logger.info(f"GPSDevice for {self.device_id} turned ON")
            
        except Exception as e:
            logger.error(f"Failed to start GPS device {self.device_id}: {e}")

    def off(self):
        """Turn off device (stop workers, plugin, and close transmitter)."""
        # Signal stop
        self._stop.set()

        # Stop plugin data stream
        try:
            self.plugin_manager.unload_current_plugin()
        except Exception as e:
            logger.warning(f"Error stopping plugin: {e}")

        # Ask transmitter to close to unblock any pending I/O in the event loop
        try:
            if self.transmitter and hasattr(self.transmitter, "request_close"):
                self.transmitter.request_close()
        except Exception:
            pass

        # Stop data worker thread
        if self.data_thread:
            self.data_thread.join(timeout=2.0)
            if self.data_thread.is_alive():
                logger.warning(f"Data worker for {self.device_id} did not stop in 2s")

        # Stop transmitter thread  
        if self.transmitter_thread:
            self.transmitter_thread.join(timeout=5.0)
            if self.transmitter_thread.is_alive():
                logger.warning(f"Transmitter for {self.device_id} did not stop in 5s; forcing close")
                try:
                    if self.transmitter and hasattr(self.transmitter, "force_close"):
                        self.transmitter.force_close()
                except Exception:
                    pass
                self.transmitter_thread.join(timeout=2.0)
            
            self.transmitter_thread = None
            self.data_thread = None

        logger.info(f"GPSDevice for {self.device_id} turned OFF")
    
    # -------------------- Plugin Management --------------------
    
    def switch_plugin(self, plugin_config: Dict[str, Any]) -> bool:
        """
        Switch to a different telemetry plugin at runtime.
        
        Args:
            plugin_config: New plugin configuration
            
        Returns:
            bool: True if switch successful, False otherwise
        """
        try:
            # Stop current plugin
            self.plugin_manager.unload_current_plugin()
            
            # Load new plugin
            if self._setup_plugin(plugin_config):
                # Restart data stream if device is active
                if not self._stop.is_set():
                    self.plugin_manager.start_data_stream()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Plugin switch failed for {self.device_id}: {e}")
            return False
    
    def get_plugin_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active plugin."""
        return self.plugin_manager.get_active_plugin_info()
    
    def set_vehicle_state(self, vehicle_state):
        """Set vehicle state for simulation plugin (if active)."""
        if self.plugin_manager.active_plugin and hasattr(self.plugin_manager.active_plugin, 'set_vehicle_state'):
            self.plugin_manager.active_plugin.set_vehicle_state(vehicle_state)
