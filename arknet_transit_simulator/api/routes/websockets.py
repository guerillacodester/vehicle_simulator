"""WebSocket endpoints for real-time event streaming."""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set

from ..dependencies import get_event_bus
from ..events.event_bus import EventBus

router = APIRouter(tags=["websockets"])

# Track active websocket connections
active_connections: Set[WebSocket] = set()


@router.websocket("/ws/events")
async def events_websocket(websocket: WebSocket, event_bus: EventBus = Depends(get_event_bus)):
    """Stream real-time events to connected clients."""
    await websocket.accept()
    active_connections.add(websocket)
    
    # Subscribe to all events
    subscription_id = "websocket_" + str(id(websocket))
    event_queue = event_bus.subscribe(subscription_id)
    
    try:
        # Background task to send events from queue to websocket
        while True:
            # Get next event from queue
            event = await event_queue.get()
            
            # Serialize event to JSON
            event_data = {
                "event_type": event.event_type.value,
                "vehicle_id": event.vehicle_id,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "data": event.data
            }
            
            # Send to websocket
            await websocket.send_json(event_data)
            
    except WebSocketDisconnect:
        # Client disconnected
        active_connections.remove(websocket)
        event_bus.unsubscribe(subscription_id)
    except Exception as e:
        # Error occurred
        print(f"WebSocket error: {e}")
        active_connections.remove(websocket)
        event_bus.unsubscribe(subscription_id)


@router.get("/ws/status")
async def websocket_status():
    """Get current WebSocket connection status."""
    return {
        "active_connections": len(active_connections),
        "endpoints": ["/ws/events"]
    }
