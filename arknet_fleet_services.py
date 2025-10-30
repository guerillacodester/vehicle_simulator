"""
ArkNet Fleet Services API
==========================

Production-grade unified backend consolidating all HTTP services into a single FastAPI application:
- GeospatialService (PostGIS spatial queries) → /geo/*
- GPSCentCom Server (GPS telemetry hub) → /gps/*
- Passenger Manifest API (enriched listings) → /manifest/*

This is the primary entrypoint for starting all HTTP services.
Each service maintains its own routers, middleware, and lifecycle events.

Usage:
    # Recommended: Launch in separate console (non-blocking)
    python start_fleet_services.py
    
    # Alternative: Run directly (blocks current terminal)
    python arknet_fleet_services.py
    
    # Production
    uvicorn arknet_fleet_services:app --host 0.0.0.0 --port 8000 --workers 4

Benefits:
- Single port configuration (port 8000)
- Single deployment unit (1 process instead of 3)
- Shared connection pools and resources
- One API base URL for all clients
- Reduced operational complexity
- Unified CORS policy

Architecture:
- Background simulators (vehicle, commuter) remain separate processes
- This backend serves all HTTP APIs
- PostgreSQL + PostGIS remains separate service
- Strapi remains separate service (port 1337)

Deployment Model:
    4-5 processes total:
    1. Unified Backend (this file) - port 8000
    2. Vehicle Simulator (background process)
    3. Commuter Simulator (background process)
    4. PostgreSQL + PostGIS
    5. Strapi (optional for admin)
"""

import asyncio
import json
import os
import sys
import time
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse


def _load_geospatial_app():
    """Load GeospatialService with proper path context."""
    import sys
    from pathlib import Path
    
    geo_path = str(Path(__file__).parent / "geospatial_service")
    old_path = sys.path.copy()
    
    try:
        # Temporarily modify sys.path
        sys.path.insert(0, geo_path)
        
        # Import within context
        import main
        return main.app
    finally:
        # Restore sys.path
        sys.path = old_path


def _load_gpscentcom_app():
    """
    Load GPSCentCom Server with proper path context.
    
    Creates a minimal FastAPI app from GPSCentCom without requiring config file.
    """
    import sys
    import os
    from pathlib import Path
    
    gps_path = str(Path(__file__).parent / "gpscentcom_server")
    old_path = sys.path.copy()
    
    try:
        # Temporarily modify sys.path
        sys.path.insert(0, gps_path)
        
        # Remove conflicting modules if they exist
        conflicting = [k for k in sys.modules.keys() if k in ('config', 'api', 'services')]
        for mod in conflicting:
            sys.modules.pop(mod, None)
        
        # Import FastAPI and dependencies
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
        from fastapi.requests import Request
        from pydantic import ValidationError
        from fastapi.exceptions import RequestValidationError
        
        # Import GPSCentCom modules
        from store import Store
        from connection_manager import DeviceConnectionManager
        from rx_handler import device_router
        from api_router import api_router
        from error_codes import ErrorRegistry
        
        # Create app without build_app() to avoid config file requirement
        app = FastAPI(title="gpscentcom_server", version="0.2.0")
        
        # Enable packet logging
        app.state.log_packets = False  # Default to false
        
        # Get AUTH_TOKEN from environment (required)
        auth_token = os.getenv("AUTH_TOKEN", "dev-token-change-in-production")
        stale_after = int(os.getenv("STALE_AFTER_SEC", "120"))
        
        # CORS
        raw_origins = os.getenv("CORS_ORIGINS", "")
        cors_origins = [o.strip(" '\"") for o in raw_origins.split(",") if o.strip()]
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Error handling
        @app.exception_handler(RequestValidationError)
        async def request_validation_handler(request: Request, exc: RequestValidationError):
            err = ErrorRegistry.CODEC_DECODE_FAIL
            return JSONResponse(status_code=400, content=ErrorRegistry.format(err))
        
        @app.exception_handler(ValidationError)
        async def validation_exception_handler(request: Request, exc: ValidationError):
            err = ErrorRegistry.CODEC_DECODE_FAIL
            return JSONResponse(status_code=400, content=ErrorRegistry.format(err))
        
        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            err = ErrorRegistry.UNKNOWN_ERROR
            return JSONResponse(status_code=500, content=ErrorRegistry.format(err))
        
        # Shared state
        app.state.auth_token = auth_token
        app.state.store = Store(stale_after=stale_after)
        app.state.manager = DeviceConnectionManager()
        app.state.start_time = time.time()
        
        # Routers
        # NOTE: device_router (WebSocket /device) is NOT included here
        # because WebSockets don't work properly through app.mount().
        # Instead, we define a direct WebSocket route in the parent app.
        # app.include_router(device_router, prefix="")  # EXCLUDED
        app.include_router(api_router)  # HTTP routes only
        
        # Background janitor task
        @app.on_event("startup")
        async def startup_event():
            async def janitor():
                while True:
                    await asyncio.sleep(30)
                    try:
                        await app.state.store.prune_stale()
                    except Exception:
                        pass
            asyncio.create_task(janitor())
        
        return app
        
    finally:
        # Restore sys.path
        sys.path = old_path


