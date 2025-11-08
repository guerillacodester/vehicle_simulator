"""
Socket.IO server integration for the launcher service.
"""
from fastapi import FastAPI
import socketio
from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

# Create Socket.IO instance with CORS support
# Tuned for immediate disconnect detection: 5s ping interval, 10s timeout
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True,
    ping_timeout=10,  # Reduced to 10s for faster stale connection detection
    ping_interval=5   # Ping every 5s to quickly spot dead connections
)

# Create ASGI app (not used directly, but kept for compatibility)
socket_app = socketio.ASGIApp(
    sio,
    socketio_path='socket.io'
)

# Authentication middleware
@sio.event
async def connect(sid, environ, auth):
    """Handle client connection with authentication."""
    try:
        # Socket.IO v5 passes auth as third parameter
        token = None
        if auth and isinstance(auth, dict):
            token = auth.get('token')
        
        # For development, accept any connection
        # TODO: Implement proper authentication in production
        logger.info(f"Client {sid} connected (token: {token})")
        await sio.emit('connection_status', {'status': 'connected'}, room=sid)
        
        # Send current service statuses to the newly connected client
        try:
            from launcher.service_manager import manager
            from datetime import datetime
            for service in manager.services.values():
                event = {
                    'service_name': service.name,
                    'timestamp': datetime.utcnow().isoformat(),
                    'state': service.state.value,
                    'message': f'Current state: {service.state.value}',
                    'port': service.port,
                    'pid': service.process.pid if service.process else None
                }
                await sio.emit('service_status', event, room=sid)
        except Exception as e:
            logger.error(f"Error sending initial service statuses: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error in connect handler: {e}")
        return False

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client {sid} disconnected")

@sio.event
async def error(sid, error_data):
    """Handle connection errors."""
    logger.error(f"Error for client {sid}: {error_data}")

# Service status events
@sio.event
async def service_status(sid, data: Dict[str, Any]):
    """Broadcast service status updates."""
    try:
        # Validate data
        if not isinstance(data, dict) or 'service_name' not in data:
            logger.error(f"Invalid service status data from {sid}: {data}")
            return
        
        # Broadcast to all connected clients
        await sio.emit('service_status', data)
        logger.debug(f"Broadcasted status for service {data['service_name']}")
    
    except Exception as e:
        logger.error(f"Error broadcasting service status: {e}")

@sio.event
async def service_command(sid, data: Dict[str, Any]):
    """Handle service control commands."""
    try:
        service_name = data.get('service_name')
        command = data.get('command')
        
        if not service_name or not command:
            await sio.emit('error', {'message': 'Invalid command data'}, room=sid)
            return
        
        # TODO: Integrate with service control logic
        logger.info(f"Received {command} command for {service_name} from {sid}")
        
        # Echo back acknowledgment
        await sio.emit('command_received', {
            'service_name': service_name,
            'command': command,
            'status': 'acknowledged'
        }, room=sid)
    
    except Exception as e:
        logger.error(f"Error handling service command: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

# Heartbeat handlers
@sio.event
async def dashboard_heartbeat(sid, data: Dict[str, Any]):
    """Respond to dashboard heartbeat with an ack so the client can detect liveness without UI churn."""
    try:
        ts = None
        if isinstance(data, dict):
            ts = data.get('ts')
        await sio.emit('dashboard_heartbeat_ack', {'ts': ts}, room=sid)
    except Exception as e:
        logger.error(f"Error handling dashboard_heartbeat: {e}")

def setup_socketio(app: FastAPI):
    """Mount Socket.IO server to FastAPI application."""
    app.mount('/', socket_app)