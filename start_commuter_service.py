"""
Commuter Service Startup Script

Starts both depot and route reservoirs for passenger spawning.
This is the main entrypoint for the commuter spawning service.

Usage:
    python start_commuter_service.py
    python start_commuter_service.py --strapi-url http://localhost:1337
"""

import asyncio
import logging
import argparse
import signal
import sys

from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.route_reservoir import RouteReservoir

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommuterService:
    """Main commuter spawning service"""
    
    def __init__(self, strapi_url: str = "http://localhost:1337"):
        self.strapi_url = strapi_url
        self.depot_reservoir = None
        self.route_reservoir = None
        self.running = False
        
    async def start(self):
        """Start both reservoirs"""
        logger.info("=" * 80)
        logger.info("🚌 COMMUTER SERVICE STARTING")
        logger.info("=" * 80)
        logger.info(f"Strapi URL: {self.strapi_url}")
        logger.info("")
        
        try:
            # Initialize reservoirs
            logger.info("Initializing depot reservoir...")
            self.depot_reservoir = DepotReservoir(
                socketio_url=self.strapi_url,
                strapi_url=self.strapi_url
            )
            
            logger.info("Initializing route reservoir...")
            self.route_reservoir = RouteReservoir(
                socketio_url=self.strapi_url,
                strapi_url=self.strapi_url
            )
            
            # Start both reservoirs
            logger.info("\nStarting depot reservoir...")
            await self.depot_reservoir.start()
            logger.info("✅ Depot reservoir started")
            
            logger.info("\nStarting route reservoir...")
            await self.route_reservoir.start()
            logger.info("✅ Route reservoir started")
            
            self.running = True
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ COMMUTER SERVICE RUNNING")
            logger.info("=" * 80)
            logger.info("Services:")
            logger.info("  - Depot Reservoir: Active (outbound passengers at depots)")
            logger.info("  - Route Reservoir: Active (bidirectional passengers along routes)")
            logger.info("")
            logger.info("Connected to:")
            logger.info(f"  - Strapi API: {self.strapi_url}/api")
            logger.info(f"  - Socket.IO: {self.strapi_url}")
            logger.info(f"  - Database: {self.strapi_url}/api/active-passengers")
            logger.info("")
            logger.info("Press Ctrl+C to stop...")
            logger.info("=" * 80)
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting commuter service: {e}", exc_info=True)
            await self.stop()
            raise
    
    async def stop(self):
        """Stop both reservoirs"""
        if not self.running:
            return
            
        logger.info("")
        logger.info("=" * 80)
        logger.info("🛑 COMMUTER SERVICE STOPPING")
        logger.info("=" * 80)
        
        self.running = False
        
        try:
            if self.depot_reservoir:
                logger.info("Stopping depot reservoir...")
                await self.depot_reservoir.stop()
                logger.info("✅ Depot reservoir stopped")
            
            if self.route_reservoir:
                logger.info("Stopping route reservoir...")
                await self.route_reservoir.stop()
                logger.info("✅ Route reservoir stopped")
                
        except Exception as e:
            logger.error(f"Error stopping commuter service: {e}", exc_info=True)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ COMMUTER SERVICE STOPPED")
        logger.info("=" * 80)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Commuter Service - Passenger Spawning System")
    parser.add_argument(
        '--strapi-url',
        type=str,
        default='http://localhost:1337',
        help='Strapi server URL (default: http://localhost:1337)'
    )
    args = parser.parse_args()
    
    service = CommuterService(strapi_url=args.strapi_url)
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\n\nReceived shutdown signal...")
        asyncio.create_task(service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received...")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
