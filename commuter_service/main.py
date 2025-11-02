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
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
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
    logger.info("   - DELETE /api/manifest                      - Delete passengers")
    logger.info("=" * 80)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Commuter Service via uvicorn...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=4000,
        reload=True,
        log_level="info"
    )

