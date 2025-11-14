"""
Commuter Service - Main FastAPI Application
==========================================

HTTP API for commuter/passenger management:
- Manifest queries (GET /api/manifest)
- Visualization endpoints (barchart, table)
- Statistics and analytics
- Passenger CRUD operations

This is the unified commuter service that replaced the deprecated commuter_service_deprecated.
"""

import logging

# Import the FastAPI app from commuter_manifest module
# This module already has all routes, CORS, and configuration
from commuter_service.interfaces.http.commuter_manifest import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

# Add startup event handler to log service start
# Add startup event handler to log service start
@app.on_event("startup")
async def startup_event():
    """Log startup information and start monitoring service."""
    logger.info("=" * 80)
    logger.info("🚀 COMMUTER SERVICE - STARTING")
    logger.info("=" * 80)
    logger.info("✅ Commuter Service API ready on http://0.0.0.0:4000")
    logger.info("📊 Main Endpoints:")
    logger.info("   - GET  /health                              - Health check")
    logger.info("   - GET  /api/manifest                        - Query passenger manifest")
    logger.info("   - GET  /api/manifest/visualization/barchart - Passenger distribution chart")
    logger.info("   - GET  /api/manifest/visualization/table    - Passenger table view")
    logger.info("   - GET  /api/manifest/stats                  - Passenger statistics")
    logger.info("   - POST /api/seed                            - Seed passengers (remote)")
    logger.info("   - DELETE /api/manifest                      - Delete passengers")
    logger.info("   - WS   /ws/stream                           - Real-time event streaming")
    logger.info("🔧 Passenger CRUD:")
    logger.info("   - GET    /api/passengers                    - List/search passengers")
    logger.info("   - GET    /api/passengers/{id}               - Get passenger")
    logger.info("   - POST   /api/passengers                    - Create passenger")
    logger.info("   - PUT    /api/passengers/{id}               - Update passenger")
    logger.info("   - PATCH  /api/passengers/{id}/board         - Board passenger")
    logger.info("   - PATCH  /api/passengers/{id}/alight        - Alight passenger")
    logger.info("   - DELETE /api/passengers/{id}               - Delete passenger")
    logger.info("🔍 Monitoring:")
    logger.info("   - GET  /api/monitor/stats                   - Monitor statistics")
    logger.info("🖥️  Client Console:")
    logger.info("   python clients/commuter/client_console.py")
    logger.info("=" * 80)
    
    # Start passenger state monitor
    try:
        from commuter_service.services.passenger_monitor import get_monitor
        monitor = get_monitor()
        await monitor.start()
        logger.info("✅ Passenger state monitor started")
    except Exception as e:
        logger.error(f"⚠️  Failed to start monitor: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of services."""
    logger.info("⏹️  Shutting down commuter service...")
    
    # Stop monitor
    try:
        from commuter_service.services.passenger_monitor import get_monitor
        monitor = get_monitor()
        await monitor.stop()
        logger.info("✅ Monitor stopped")
    except:
        pass
    
    logger.info("👋 Goodbye!")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Commuter Service via uvicorn...")
    uvicorn.run(
        "commuter_service.main:app",
        host="0.0.0.0",
        port=4000,
        reload=True,
        log_level="info"
    )

