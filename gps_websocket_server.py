#!/usr/bin/env python3
"""
Simple WebSocket Server for GPS Telemetry Testing
"""

import asyncio
import websockets
import json
from urllib.parse import parse_qs, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPSWebSocketServer:
    def __init__(self, host="localhost", port=5001):  # Use different port to avoid conflict
        self.host = host
        self.port = port
        self.clients = {}

    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connection"""
        try:
            # Parse the path and query parameters
            parsed_url = urlparse(path)
            query_params = parse_qs(parsed_url.query)
            
            device_id = query_params.get('deviceId', ['unknown'])[0]
            token = query_params.get('token', [''])[0]
            
            logger.info(f"🔌 New GPS device connected: {device_id}")
            logger.info(f"   Path: {path}")
            logger.info(f"   Token: {token}")
            
            # Store client
            client_key = f"{device_id}_{id(websocket)}"
            self.clients[client_key] = {
                'websocket': websocket,
                'device_id': device_id,
                'token': token,
                'message_count': 0
            }
            
            # Listen for messages
            async for message in websocket:
                try:
                    # Parse GPS telemetry data
                    if isinstance(message, str):
                        data = json.loads(message)
                    else:
                        data = json.loads(message.decode('utf-8'))
                    
                    # Update message count
                    self.clients[client_key]['message_count'] += 1
                    count = self.clients[client_key]['message_count']
                    
                    # Log GPS data
                    logger.info(f"📍 GPS Data from {device_id} (#{count}):")
                    logger.info(f"   Lat: {data.get('lat', 'N/A')}")
                    logger.info(f"   Lon: {data.get('lon', 'N/A')}")
                    logger.info(f"   Speed: {data.get('speed', 'N/A')} km/h")
                    logger.info(f"   Heading: {data.get('heading', 'N/A')}°")
                    logger.info(f"   Route: {data.get('route', 'N/A')}")
                    logger.info(f"   Vehicle: {data.get('vehicle_reg', device_id)}")
                    logger.info(f"   Timestamp: {data.get('ts', data.get('timestamp', 'N/A'))}")
                    
                    # Send acknowledgment back
                    response = {
                        "status": "received",
                        "device_id": device_id,
                        "message_count": count,
                        "timestamp": data.get('ts', data.get('timestamp'))
                    }
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON from {device_id}: {e}")
                except Exception as e:
                    logger.error(f"❌ Error processing message from {device_id}: {e}")
                    
        except websockets.exceptions.ConnectionClosedOK:
            logger.info(f"🔌 GPS device {device_id} disconnected normally")
        except websockets.exceptions.ConnectionClosedError:
            logger.warning(f"⚠️ GPS device {device_id} disconnected with error")
        except Exception as e:
            logger.error(f"❌ Error handling client {device_id}: {e}")
        finally:
            # Clean up client
            if client_key in self.clients:
                del self.clients[client_key]
                logger.info(f"🧹 Cleaned up client: {device_id}")

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"🚀 Starting GPS WebSocket Server on {self.host}:{self.port}")
        logger.info(f"📡 Expected URL format: ws://{self.host}:{self.port}/device?deviceId=DEVICE_ID&token=TOKEN")
        
        # Start server on /device endpoint
        async with websockets.serve(
            lambda ws, path: self.handle_client(ws, path),
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        ):
            logger.info(f"✅ Server is listening on ws://{self.host}:{self.port}")
            logger.info("📊 Waiting for GPS devices to connect...")
            
            # Keep server running
            await asyncio.Future()  # Run forever

def main():
    """Main entry point"""
    server = GPSWebSocketServer()
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()
