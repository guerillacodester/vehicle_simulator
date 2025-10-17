"""
Simple startup script WITHOUT the CLI interface
Just to see the raw logs and find where it hangs
"""

import asyncio
import sys
import logging

# Force UTF-8 encoding for Windows console to support emojis 🎉
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Configure logging to see everything with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('commuter_startup.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Will now use UTF-8
    ]
)

async def start_services():
    from commuter_service.depot_reservoir import DepotReservoir
    from commuter_service.route_reservoir import RouteReservoir
    
    print("\n" + "=" * 80)
    print("COMMUTER SERVICE STARTUP - RAW LOGS")
    print("=" * 80 + "\n")
    
    depot = DepotReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    route = RouteReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    print("\n[>] Starting depot reservoir...\n")
    await depot.start()
    
    print("\n[>] Starting route reservoir...\n")
    await route.start()
    
    print("\n[OK] Both reservoirs started!\n")
    print("Waiting 90 seconds to observe spawns...\n")
    
    await asyncio.sleep(90)
    
    print("\n[STOP] Stopping...\n")
    await depot.stop()
    await route.stop()
    
    print("[OK] Stopped\n")

if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
