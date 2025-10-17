"""
Simple Production Monitor - Outputs to log file for tailing
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.route_reservoir import RouteReservoir

LOG_FILE = "production_spawns.log"

def log(message):
    """Write to log file and stdout"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line)
    print(line, end='', flush=True)

async def monitor_spawns(depot, route):
    """Monitor and report spawn activity"""
    last_depot_count = 0
    last_route_count = 0
    check_count = 0
    
    log("=== MONITORING STARTED ===")
    
    while True:
        await asyncio.sleep(5)
        check_count += 1
        
        # Check depot spawns
        if depot.spawning_coordinator:
            depot_stats = depot.spawning_coordinator.get_stats()
            depot_count = depot_stats['total_spawned']
            
            if depot_count > last_depot_count:
                diff = depot_count - last_depot_count
                log(f"[DEPOT] +{diff:3d} passengers | Total: {depot_count:4d}")
                last_depot_count = depot_count
        
        # Check route spawns
        if route.spawning_coordinator:
            route_stats = route.spawning_coordinator.get_stats()
            route_count = route_stats['total_spawned']
            
            if route_count > last_route_count:
                diff = route_count - last_route_count
                log(f"[ROUTE] +{diff:3d} passengers | Total: {route_count:4d}")
                last_route_count = route_count
        
        # Heartbeat every minute
        if check_count % 12 == 0:
            log(f"[STATS] Depot: {last_depot_count} | Route: {last_route_count} | Total: {last_depot_count + last_route_count}")

async def start_services():
    """Start services"""
    # Clear log file
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("")
    
    log("=== COMMUTER SERVICE PRODUCTION RUN ===")
    log("Initializing services...")
    
    depot = DepotReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    route = RouteReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    log("Starting Depot Reservoir...")
    await depot.start()
    log("Depot Reservoir: ONLINE")
    
    log("Starting Route Reservoir...")
    await route.start()
    log("Route Reservoir: ONLINE")
    
    log("Services ready. Waiting for first spawn cycle (30s)...")
    
    try:
        await monitor_spawns(depot, route)
    except KeyboardInterrupt:
        log("Shutting down...")
        await depot.stop()
        await route.stop()
        log("Services stopped")

if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        pass
