"""
ArkNet Commuter Service - CLI Launcher

Beautiful terminal interface for monitoring the commuter service.

Usage:
    python start_commuter_cli.py

Features:
- Real-time spawn event monitoring
- Live statistics dashboard
- Zone loading progress
- Service health indicators
- Professional terminal UI
"""

import asyncio
import sys
from commuter_service.cli_interface import run_cli_interface

if __name__ == "__main__":
    try:
        asyncio.run(run_cli_interface())
    except KeyboardInterrupt:
        print("\n✅ Commuter service stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
