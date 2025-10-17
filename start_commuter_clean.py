"""
Production Commuter Service Launcher (With Beautiful Emojis! 🎉)
Starts both depot and route reservoirs with clean console output
"""
import asyncio
import sys
import logging
from datetime import datetime

# Force UTF-8 encoding for Windows console to support emojis! 🚀
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.route_reservoir import RouteReservoir

# Configure logging to file only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('commuter_production.log', encoding='utf-8'),
    ]
)


async def start_services():
    """Start both depot and route reservoirs"""
    print("\n" + "="*80)
    print("COMMUTER SERVICE - PRODUCTION MODE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Log file: commuter_production.log")
    print("="*80 + "\n")
    
    depot = DepotReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    route = RouteReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    print("[1/2] Starting depot reservoir...")
    await depot.start()
    print("      Depot reservoir running\n")
    
    print("[2/2] Starting route reservoir...")
    await route.start()
    print("      Route reservoir running\n")
    
    print("="*80)
    print("BOTH SERVICES RUNNING")
    print("="*80)
    print("Spawning every 30 seconds...")
    print("Press Ctrl+C to stop")
    print("="*80 + "\n")
    
    # Monitor spawn activity
    last_depot_total = 0
    last_route_total = 0
    cycle = 0
    
    try:
        while True:
            await asyncio.sleep(35)  # Check every 35 seconds (after spawn cycles)
            cycle += 1
            
            # Get current stats
            depot_stats = await depot.statistics.get_stats()
            route_stats = await route.statistics.get_stats()
            
            depot_spawned = depot_stats.get('total_spawned', 0)
            route_spawned = route_stats.get('total_spawned', 0)
            
            depot_new = depot_spawned - last_depot_total
            route_new = route_spawned - last_route_total
            
            if depot_new > 0 or route_new > 0:
                print(f"[Cycle {cycle}] +{depot_new} depot, +{route_new} route | "
                      f"Total: {depot_spawned} depot, {route_spawned} route passengers")
            
            last_depot_total = depot_spawned
            last_route_total = route_spawned
            
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("SHUTTING DOWN")
        print("="*80)
        await depot.stop()
        await route.stop()
        print("Services stopped cleanly")
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
