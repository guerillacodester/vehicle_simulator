"""
Commuter Service - Passenger Spawning Engine

Entrypoint for running the commuter/passenger spawning service.
Starts both depot and route reservoirs to spawn passengers.

Usage:
    python -m commuter_service
    python -m commuter_service --depot-only
    python -m commuter_service --route-only
    python -m commuter_service --socketio-url http://localhost:1337 --strapi-url http://localhost:1337
"""
import asyncio
import argparse
import logging
import os
from typing import Optional
from dotenv import load_dotenv

from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.route_reservoir import RouteReservoir

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_commuter_service(
    socketio_url: str = None,
    strapi_url: str = None,
    depot_only: bool = False,
    route_only: bool = False
):
    """
    Run the commuter service with depot and/or route reservoirs
    
    Args:
        socketio_url: Socket.IO server URL (from env ARKNET_API_URL or default)
        strapi_url: Strapi API base URL (from env ARKNET_API_URL or default)
        depot_only: Only run depot reservoir
        route_only: Only run route reservoir
    """
    # Get URLs from environment or use defaults
    base_url = os.getenv('ARKNET_API_URL', 'http://localhost:1337')
    socketio_url = socketio_url or base_url
    strapi_url = strapi_url or base_url
    
    logger.info("[START] Starting Commuter Service...")
    logger.info(f"   Socket.IO: {socketio_url}")
    logger.info(f"   Strapi API: {strapi_url}")
    
    depot_reservoir: Optional[DepotReservoir] = None
    route_reservoir: Optional[RouteReservoir] = None
    
    try:
        # Start depot reservoir (outbound passengers)
        if not route_only:
            logger.info("[DEPOT] Starting Depot Reservoir (Outbound Passengers)...")
            depot_reservoir = DepotReservoir(
                socketio_url=socketio_url,
                strapi_url=strapi_url
            )
            await depot_reservoir.start()
            logger.info("[OK] Depot Reservoir started")
        
        # Start route reservoir (bidirectional passengers)
        if not depot_only:
            logger.info("[ROUTE] Starting Route Reservoir (Route Passengers)...")
            route_reservoir = RouteReservoir(
                socketio_url=socketio_url,
                strapi_url=strapi_url
            )
            await route_reservoir.start()
            logger.info("[OK] Route Reservoir started")
        
        logger.info("[READY] Commuter Service fully operational!")
        logger.info("   Press Ctrl+C to stop")
        
        # Keep running and print periodic statistics
        stats_interval = 30  # Print stats every 30 seconds
        last_stats_time = asyncio.get_event_loop().time()
        
        while True:
            await asyncio.sleep(1)
            
            # Print statistics periodically
            current_time = asyncio.get_event_loop().time()
            if current_time - last_stats_time >= stats_interval:
                logger.info("=" * 80)
                logger.info("[STATS] SYSTEM STATISTICS")
                logger.info("=" * 80)
                
                if depot_reservoir:
                    depot_stats = depot_reservoir.stats
                    total_active = sum(len(q.commuters) for q in depot_reservoir.queues.values())
                    logger.info(f"[DEPOT] DEPOT RESERVOIR:")
                    logger.info(f"   • Total Spawned: {depot_stats['total_spawned']}")
                    logger.info(f"   • Total Picked Up: {depot_stats['total_picked_up']}")
                    logger.info(f"   • Total Expired: {depot_stats['total_expired']}")
                    logger.info(f"   • Currently Waiting: {total_active}")
                    logger.info(f"   • Active Depots: {len(depot_reservoir.queues)}")
                
                if route_reservoir:
                    route_stats = route_reservoir.stats
                    logger.info(f"[ROUTE] ROUTE RESERVOIR:")
                    logger.info(f"   • Total Spawned: {route_stats['total_spawned']}")
                    logger.info(f"   • Total Picked Up: {route_stats['total_picked_up']}")
                    logger.info(f"   • Total Expired: {route_stats['total_expired']}")
                    logger.info(f"   • Currently Waiting: {len(route_reservoir.active_commuters)}")
                    logger.info(f"   • Active Grid Cells: {len(route_reservoir.grid)}")
                
                logger.info("=" * 80)
                last_stats_time = current_time
            
    except KeyboardInterrupt:
        logger.info("\n[SHUTDOWN] Shutting down Commuter Service...")
    except Exception as e:
        logger.error(f"[ERROR] Error in Commuter Service: {e}", exc_info=True)
    finally:
        # Cleanup
        if depot_reservoir:
            logger.info("Stopping Depot Reservoir...")
            await depot_reservoir.stop()
        if route_reservoir:
            logger.info("Stopping Route Reservoir...")
            await route_reservoir.stop()
        logger.info("[OK] Commuter Service stopped cleanly")


def main():
    """Main entrypoint"""
    # Get default URL from environment
    default_url = os.getenv('ARKNET_API_URL', 'http://localhost:1337')
    
    parser = argparse.ArgumentParser(
        description="Commuter Service - Passenger Spawning Engine"
    )
    parser.add_argument(
        '--socketio-url',
        default=default_url,
        help=f'Socket.IO server URL (default: {default_url})'
    )
    parser.add_argument(
        '--strapi-url',
        default=default_url,
        help=f'Strapi API base URL (default: {default_url})'
    )
    parser.add_argument(
        '--depot-only',
        action='store_true',
        help='Only run depot reservoir (outbound passengers only)'
    )
    parser.add_argument(
        '--route-only',
        action='store_true',
        help='Only run route reservoir (route passengers only)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the service
    asyncio.run(run_commuter_service(
        socketio_url=args.socketio_url,
        strapi_url=args.strapi_url,
        depot_only=args.depot_only,
        route_only=args.route_only
    ))


if __name__ == '__main__':
    main()
