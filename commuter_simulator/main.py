"""
Commuter Simulator - Main Entry Point
=====================================

Single entry point for starting the commuter simulator service.
Orchestrates depot and route reservoirs with the simulator engine.
"""

import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from commuter_simulator.infrastructure.database import StrapiApiClient
from commuter_simulator.services.socketio import SocketIOService, ServiceType
from commuter_simulator.core.domain.simulator_engine import SimulatorEngine


class CommuterSimulatorService:
    """
    Main service orchestrator for the commuter simulator.
    
    Manages:
    - Simulator engine (statistical passenger generation)
    - Depot reservoir (depot-based spawning)
    - Route reservoir (route-based spawning)
    - Socket.IO communication
    """
    
    def __init__(
        self,
        strapi_url: str = "http://localhost:1337",
        socketio_url: str = "http://localhost:1337"
    ):
        self.strapi_url = strapi_url
        self.socketio_url = socketio_url
        
        # Configure logging
        self.logger = self._setup_logging()
        
        # Core services
        self.api_client: StrapiApiClient = None
        self.simulator_engine: SimulatorEngine = None
        
        # Statistics
        self.stats = {
            "started_at": None,
            "depot_spawns": 0,
            "route_spawns": 0,
            "total_spawns": 0
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)
    
    async def start(self):
        """Start all services"""
        self.logger.info("="*80)
        self.logger.info("COMMUTER SIMULATOR - STARTING")
        self.logger.info("="*80)
        self.stats["started_at"] = datetime.now().isoformat()
        
        try:
            # Initialize API client (single source of truth)
            self.logger.info("[1/3] Initializing Strapi API client...")
            self.api_client = StrapiApiClient(self.strapi_url)
            await self.api_client.connect()
            
            # Initialize simulator engine
            self.logger.info("[2/3] Initializing simulator engine...")
            self.simulator_engine = SimulatorEngine(
                api_client=self.api_client,
                socketio_url=self.socketio_url
            )
            await self.simulator_engine.initialize()
            
            # Start simulation
            self.logger.info("[3/3] Starting simulation...")
            await self.simulator_engine.start()
            
            self.logger.info("="*80)
            self.logger.info("✓ COMMUTER SIMULATOR RUNNING")
            self.logger.info("="*80)
            
            # Keep running
            while True:
                await asyncio.sleep(60)
                self._print_stats()
                
        except KeyboardInterrupt:
            self.logger.info("\n⚠️  Shutdown requested...")
            await self.stop()
        except Exception as e:
            self.logger.error(f"✗ Fatal error: {e}", exc_info=True)
            await self.stop()
            raise
    
    async def stop(self):
        """Stop all services"""
        self.logger.info("="*80)
        self.logger.info("STOPPING SERVICES")
        self.logger.info("="*80)
        
        if self.simulator_engine:
            await self.simulator_engine.stop()
        
        if self.api_client:
            await self.api_client.close()
        
        self._print_final_stats()
        self.logger.info("✓ Shutdown complete")
    
    def _print_stats(self):
        """Print current statistics"""
        if self.simulator_engine:
            stats = self.simulator_engine.get_stats()
            self.logger.info(f"Statistics: {stats}")
    
    def _print_final_stats(self):
        """Print final statistics"""
        self.logger.info("="*80)
        self.logger.info("FINAL STATISTICS")
        self.logger.info("="*80)
        
        if self.simulator_engine:
            stats = self.simulator_engine.get_stats()
            for key, value in stats.items():
                self.logger.info(f"  {key}: {value}")


async def main():
    """Main entry point"""
    service = CommuterSimulatorService(
        strapi_url="http://localhost:1337",
        socketio_url="http://localhost:1337"
    )
    
    await service.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ Shutdown complete")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)