def _load_manifest_app():
    """Load Manifest API (clean architecture - no path issues)."""
    from commuter_simulator.interfaces.http.manifest_api import app as manifest_app
    return manifest_app


# Load all services
print("📦 Loading GeospatialService...")
try:
    geospatial_app = _load_geospatial_app()
    print("   ✅ GeospatialService loaded")
except Exception as e:
    print(f"   ❌ Failed to load GeospatialService: {e}")
    geospatial_app = None

print("📦 Loading GPSCentCom Server...")
try:
    gpscentcom_app = _load_gpscentcom_app()
    print("   ✅ GPSCentCom Server loaded")
except Exception as e:
    print(f"   ❌ Failed to load GPSCentCom Server: {e}")
    gpscentcom_app = None

print("📦 Loading Manifest API...")
try:
    manifest_app = _load_manifest_app()
    print("   ✅ Manifest API loaded")
except Exception as e:
    print(f"   ❌ Failed to load Manifest API: {e}")
    manifest_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Unified startup and shutdown for all services.
    
    Note: Each mounted sub-app has its own lifespan context manager.
    This handles the unified backend lifecycle.
    """
    # Startup
    print("=" * 70)
    print("🚀 Starting ArkNet Unified Backend...")
    print("=" * 70)
    
    app.state.start_time = time.time()
    
    print("\n✅ Mounted Services:")
    print("   📍 /geo/*       - Geospatial Service (reverse geocoding, geofencing)")
    print("   📍 /gps/*       - GPSCentCom Server (device telemetry)")
    print("   📍 /manifest/*  - Manifest API (passenger enrichment)")
    print("\n✅ Unified Backend ready on port 8000!")
    print("=" * 70)
    
    yield
    
    # Shutdown
    print("\n" + "=" * 70)
    print("🛑 Shutting down ArkNet Unified Backend...")
    uptime = time.time() - app.state.start_time
    print(f"   Total uptime: {uptime:.1f} seconds")
    print("✅ Shutdown complete")
    print("=" * 70)


# Create unified FastAPI application
app = FastAPI(
    title="ArkNet Unified Backend",
    description=(
        "Consolidated HTTP API serving geospatial, GPS telemetry, and manifest services. "
        "Mounts existing FastAPI applications without recoding."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Global CORS middleware for unified backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# CRITICAL: Define WebSocket route BEFORE mounting apps!
# FastAPI's app.mount() catches all sub-paths, so specific routes must be
# defined first. WebSockets don't work properly through mount anyway.
# ============================================================================
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/gps/device")
async def gps_device_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for GPS devices (proxied to GPSCentCom handler).
    
    This is a direct route because FastAPI's app.mount() doesn't properly
    support WebSocket connections in sub-applications.
    
    Simply delegates to the GPSCentCom connection manager using its public API.
    """
    try:
        client_host = websocket.client.host if websocket.client else "unknown"
        device_id = websocket.query_params.get("deviceId", "unknown")
        print(f"\n{'='*70}")
        print(f"🔌 WebSocket connection attempt from {client_host} for device {device_id}")
        print(f"   Query params: {dict(websocket.query_params)}")
        print(f"{'='*70}\n")
        
        # Validate GPS service is available
        if not gpscentcom_app:
            print(f"❌ GPS service not available - rejecting connection")
            await websocket.close(code=1011, reason="GPS service not available")
            return
        
        # Inject app state into websocket so manager can access store
        websocket.app = gpscentcom_app
        
        # Get manager from GPS app state
        manager = gpscentcom_app.state.manager
        
        # Use the manager's public connect() API (it handles accept + registration)
        try:
            await manager.connect(websocket, device_id)
            print(f"✅ Device {device_id} connected and registered")
        except Exception as e:
            print(f"❌ Failed to connect device {device_id}: {e}")
            import traceback
            traceback.print_exc()
            return
    except Exception as e:
        print(f"❌ CRITICAL: WebSocket handler crashed before connection: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    try:
        while True:
            message = await websocket.receive()
            
            # Handle ping/pong
            if message.get("type") == "websocket.ping":
                await websocket.send({"type": "websocket.pong"})
                continue
            
            if message.get("type") == "websocket.pong":
                continue
            
            # Handle text message (JSON telemetry)
            if message["type"] == "websocket.receive" and "text" in message:
                data_str = message["text"]
                try:
                    data = json.loads(data_str) if isinstance(data_str, str) else data_str
                    await manager.handle_message(websocket, data)
                except json.JSONDecodeError:
                    pass
            
            # Handle binary message
            elif message["type"] == "websocket.receive" and "bytes" in message:
                pass  # Binary codec support if needed
            
            # Handle disconnect
            elif message["type"] == "websocket.disconnect":
                break
                
    except WebSocketDisconnect:
        print(f"🔌 Device {device_id} disconnected normally")
    except Exception as e:
        print(f"❌ WebSocket error for device {device_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await manager.disconnect(websocket)
        except:
            pass


# ============================================================================
# Mount existing services as sub-applications
# Each maintains its own routers, middleware, and lifecycle
# ============================================================================

if geospatial_app:
    app.mount("/geo", geospatial_app)
    print("   ✅ Mounted at /geo")
else:
    print("   ⚠️  GeospatialService not available")

if gpscentcom_app:
    app.mount("/gps", gpscentcom_app)
    print("   ✅ Mounted at /gps")
else:
    print("   ⚠️  GPSCentCom Server not available")

if manifest_app:
    app.mount("/manifest", manifest_app)
    print("   ✅ Mounted at /manifest")
else:
    print("   ⚠️  Manifest API not available")


# ============================================================================
# Server-Sent Events (SSE) endpoint for clients to receive real-time telemetry
# ============================================================================
from fastapi.responses import StreamingResponse

@app.get("/gps/stream")
async def gps_telemetry_stream(
    device_id: str = None,
    route_code: str = None
):
    """
    Server-Sent Events (SSE) endpoint for clients to receive real-time GPS telemetry.
    
    This allows dashboard/monitoring clients to subscribe to live telemetry updates
    without polling. Data is pushed from server to client as it arrives.
    
    Query Parameters:
        device_id (optional): Filter to specific device
        route_code (optional): Filter to devices on specific route
    
    Usage:
        JavaScript (Browser):
            const eventSource = new EventSource('http://localhost:8000/gps/stream');
            eventSource.onmessage = (event) => {
                const telemetry = JSON.parse(event.data);
                console.log('Received telemetry:', telemetry);
            };
        
        Python:
            import requests
            response = requests.get('http://localhost:8000/gps/stream', stream=True)
            for line in response.iter_lines():
                if line.startswith(b'data:'):
                    telemetry = json.loads(line[5:])
                    print(telemetry)
    
    Returns:
        Stream of telemetry updates in SSE format (text/event-stream)
    """
    if not gpscentcom_app:
        return JSONResponse(
            status_code=503,
            content={"error": "GPS service not available"}
        )
    
    async def event_generator():
        """Generate SSE events from GPS telemetry store."""
        store = gpscentcom_app.state.store
        last_seen = {}  # Track last timestamp per device to avoid duplicates
        
        print(f"📡 Client connected to telemetry stream (device_id={device_id}, route_code={route_code})")
        
        try:
            while True:
                # Get all current device states
                states = await store.list_states()
                
                for state in states:
                    # Apply filters
                    if device_id and state.deviceId != device_id:
                        continue
                    if route_code and getattr(state, 'route', None) != route_code:
                        continue
                    
                    # Check if this is a new update (avoid sending duplicates)
                    state_timestamp = state.lastSeen
                    last_timestamp = last_seen.get(state.deviceId)
                    
                    if last_timestamp != state_timestamp:
                        # New update - send to client
                        last_seen[state.deviceId] = state_timestamp
                        
                        # Format as SSE event
                        telemetry_data = {
                            "deviceId": state.deviceId,
                            "route": getattr(state, 'route', None),
                            "vehicleReg": getattr(state, 'vehicleReg', None),
                            "driverId": getattr(state, 'driverId', None),
                            "driverName": getattr(state, 'driverName', None),
                            "location": {
                                "lat": state.lat,
                                "lon": state.lon
                            },
                            "speed": state.speed,
                            "heading": state.heading,
                            "timestamp": state_timestamp
                        }
                        
                        # SSE format: "data: {json}\n\n"
                        yield f"data: {json.dumps(telemetry_data)}\n\n"
                
                # Poll every 1 second for updates
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            print(f"📡 Client disconnected from telemetry stream")
        except Exception as e:
            print(f"❌ Error in telemetry stream: {e}")
            import traceback
            traceback.print_exc()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@app.get("/")
async def root():
    """
    Unified backend root endpoint.
    
    Provides service discovery and health check links.
    """
    uptime = time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
    
    return {
        "service": "ArkNet Unified Backend",
        "version": "1.0.0",
        "status": "operational",
        "uptime_seconds": round(uptime, 1),
        "services": {
            "geospatial": {
                "prefix": "/geo",
                "description": "Reverse geocoding, geofencing, spatial queries",
                "health": "/geo/health",
                "docs": "/geo/docs"
            },
            "gpscentcom": {
                "prefix": "/gps",
                "description": "GPS device telemetry ingestion and retrieval",
                "health": "/gps/health",
                "docs": "/gps/docs",
                "websocket": "ws://localhost:8000/gps/device"
            },
            "manifest": {
                "prefix": "/manifest",
                "description": "Enriched passenger manifest with route positions",
                "health": "/manifest/health",
                "docs": "/manifest/docs"
            }
        },
        "endpoints": {
            "geocoding": "/geo/geocode/reverse?lat=35.0844&lon=-106.6504",
            "geofence": "/geo/geofence/check?lat=35.0844&lon=-106.6504",
            "devices": "/gps/devices",
            "manifest": "/manifest/api/manifest?limit=10",
            "gps_websocket": "ws://localhost:8000/gps/device?token=YOUR_TOKEN&deviceId=DEVICE_ID",
            "gps_stream": "/gps/stream (SSE - real-time telemetry for clients)",
            "gps_stream_filtered": "/gps/stream?device_id=GPS-ZR102 or /gps/stream?route_code=1"
        }
    }


@app.get("/health")
async def unified_health(request: Request):
    """
    Unified health check endpoint.
    
    Aggregates health from all mounted services.
    """
    uptime = time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
    
    health_status = {
        "status": "ok",
        "service": "unified_backend",
        "uptime_seconds": round(uptime, 1),
        "services": {
            "geospatial": "mounted at /geo",
            "gpscentcom": "mounted at /gps",
            "manifest": "mounted at /manifest"
        }
    }
    
    # Note: Individual service health checks available at:
    # /geo/health, /gps/health, /manifest/health
    
    return health_status


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unified backend.
    
    Individual services have their own exception handlers.
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "service": "unified_backend"
        }
    )


if __name__ == "__main__":
    import uvicorn
    import sys
    
    print("\n" + "=" * 70)
    print("Starting ArkNet Unified Backend Server...")
    print("=" * 70)
    
    # Windows-friendly: disable signal handling for graceful CTRL+C
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        use_colors=sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else True
    )
    
    server = uvicorn.Server(config)
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n⚠️  Received shutdown signal (CTRL+C)")
        pass  # Graceful exit
