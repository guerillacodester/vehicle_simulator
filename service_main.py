#!/usr/bin/env python3
"""
ArkNet Transit Simulator Service
=================================

Runs the simulator as a background service/daemon.
Linux-compatible with systemd integration.

Usage:
    # Foreground (testing):
    python service_main.py

    # Background (production):
    nohup python service_main.py > simulator.log 2>&1 &

    # Systemd service:
    sudo systemctl start arknet-simulator
"""

import sys
import signal
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from arknet_transit_simulator.simulator import CleanVehicleSimulator
from arknet_transit_simulator.config.config_loader import ConfigLoader

# Configure logging for service
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulator_service.log')
    ]
)

logger = logging.getLogger(__name__)


class SimulatorService:
    """Service wrapper for the transit simulator"""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_port: int = 5001,
        enable_boarding_after: Optional[float] = None,
        sim_time: Optional[datetime] = None
    ):
        """
        Initialize service
        
        Args:
            api_url: Strapi API URL
            api_port: Fleet Management API port
            enable_boarding_after: Auto-enable boarding delay
            sim_time: Simulation time override
        """
        self.api_url = api_url
        self.api_port = api_port
        self.enable_boarding_after = enable_boarding_after
        self.sim_time = sim_time
        self.simulator = None
        self._shutdown_requested = False
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name} signal - initiating shutdown...")
        self._shutdown_requested = True
    
    async def start(self):
        """Start the simulator service"""
        try:
            logger.info("=" * 60)
            logger.info("ArkNet Transit Simulator Service")
            logger.info("=" * 60)
            logger.info(f"API Port: {self.api_port}")
            logger.info(f"Strapi URL: {self.api_url or 'Auto-detect from config'}")
            if self.sim_time:
                logger.info(f"Simulation Time: {self.sim_time}")
            logger.info("=" * 60)
            
            # Load GPS configuration
            config_loader = ConfigLoader()
            gps_config = config_loader.get_gps_config()
            
            # Create simulator with API enabled
            self.simulator = CleanVehicleSimulator(
                api_url=self.api_url,
                enable_boarding_after=self.enable_boarding_after,
                gps_config=gps_config,
                sim_time=self.sim_time,
                enable_api=True,
                api_port=self.api_port
            )
            
            # Initialize simulator
            logger.info("Initializing simulator...")
            if not await self.simulator.initialize():
                logger.error("Simulator initialization failed")
                return 1
            
            logger.info("✅ Simulator initialized successfully")
            logger.info(f"🌐 Fleet Management API: http://localhost:{self.api_port}")
            logger.info(f"📖 API Documentation: http://localhost:{self.api_port}/docs")
            logger.info(f"🔍 Health Check: http://localhost:{self.api_port}/health")
            logger.info("")
            logger.info("Service is running. Use fleet console to interact.")
            logger.info("To connect: python -m clients.fleet")
            logger.info("")
            
            # Run simulator indefinitely
            await self.simulator.run(duration=None)
            
            logger.info("Simulator service stopped")
            return 0
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            return 0
        except Exception as e:
            logger.error(f"Service error: {e}", exc_info=True)
            return 1
        finally:
            if self.simulator:
                await self.simulator.shutdown()
    
    def run(self):
        """Run the service (blocking)"""
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Run async event loop
        exit_code = asyncio.run(self.start())
        sys.exit(exit_code)


def parse_args():
    """Parse command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="ArkNet Transit Simulator Service"
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default=None,
        help='Strapi API URL (default: auto-detect from config.ini)'
    )
    parser.add_argument(
        '--api-port',
        type=int,
        default=5001,
        help='Fleet Management API port (default: 5001)'
    )
    parser.add_argument(
        '--enable-boarding-after',
        type=float,
        default=None,
        help='Auto-enable boarding after N seconds'
    )
    parser.add_argument(
        '--sim-time',
        type=str,
        default=None,
        help='Simulation time (ISO format or HH:MM)'
    )
    parser.add_argument(
        '--sim-date',
        type=str,
        default=None,
        help='Simulation date (YYYY-MM-DD)'
    )
    
    return parser.parse_args()


def parse_sim_time(args):
    """Parse simulation time from arguments"""
    if not args.sim_time and not args.sim_date:
        return None
    
    from datetime import datetime
    
    # Parse time
    if args.sim_time:
        # Try ISO format first
        try:
            return datetime.fromisoformat(args.sim_time.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        # Try HH:MM format
        try:
            parts = args.sim_time.split(':')
            if len(parts) == 2:
                hour, minute = int(parts[0]), int(parts[1])
                now = datetime.now()
                
                # Use sim_date if provided
                if args.sim_date:
                    date_parts = args.sim_date.split('-')
                    year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                    return datetime(year, month, day, hour, minute)
                else:
                    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except (ValueError, IndexError):
            pass
    
    # Just date, use current time
    if args.sim_date:
        date_parts = args.sim_date.split('-')
        year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
        now = datetime.now()
        return datetime(year, month, day, now.hour, now.minute)
    
    return None


def main():
    """Main entry point"""
    args = parse_args()
    sim_time = parse_sim_time(args)
    
    # Create and run service
    service = SimulatorService(
        api_url=args.api_url,
        api_port=args.api_port,
        enable_boarding_after=args.enable_boarding_after,
        sim_time=sim_time
    )
    
    service.run()


if __name__ == "__main__":
    main()
