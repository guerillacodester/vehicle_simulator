#!/usr/bin/env python3
"""
Simple WebSocket Telemetry Server
---------------------------------
Basic WebSocket server to receive and display GPS telemetry packets.
Run this first, then run the GPS test to see the packets arrive.
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class TelemetryServer:
    def __init__(self, host="localhost", port=5000):
        self.host = host
        self.port = port
        self.clients = set()
        self.packet_count = 0
        
    async def register_client(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"📱 GPS device connected: {client_info}")
        logger.info(f"🔢 Total connected devices: {len(self.clients)}")
        
    async def unregister_client(self, websocket):
        """Unregister a client connection"""
        self.clients.remove(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"📱 GPS device disconnected: {client_info}")
        logger.info(f"🔢 Total connected devices: {len(self.clients)}")
        
    async def handle_client(self, websocket, path):
        """Handle a WebSocket client connection"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                await self.process_telemetry(message, websocket)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 GPS device connection closed normally")
        except Exception as e:
            logger.error(f"❌ Error handling GPS device: {e}")
        finally:
            await self.unregister_client(websocket)
            
    async def process_telemetry(self, message, websocket):
        """Process incoming telemetry data"""
        try:
            self.packet_count += 1
            client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            
            # Try to parse as JSON
            try:
                data = json.loads(message)
                logger.info(f"📡 TELEMETRY PACKET #{self.packet_count} from {client_info}")
                logger.info(f"   🆔 Device: {data.get('deviceId', 'unknown')}")
                logger.info(f"   📍 Location: {data.get('lat', 0):.6f}, {data.get('lon', 0):.6f}")
                logger.info(f"   🚗 Speed: {data.get('speed', 0)} km/h")
                logger.info(f"   🧭 Heading: {data.get('heading', 0)}°")
                logger.info(f"   🛣️ Route: {data.get('route', 'unknown')}")
                logger.info(f"   🚌 Vehicle: {data.get('vehicleReg', 'unknown')}")
                logger.info(f"   ⏰ Time: {data.get('timestamp', 'unknown')}")
                
                # Extract driver info if present
                driver_name = data.get('driverName', {})
                if isinstance(driver_name, dict):
                    driver_display = f"{driver_name.get('first', '')} {driver_name.get('last', '')}"
                else:
                    driver_display = str(driver_name)
                logger.info(f"   👨‍✈️ Driver: {driver_display}")
                
            except json.JSONDecodeError:
                # Handle non-JSON messages (might be binary)
                logger.info(f"📡 RAW PACKET #{self.packet_count} from {client_info}")
                logger.info(f"   📦 Length: {len(message)} bytes")
                logger.info(f"   📄 Content: {message[:100]}{'...' if len(message) > 100 else ''}")
                
            logger.info("   " + "="*50)
            
        except Exception as e:
            logger.error(f"❌ Error processing telemetry: {e}")
            
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"🚀 Starting GPS Telemetry Server...")
        logger.info(f"🔗 WebSocket URL: ws://{self.host}:{self.port}")
        logger.info(f"⏳ Waiting for GPS device connections...")
        logger.info("   " + "="*50)
        
        # Start WebSocket server
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info(f"✅ Server listening on ws://{self.host}:{self.port}")
        
        # Keep server running
        await server.wait_closed()

async def main():
    """Main function"""
    print("🛰️ GPS TELEMETRY WEBSOCKET SERVER")
    print("=" * 50)
    print("This server receives and displays GPS telemetry packets.")
    print("Run your GPS test scripts to send packets here.\n")
    
    server = TelemetryServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())