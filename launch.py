#!/usr/bin/env python3
"""
ArkNet Fleet System Launcher - Single Entry Point
=================================================

Production-grade launcher with SOLID architecture.

STARTUP SEQUENCE:
1. Monitor Server (port 8000) - Health gated
2. Strapi CMS (Foundation) - Health gated
3. GPSCentCom Server - Health gated
4. Pre-simulator delay
5. Vehicle + Commuter Simulators (parallel)
6. Geospatial + Manifest Services - Health gated

Each service console spawns ONLY AFTER health check passes.

Usage:
    python launch.py
"""

import sys
from pathlib import Path

# Add launcher package to path
sys.path.insert(0, str(Path(__file__).parent))

from launcher.app import LauncherApplication


def main():
    """Main entry point."""
    config_path = Path(__file__).parent / "config.ini"
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        print()
        print("   Please ensure config.ini exists in the root directory")
        sys.exit(1)
    
    try:
        app = LauncherApplication(config_path)
        app.run()
    except KeyboardInterrupt:
        print()
        print("👋 Launcher interrupted by user")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
