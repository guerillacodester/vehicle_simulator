"""
Start Fleet Management API Server
=================================
Proper startup script for the Fleet Management API with hot reload support.
"""

import uvicorn
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def start_api_server():
    """Start the API server with proper configuration"""
    uvicorn.run(
        "world.fleet_manager.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        reload_dirs=[str(project_root)]
    )

if __name__ == "__main__":
    start_api_server()
