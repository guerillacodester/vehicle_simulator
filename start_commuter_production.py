"""
Production Commuter Service Launcher
Starts both depot and route reservoirs with real-time monitoring
"""
import asyncio
import sys
import os
from datetime import datetime

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.route_reservoir import RouteReservoir

# Stats tracking
spawn_stats = {
    'depot': {'total': 0, 'cycles': 0, 'last_spawn': None},
    'route': {'total': 0, 'cycles': 0, 'last_spawn': None}
}

def print_header():
    """Print startup header"""
    print("\n" + "="*80)
    print(" COMMUTER SERVICE - PRODUCTION MODE")
    print("="*80)
    print(f" Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(" Press Ctrl+C to stop")
    print("="*80 + "\n")

def print_spawn_event(context: str, count: int):
    """Print a spawn event"""
    global spawn_stats
    spawn_stats[context]['total'] += count
    spawn_stats[context]['cycles'] += 1
    spawn_stats[context]['last_spawn'] = datetime.now()
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] [{context.upper():6s}] Spawned {count:3d} passengers | "
          f"Total: {spawn_stats[context]['total']:4d} | "
          f"Cycles: {spawn_stats[context]['cycles']:3d}")

def print_stats():
    """Print current stats"""
    print("\n" + "-"*80)
    print(" CURRENT STATISTICS")
    print("-"*80)
    for context in ['depot', 'route']:
        stats = spawn_stats[context]
        last = stats['last_spawn'].strftime('%H:%M:%S') if stats['last_spawn'] else 'Never'
        print(f" {context.upper():6s}: {stats['total']:4d} total passengers | "
              f"{stats['cycles']:3d} cycles | Last: {last}")
    print("-"*80 + "\n")

async def spawn_callback_depot(spawn_request):
    """Callback for depot spawns"""
    # Increment counter (actual spawn processing happens in reservoir)
    pass

async def spawn_callback_route(spawn_request):
    """Callback for route spawns"""
    # Increment counter (actual spawn processing happens in reservoir)
    pass

async def monitor_spawns(depot, route):
    """Monitor and report spawn activity"""
    last_depot_count = 0
    last_route_count = 0
    cycles = 0
    
    while True:
        await asyncio.sleep(5)  # Check every 5 seconds
        
        # Get current stats from coordinators
        if depot.spawning_coordinator:
            depot_stats = depot.spawning_coordinator.get_stats()
            depot_count = depot_stats['total_spawned']
            
            if depot_count > last_depot_count:
                diff = depot_count - last_depot_count
                print_spawn_event('depot', diff)
                last_depot_count = depot_count
        
        if route.spawning_coordinator:
            route_stats = route.spawning_coordinator.get_stats()
            route_count = route_stats['total_spawned']
            
            if route_count > last_route_count:
                diff = route_count - last_route_count
                print_spawn_event('route', diff)
                last_route_count = route_count
        
        # Print stats every minute
        cycles += 1
        if cycles % 12 == 0:  # Every 60 seconds (12 * 5s)
            print_stats()

async def start_services():
    """Start both depot and route reservoirs"""
    print_header()
    
    print("[INIT] Initializing Depot Reservoir...")
    depot = DepotReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    print("[INIT] Initializing Route Reservoir...")
    route = RouteReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    print("\n[START] Starting Depot Reservoir...")
    await depot.start()
    print("[OK] Depot Reservoir started")
    
    print("[START] Starting Route Reservoir...")
    await route.start()
    print("[OK] Route Reservoir started")
    
    print("\n[MONITOR] Monitoring spawn activity...\n")
    print("-"*80)
    
    # Start monitoring
    try:
        await monitor_spawns(depot, route)
    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Stopping services...")
        await depot.stop()
        await route.stop()
        print("[OK] Services stopped")
        print_stats()

if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        print("\n[EXIT] Shutting down...")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
