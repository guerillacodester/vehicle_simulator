"""
Production Commuter Service Runner with Real-Time Console Output
Shows spawning activity as it happens
"""
import asyncio
import sys
import logging
from datetime import datetime
from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.route_reservoir import RouteReservoir

# Configure console logging with simple format (no emojis)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('commuter_production.log')
    ]
)

class ProductionMonitor:
    def __init__(self):
        self.depot_spawns = 0
        self.route_spawns = 0
        self.start_time = datetime.now()
    
    def on_depot_spawn(self, count: int):
        self.depot_spawns += count
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*80}")
        print(f"[DEPOT SPAWN] +{count} passengers | Total: {self.depot_spawns} | Elapsed: {elapsed:.0f}s")
        print(f"{'='*80}\n")
    
    def on_route_spawn(self, count: int):
        self.route_spawns += count
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*80}")
        print(f"[ROUTE SPAWN] +{count} passengers | Total: {self.route_spawns} | Elapsed: {elapsed:.0f}s")
        print(f"{'='*80}\n")
    
    def print_summary(self):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*80}")
        print(f"PRODUCTION RUN SUMMARY")
        print(f"{'='*80}")
        print(f"Runtime: {elapsed:.0f} seconds")
        print(f"Depot Spawns: {self.depot_spawns}")
        print(f"Route Spawns: {self.route_spawns}")
        print(f"Total Spawns: {self.depot_spawns + self.route_spawns}")
        print(f"Spawn Rate: {(self.depot_spawns + self.route_spawns) / (elapsed / 60):.1f} passengers/minute")
        print(f"{'='*80}\n")


async def spawn_callback(monitor, context: str):
    """Callback to track spawns"""
    async def callback(spawn_request):
        if context == "depot":
            monitor.on_depot_spawn(1)
        else:
            monitor.on_route_spawn(1)
    return callback


async def main():
    print("\n" + "="*80)
    print("COMMUTER SERVICE - PRODUCTION RUN")
    print("="*80)
    print("Starting both depot and route reservoirs...")
    print("Press Ctrl+C to stop\n")
    
    monitor = ProductionMonitor()
    
    # Create reservoirs
    depot = DepotReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    route = RouteReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    # Start depot reservoir
    print("\n[1/2] Starting depot reservoir...")
    await depot.start()
    print("[OK] Depot reservoir started")
    
    # Start route reservoir
    print("\n[2/2] Starting route reservoir...")
    await route.start()
    print("[OK] Route reservoir started")
    
    print("\n" + "="*80)
    print("SERVICE RUNNING - Monitoring spawn activity...")
    print("Spawn interval: 30 seconds")
    print("="*80 + "\n")
    
    try:
        # Run forever, printing stats every 60 seconds
        cycle = 0
        while True:
            await asyncio.sleep(60)
            cycle += 1
            print(f"\n[CYCLE {cycle}] Service running for {cycle} minute(s)...")
            monitor.print_summary()
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        monitor.print_summary()
        await depot.stop()
        await route.stop()
        print("Service stopped cleanly")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
