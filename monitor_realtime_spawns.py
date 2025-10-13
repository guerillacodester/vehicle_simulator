"""
Real-time Spawn Monitor
======================
Monitors passenger spawning events in real-time using Socket.IO
Shows depot spawns, route spawns with actual depot/route/POI data from API
"""

import asyncio
import socketio
import httpx
from datetime import datetime
from colorama import init, Fore, Style
import sys

# Initialize colorama for Windows
init()

class SpawnMonitor:
    def __init__(self, socketio_url="http://localhost:1337", api_url="http://localhost:1337/api"):
        self.socketio_url = socketio_url
        self.api_url = api_url
        self.sio = socketio.AsyncClient()
        
        # Cache for API data
        self.depots = {}
        self.routes = {}
        self.vehicles = {}
        
        # Statistics
        self.stats = {
            "depot_spawns": 0,
            "route_spawns": 0,
            "total_spawns": 0,
            "start_time": datetime.now()
        }
        
    async def load_api_data(self):
        """Load depots, routes, and vehicles from API"""
        print(f"\n{Fore.CYAN}📡 Loading data from API...{Style.RESET_ALL}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Load depots
                resp = await client.get(f"{self.api_url}/depots")
                if resp.status_code == 200:
                    depot_data = resp.json()
                    for depot in depot_data.get('data', []):
                        self.depots[depot['depot_id']] = {
                            'name': depot['name'],
                            'address': depot.get('address', 'N/A'),
                            'latitude': depot.get('latitude'),
                            'longitude': depot.get('longitude')
                        }
                    print(f"{Fore.GREEN}✅ Loaded {len(self.depots)} depots{Style.RESET_ALL}")
                
                # Load routes
                resp = await client.get(f"{self.api_url}/routes")
                if resp.status_code == 200:
                    route_data = resp.json()
                    for route in route_data.get('data', []):
                        self.routes[route['short_name']] = {
                            'long_name': route['long_name'],
                            'description': route.get('description', ''),
                            'color': route.get('color', '#000000')
                        }
                    print(f"{Fore.GREEN}✅ Loaded {len(self.routes)} routes{Style.RESET_ALL}")
                
                # Load vehicles (if any)
                try:
                    resp = await client.get(f"{self.api_url}/vehicles")
                    if resp.status_code == 200:
                        vehicle_data = resp.json()
                        for vehicle in vehicle_data.get('data', []):
                            self.vehicles[vehicle.get('vehicle_id', vehicle['id'])] = {
                                'name': vehicle.get('name', 'Unknown'),
                                'capacity': vehicle.get('capacity', 0),
                                'route': vehicle.get('route', 'N/A')
                            }
                        print(f"{Fore.GREEN}✅ Loaded {len(self.vehicles)} vehicles{Style.RESET_ALL}")
                except:
                    print(f"{Fore.YELLOW}⚠️  No vehicles found in database{Style.RESET_ALL}")
                    
            except Exception as e:
                print(f"{Fore.RED}❌ Error loading API data: {e}{Style.RESET_ALL}")
    
    async def connect(self):
        """Connect to Socket.IO namespaces"""
        print(f"\n{Fore.CYAN}🔌 Connecting to Socket.IO...{Style.RESET_ALL}")
        
        # Register event handlers
        @self.sio.event
        async def connect():
            print(f"{Fore.GREEN}✅ Connected to Socket.IO server{Style.RESET_ALL}")
        
        @self.sio.event
        async def disconnect():
            print(f"{Fore.YELLOW}⚠️  Disconnected from Socket.IO{Style.RESET_ALL}")
        
        @self.sio.on('message', namespace='/depot-reservoir')
        async def on_depot_message(data):
            # Debug: print what we received
            print(f"\n{Fore.CYAN}[DEBUG DEPOT] Received data type: {type(data)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[DEBUG DEPOT] Data keys: {data.keys() if isinstance(data, dict) else 'N/A'}{Style.RESET_ALL}")
            if isinstance(data, dict) and 'type' in data:
                print(f"{Fore.CYAN}[DEBUG DEPOT] Message type: {data.get('type')}{Style.RESET_ALL}")
            if isinstance(data, dict) and 'data' in data:
                print(f"{Fore.CYAN}[DEBUG DEPOT] Inner data keys: {data['data'].keys() if isinstance(data['data'], dict) else 'N/A'}{Style.RESET_ALL}")
            
            # Check if this is a spawn event
            if isinstance(data, dict) and data.get('type') == 'commuter:spawned':
                # Extract the actual spawn data from the message wrapper
                spawn_data = data.get('data', {})
                await self.handle_depot_spawn(spawn_data)
        
        @self.sio.on('message', namespace='/route-reservoir')
        async def on_route_message(data):
            # Debug: print what we received
            print(f"\n{Fore.MAGENTA}[DEBUG ROUTE] Received data type: {type(data)}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}[DEBUG ROUTE] Data keys: {data.keys() if isinstance(data, dict) else 'N/A'}{Style.RESET_ALL}")
            if isinstance(data, dict) and 'type' in data:
                print(f"{Fore.MAGENTA}[DEBUG ROUTE] Message type: {data.get('type')}{Style.RESET_ALL}")
            if isinstance(data, dict) and 'data' in data:
                print(f"{Fore.MAGENTA}[DEBUG ROUTE] Inner data keys: {data['data'].keys() if isinstance(data['data'], dict) else 'N/A'}{Style.RESET_ALL}")
            
            # Check if this is a spawn event
            if isinstance(data, dict) and data.get('type') == 'commuter:spawned':
                # Extract the actual spawn data from the message wrapper
                spawn_data = data.get('data', {})
                await self.handle_route_spawn(spawn_data)
        
        # Connect to both namespaces
        try:
            await self.sio.connect(self.socketio_url, namespaces=['/depot-reservoir', '/route-reservoir'])
            print(f"{Fore.GREEN}✅ Subscribed to depot and route spawn events{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Connection error: {e}{Style.RESET_ALL}")
            return False
        
        return True
    
    def _normalize_location(self, location):
        """Convert location to dict format {lat: x, lon: y}"""
        if isinstance(location, dict):
            return location
        elif isinstance(location, (tuple, list)) and len(location) >= 2:
            return {'lat': location[0], 'lon': location[1]}
        else:
            return {'lat': 0, 'lon': 0}
    
    async def handle_depot_spawn(self, data):
        """Handle depot spawn event"""
        self.stats['depot_spawns'] += 1
        self.stats['total_spawns'] += 1
        
        # Extract spawn data (handle both formats: passenger_id/spawn_location OR commuter_id/current_location)
        commuter_id = data.get('passenger_id') or data.get('commuter_id', 'unknown')
        depot_id = data.get('depot_id', 'unknown')
        route_id = data.get('route_id', 'unknown')
        location = self._normalize_location(data.get('spawn_location') or data.get('current_location', {}))
        destination = self._normalize_location(data.get('destination', {}))
        priority = data.get('priority', 3)
        
        # Get depot info
        depot_info = self.depots.get(depot_id, {})
        depot_name = depot_info.get('name', depot_id)
        
        # Get route info
        route_info = self.routes.get(route_id, {})
        route_name = route_info.get('long_name', route_id)
        
        # Display spawn event
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{Fore.YELLOW}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🚏 DEPOT SPAWN #{self.stats['depot_spawns']}{Style.RESET_ALL} @ {timestamp}")
        print(f"{Fore.YELLOW}{'='*80}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}Passenger ID:{Style.RESET_ALL} {commuter_id[:8]}...")
        print(f"  {Fore.GREEN}🏢 Depot:{Style.RESET_ALL} {depot_name}")
        print(f"     {Fore.CYAN}📍 Location:{Style.RESET_ALL} ({location.get('lat', 0):.4f}, {location.get('lon', 0):.4f})")
        print(f"  {Fore.BLUE}🚌 Route:{Style.RESET_ALL} {route_name}")
        print(f"  {Fore.MAGENTA}🎯 Destination:{Style.RESET_ALL} ({destination.get('lat', 0):.4f}, {destination.get('lon', 0):.4f})")
        print(f"  {Fore.YELLOW}⭐ Priority:{Style.RESET_ALL} {priority}")
        print(f"{Fore.YELLOW}{'='*80}{Style.RESET_ALL}\n")
    
    async def handle_route_spawn(self, data):
        """Handle route spawn event"""
        self.stats['route_spawns'] += 1
        self.stats['total_spawns'] += 1
        
        # Extract spawn data (handle both formats: passenger_id/spawn_location OR commuter_id/current_location)
        commuter_id = data.get('passenger_id') or data.get('commuter_id', 'unknown')
        route_id = data.get('route_id', 'unknown')
        location = self._normalize_location(data.get('spawn_location') or data.get('current_location', {}))
        destination = self._normalize_location(data.get('destination', {}))
        direction = data.get('direction', 'OUTBOUND')
        priority = data.get('priority', 3)
        
        # Get route info
        route_info = self.routes.get(route_id, {})
        route_name = route_info.get('long_name', route_id)
        
        # Display spawn event
        timestamp = datetime.now().strftime("%H:%M:%S")
        direction_icon = "⬆️" if direction == "inbound" else "⬇️"
        
        print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🛣️  ROUTE SPAWN #{self.stats['route_spawns']}{Style.RESET_ALL} @ {timestamp}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}Passenger ID:{Style.RESET_ALL} {commuter_id[:8]}...")
        print(f"  {Fore.BLUE}🚌 Route:{Style.RESET_ALL} {route_name}")
        print(f"     {Fore.CYAN}📍 Spawn Location:{Style.RESET_ALL} ({location.get('lat', 0):.4f}, {location.get('lon', 0):.4f})")
        print(f"  {direction_icon} {Fore.WHITE}Direction:{Style.RESET_ALL} {direction.upper()}")
        print(f"  {Fore.MAGENTA}🎯 Destination:{Style.RESET_ALL} ({destination.get('lat', 0):.4f}, {destination.get('lon', 0):.4f})")
        print(f"  {Fore.YELLOW}⭐ Priority:{Style.RESET_ALL} {priority}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")
    
    def print_stats(self):
        """Print current statistics"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        mins = int(uptime // 60)
        secs = int(uptime % 60)
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 SPAWN MONITOR STATISTICS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}🚏 Depot Spawns:{Style.RESET_ALL} {self.stats['depot_spawns']}")
        print(f"  {Fore.BLUE}🛣️  Route Spawns:{Style.RESET_ALL} {self.stats['route_spawns']}")
        print(f"  {Fore.YELLOW}📈 Total Spawns:{Style.RESET_ALL} {self.stats['total_spawns']}")
        print(f"  {Fore.WHITE}⏱️  Uptime:{Style.RESET_ALL} {mins}m {secs}s")
        if uptime > 0:
            rate = self.stats['total_spawns'] / uptime * 60
            print(f"  {Fore.MAGENTA}📊 Spawn Rate:{Style.RESET_ALL} {rate:.2f} passengers/minute")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    async def run(self):
        """Run the monitor"""
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔍 REAL-TIME PASSENGER SPAWN MONITOR{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        # Load API data
        await self.load_api_data()
        
        # Connect to Socket.IO
        connected = await self.connect()
        if not connected:
            print(f"{Fore.RED}❌ Failed to connect. Exiting.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Monitor is LIVE - Watching for spawn events...{Style.RESET_ALL}")
        print(f"{Fore.GREEN}   Press Ctrl+C to stop{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")
        
        # Keep running and print stats every 60 seconds
        try:
            while True:
                await asyncio.sleep(60)
                self.print_stats()
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}⚠️  Shutting down monitor...{Style.RESET_ALL}")
            self.print_stats()
            await self.sio.disconnect()
            print(f"{Fore.GREEN}✅ Monitor stopped{Style.RESET_ALL}\n")


async def main():
    monitor = SpawnMonitor()
    await monitor.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
        sys.exit(0)
