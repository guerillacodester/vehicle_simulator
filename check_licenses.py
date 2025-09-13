#!/usr/bin/env python3
"""Quick license check script."""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher

async def check_licenses():
    depot_manager = DepotManager('TestDepot')
    dispatcher = Dispatcher('TestFleetDispatcher', 'http://localhost:8000')
    depot_manager.set_dispatcher(dispatcher)
    
    await depot_manager.initialize()
    assignments = await depot_manager.dispatcher.get_vehicle_assignments()
    
    print("=== ACTUAL LICENSE DATA FROM DISPATCHER ===")
    for assignment in assignments:
        print(f'{assignment.driver_name}: License={assignment.driver_id}, Vehicle={assignment.vehicle_id}, Route={assignment.route_id}')

if __name__ == "__main__":
    asyncio.run(check_licenses())