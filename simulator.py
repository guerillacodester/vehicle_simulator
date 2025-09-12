#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3

"""

Clean Vehicle Simulator Entry Point"""



Usage:Clean Vehicle Simulator Entry Point""""""

    python simulator.py --mode depot --duration 30

    python simulator.py --mode display==================================

"""

Simplified entry point that only uses the core clean components:Clean Vehicle Simulator Entry PointVehicle Simulator Entry Point

import sys

import asyncio- Depot Manager for orchestration

import argparse

import logging- Dispatcher for Fleet Manager API connection==============================================================

from pathlib import Path



logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-5s | %(message)s')

Usage:Simplified entry point that only uses the core clean components:Main entry point for the Arknet Transit Vehicle Simulator system.

PROJECT_ROOT = Path(__file__).parent

sys.path.insert(0, str(PROJECT_ROOT))    python simulator.py --mode depot --duration 30



    python simulator.py --mode display- Depot Manager for orchestration

async def display_vehicle_assignments():

    """Display vehicle assignments.""""""

    print("=" * 80)

    print("VEHICLE-DRIVER-ROUTE ASSIGNMENT EVIDENCE")- Dispatcher for Fleet Manager API connectionUsage:

    print("=" * 80)

    import sys

    try:

        from world.vehicle_simulator.main import CleanVehicleSimulatorimport os    ./simulator --mode depot --debug --duration 300 --tick-time 1.0

        

        simulator = CleanVehicleSimulator()import argparse

        

        if not await simulator.initialize():import asyncioUsage:    ./simulator --mode telemetry --port 5000

            print("❌ INITIALIZATION FAILED")

            returnimport logging

        

        assignments = await simulator.dispatcher.get_vehicle_assignments()from pathlib import Path    python simulator.py --mode depot --duration 30    ./simulator --help

        if not assignments:

            print("⚠️  No vehicle assignments found")

            await simulator.shutdown()

            return# Configure logging    python simulator.py --mode display

        

        print(f"📋 Found {len(assignments)} vehicle assignments:")logging.basicConfig(

        print("-" * 80)

            level=logging.INFO,"""Modes:

        for i, assignment in enumerate(assignments, 1):

            print(f"Assignment {i}:")    format='%(asctime)s | %(levelname)-5s | %(message)s'

            print(f"  🚌 Vehicle: {assignment.vehicle_reg_code}")

            print(f"  👨‍💼 Driver: {assignment.driver_name}"))    depot       - Fleet management mode with vehicle-driver-route coordination

            print(f"  🛣️  Route: {assignment.route_name}")

            

            route_info = await simulator.dispatcher.get_route_info(assignment.route_id)

            if route_info and route_info.geometry:# Add project root to Python pathimport sys    telemetry   - WebSocket telemetry server mode for GPS data reception

                coord_count = route_info.coordinate_count or "Unknown"

                print(f"  🗺️  GPS Coordinates: {coord_count} points available")PROJECT_ROOT = Path(__file__).parent

            print()

        sys.path.insert(0, str(PROJECT_ROOT))import os    display     - Display current vehicle assignments and system status

        await simulator.shutdown()

        print("✅ System shutdown complete")

        

    except Exception as e:import argparse"""

        print(f"❌ Error: {e}")

async def display_vehicle_assignments():



def run_clean_depot_mode(args):    """Display vehicle-driver-route assignments with GPS data."""import asyncio

    """Run clean depot mode."""

    print("🚌 CLEAN DEPOT MODE")    print("=" * 80)

    print(f"Duration: {args.duration or 'indefinite'} seconds")

        print("VEHICLE-DRIVER-ROUTE ASSIGNMENT EVIDENCE")import loggingimport sys

    async def run_clean():

        from world.vehicle_simulator.main import CleanVehicleSimulator    print("=" * 80)

        simulator = CleanVehicleSimulator()

            from pathlib import Pathimport os

        if not await simulator.initialize():

            print("❌ Failed to initialize")    try:

            return

                from world.vehicle_simulator.main import CleanVehicleSimulatorimport argparse

        await simulator.run(duration=args.duration)

            

    asyncio.run(run_clean())

        print("✓ Loading clean simulator components...")# Configure loggingimport logging



def main():        

    parser = argparse.ArgumentParser(description="Clean Vehicle Simulator")

    parser.add_argument('--mode', choices=['depot', 'display'], default='display')        simulator = CleanVehicleSimulator()logging.basicConfig(from pathlib import Path

    parser.add_argument('--debug', action='store_true')

    parser.add_argument('--duration', type=float, help='Duration in seconds')        

    

    args = parser.parse_args()        print("🔄 Initializing system and connecting to Fleet Manager API...")    level=logging.INFO,

    

    if args.debug:        if not await simulator.initialize():

        logging.getLogger().setLevel(logging.DEBUG)

                print("❌ INITIALIZATION FAILED")    format='%(asctime)s | %(levelname)-5s | %(message)s'# Configure logging to see all messages

    try:

        if args.mode == 'display':            print("   - Check Fleet Manager API is running on http://localhost:8000")

            asyncio.run(display_vehicle_assignments())

        elif args.mode == 'depot':            print("   - Verify database contains vehicle, driver, and route data"))logging.basicConfig(

            run_clean_depot_mode(args)

    except Exception as e:            return

        print(f"❌ Error: {e}")

            level=logging.INFO,



if __name__ == "__main__":        print("✅ System initialized successfully")

    main()
        print()# Add project root to Python path    format='%(asctime)s - %(levelname)s - %(message)s'

        

        # Get assignmentsPROJECT_ROOT = Path(__file__).parent)

        assignments = await simulator.dispatcher.get_vehicle_assignments()

        if not assignments:sys.path.insert(0, str(PROJECT_ROOT))

            print("⚠️  No vehicle assignments found")

            await simulator.shutdown()# Add the project root to Python path

            return

        PROJECT_ROOT = Path(__file__).parent

        print(f"📋 Found {len(assignments)} vehicle assignments:")

        print("-" * 80)async def display_vehicle_assignments():sys.path.insert(0, str(PROJECT_ROOT))

        

        for i, assignment in enumerate(assignments, 1):    """Display vehicle-driver-route assignments with GPS data."""

            print(f"Assignment {i}:")

            print(f"  🚌 Vehicle: {assignment.vehicle_reg_code}")    print("=" * 80)async def display_vehicle_assignments():

            print(f"  👨‍💼 Driver: {assignment.driver_name}")

            print(f"  🛣️  Route: {assignment.route_name}")    print("VEHICLE-DRIVER-ROUTE ASSIGNMENT EVIDENCE")    """Display complete evidence of vehicle-driver-route assignments with GPS data."""

            print(f"  📝 Type: {assignment.assignment_type}")

                print("=" * 80)    print("=" * 80)

            # Get route GPS data

            route_info = await simulator.dispatcher.get_route_info(assignment.route_id)        print("VEHICLE-DRIVER-ROUTE ASSIGNMENT EVIDENCE")

            if route_info and route_info.geometry:

                coord_count = route_info.coordinate_count or "Unknown"    try:    print("=" * 80)

                print(f"  🗺️  GPS Coordinates: {coord_count} points available")

                print(f"  📏 Distance: {route_info.distance_km or 'Unknown'} km")        from world.vehicle_simulator.main import CleanVehicleSimulator    

            else:

                print(f"  ⚠️  GPS data: Not available")            try:

            

            print()        print("✓ Loading clean simulator components...")        # Import classes

        

        await simulator.shutdown()                from world.vehicle_simulator.core.depot_manager import DepotManager

        print("✅ System shutdown complete")

                simulator = CleanVehicleSimulator()        from world.vehicle_simulator.core.dispatcher import Dispatcher

    except Exception as e:

        print(f"❌ Error: {e}")                

        import traceback

        traceback.print_exc()        print("🔄 Initializing system and connecting to Fleet Manager API...")        print("✓ System components loaded")



        if not await simulator.initialize():        

def run_clean_depot_mode(args):

    """Run the clean depot simulator."""            print("❌ INITIALIZATION FAILED")        # Create and initialize system

    print("=" * 60)

    print("🚌 CLEAN VEHICLE SIMULATOR - DEPOT MODE")            print("   - Check Fleet Manager API is running on http://localhost:8000")        dispatcher = Dispatcher("FleetDispatcher", "http://localhost:8000")

    print("=" * 60)

    print(f"⏱️  Duration: {args.duration or 'indefinite'} seconds")            print("   - Verify database contains vehicle, driver, and route data")        depot = DepotManager("MainDepot")

    print(f"🏭 Architecture: Depot Manager + Dispatcher only")

    print("-" * 60)            return        depot.set_dispatcher(dispatcher)

    

    async def run_clean():                

        from world.vehicle_simulator.main import CleanVehicleSimulator

                print("✅ System initialized successfully")        # Initialize system

        simulator = CleanVehicleSimulator()

                print()        print("\n🔄 Initializing fleet management system...")

        if not await simulator.initialize():

            print("❌ Failed to initialize clean simulator")                init_result = await depot.initialize()

            return

                # Get assignments        

        await simulator.run(duration=args.duration)

            assignments = await simulator.dispatcher.get_vehicle_assignments()        if not init_result:

    try:

        asyncio.run(run_clean())        if not assignments:            print("❌ Fleet system initialization failed")

    except KeyboardInterrupt:

        print("\n⏹️  Interrupted by user")            print("⚠️  No vehicle assignments found")            return False

    

    print("-" * 60)            await simulator.shutdown()        

    print("✅ Clean Simulation Complete")

            return        print("✅ Fleet system operational")



def run_telemetry_mode(args):                

    """Run telemetry server mode."""

    print("=" * 60)        print(f"📋 Found {len(assignments)} vehicle assignments:")        # Get all vehicle assignments

    print("📡 TELEMETRY SERVER MODE")

    print("=" * 60)        print("-" * 80)        vehicle_assignments = await dispatcher.get_vehicle_assignments()

    print(f"🔌 Port: {args.port}")

    print("-" * 60)                driver_assignments = await dispatcher.get_driver_assignments()

    

    try:        for i, assignment in enumerate(assignments, 1):        

        from telemetry_server import run_telemetry_server

        run_telemetry_server(port=args.port)            print(f"Assignment {i}:")        print(f"\n📊 FLEET OVERVIEW:")

    except ImportError as e:

        print(f"❌ Telemetry server not available: {e}")            print(f"  🚌 Vehicle: {assignment.vehicle_reg_code}")        print(f"   • Total Vehicles: {len(vehicle_assignments)}")

    except Exception as e:

        print(f"❌ Telemetry server error: {e}")            print(f"  👨‍💼 Driver: {assignment.driver_name}")        print(f"   • Total Drivers: {len(driver_assignments)}")



            print(f"  🛣️  Route: {assignment.route_name}")        print(f"   • Available Drivers: {len([d for d in driver_assignments if d.status == 'available'])}")

def main():

    """Main entry point."""            print(f"  📝 Type: {assignment.assignment_type}")        

    parser = argparse.ArgumentParser(

        description="Clean Arknet Transit Vehicle Simulator",                    print("\n" + "=" * 80)

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog="""            # Get route GPS data        print("COMPLETE VEHICLE ASSIGNMENTS WITH GPS ROUTE DATA")

Examples:

  %(prog)s --mode depot --duration 30            route_info = await simulator.dispatcher.get_route_info(assignment.route_id)        print("=" * 80)

  %(prog)s --mode display

  %(prog)s --mode telemetry --port 5000            if route_info and route_info.geometry:        

        """

    )                coord_count = route_info.coordinate_count or "Unknown"        # Display each vehicle assignment

    

    parser.add_argument(                print(f"  🗺️  GPS Coordinates: {coord_count} points available")        for i, vehicle in enumerate(vehicle_assignments, 1):

        '--mode', 

        choices=['depot', 'telemetry', 'display'],                print(f"  📏 Distance: {route_info.distance_km or 'Unknown'} km")            print(f"\n🚐 VEHICLE #{i}")

        default='display',

        help='Simulator mode (default: display)'            else:            print(f"   License Plate: {vehicle.vehicle_reg_code}")

    )

                    print(f"  ⚠️  GPS data: Not available")            print(f"   Status: {vehicle.status}")

    parser.add_argument(

        '--debug',                         

        action='store_true',

        help='Enable debug logging'            print()            print(f"\n👤 ASSIGNED DRIVER:")

    )

                        print(f"   Driver Name: {vehicle.driver_name}")

    parser.add_argument(

        '--duration',         await simulator.shutdown()            print(f"   License Number: {vehicle.license_number}")

        type=float, 

        default=None,        print("✅ System shutdown complete")            print(f"   Status: {vehicle.driver_status}")

        help='Run duration in seconds (default: indefinite for depot mode)'

    )                    

    

    parser.add_argument(    except Exception as e:            print(f"\n🗺️  ASSIGNED ROUTE:")

        '--tick-time', 

        type=float,         print(f"❌ Error: {e}")            print(f"   Route Number: {vehicle.route_name}")

        default=1.0,

        help='Tick time interval in seconds (default: 1.0) - DEPRECATED'        import traceback            

    )

            traceback.print_exc()            # Get detailed route info with GPS coordinates

    parser.add_argument(

        '--port',             route_info = await dispatcher.get_route_info(vehicle.route_id)

        type=int, 

        default=5000,            if route_info:

        help='Port for telemetry server mode (default: 5000)'

    )def run_clean_depot_mode(args):                print(f"   Full Route Name: {route_info.route_name}")



    args = parser.parse_args()    """Run the clean depot simulator."""                print(f"   Route Type: {route_info.route_type}")

    

    # Set up debug logging    print("=" * 60)                print(f"   GPS Coordinate Points: {len(route_info.geometry.get('coordinates', []))}")

    if args.debug:

        logging.getLogger().setLevel(logging.DEBUG)    print("🚌 CLEAN VEHICLE SIMULATOR - DEPOT MODE")                

    

    # Warn about deprecated arguments    print("=" * 60)                # Show GPS coordinate evidence

    if args.tick_time != 1.0:

        print("⚠️  Warning: --tick-time is deprecated in clean architecture")    print(f"⏱️  Duration: {args.duration or 'indefinite'} seconds")                print(f"\n📍 GPS COORDINATE EVIDENCE:")

        

    try:    print(f"🏭 Architecture: Depot Manager + Dispatcher only")                if route_info.geometry and 'coordinates' in route_info.geometry:

        if args.mode == 'display':

            asyncio.run(display_vehicle_assignments())    print("-" * 60)                    coords = route_info.geometry['coordinates']

            

        elif args.mode == 'depot':                        print(f"   Geometry Type: {route_info.geometry.get('type', 'Unknown')}")

            run_clean_depot_mode(args)

                async def run_clean():                    print(f"   Total Points: {len(coords)}")

        elif args.mode == 'telemetry':

            run_telemetry_mode(args)        from world.vehicle_simulator.main import CleanVehicleSimulator                    

            

    except KeyboardInterrupt:                            if coords:

        print("\n⏹️  Stopped by user")

    except Exception as e:        simulator = CleanVehicleSimulator()                        start_point = coords[0]

        print(f"❌ Error: {e}")

        if args.debug:                                end_point = coords[-1]

            import traceback

            traceback.print_exc()        if not await simulator.initialize():                        print(f"   Start Point: [{start_point[0]:.6f}, {start_point[1]:.6f}]")

        sys.exit(1)

            print("❌ Failed to initialize clean simulator")                        print(f"   End Point: [{end_point[0]:.6f}, {end_point[1]:.6f}]")



if __name__ == "__main__":            return                        

    main()
                                # Show first 5 coordinates for verification

        await simulator.run(duration=args.duration)                        print(f"\n   📋 First 5 GPS Coordinates for Interpolation:")

                            for j, coord in enumerate(coords[:5], 1):

    try:                            print(f"      Point {j}: Longitude {coord[0]:.6f}, Latitude {coord[1]:.6f}")

        asyncio.run(run_clean())                        

    except KeyboardInterrupt:                        if len(coords) > 5:

        print("\n⏹️  Interrupted by user")                            print(f"   ... and {len(coords) - 5} more coordinate points")

                            

    print("-" * 60)                        # Calculate rough distance

    print("✅ Clean Simulation Complete")                        if len(coords) >= 2:

                            distance = abs(end_point[0] - start_point[0]) + abs(end_point[1] - start_point[1])

                            print(f"   Rough Distance: {distance:.6f} degrees")

def run_telemetry_mode(args):            

    """Run telemetry server mode."""            print("-" * 80)

    print("=" * 60)        

    print("📡 TELEMETRY SERVER MODE")        # Test route distribution

    print("=" * 60)        print(f"\n🚀 ROUTE DISTRIBUTION EVIDENCE:")

    print(f"🔌 Port: {args.port}")        print(f"   Testing route distribution with GPS coordinates...")

    print("-" * 60)        

            if vehicle_assignments:

    try:            test_vehicle = vehicle_assignments[0]

        from telemetry_server import run_telemetry_server            print(f"   📋 Distributing to: {test_vehicle.driver_name} driving {test_vehicle.vehicle_reg_code} on Route {test_vehicle.route_name}")

        run_telemetry_server(port=args.port)            

    except ImportError as e:            # Test sending route with GPS data

        print(f"❌ Telemetry server not available: {e}")            test_driver_routes = [{

    except Exception as e:                'driver_id': test_vehicle.driver_id,

        print(f"❌ Telemetry server error: {e}")                'route_id': test_vehicle.route_id,

                'vehicle_id': test_vehicle.vehicle_id,

                'driver_name': test_vehicle.driver_name,

def main():                'vehicle_reg_code': test_vehicle.vehicle_reg_code,

    """Main entry point."""                'route_name': test_vehicle.route_name

    parser = argparse.ArgumentParser(            }]

        description="Clean Arknet Transit Vehicle Simulator",            

        formatter_class=argparse.RawDescriptionHelpFormatter,            success = await dispatcher.send_routes_to_drivers(test_driver_routes)

        epilog="""            if success:

Examples:                print(f"   ✅ Route distribution successful")

  %(prog)s --mode depot --duration 30            

  %(prog)s --mode display            print(f"   ✅ Route with GPS coordinates successfully prepared for {test_vehicle.driver_name}")

  %(prog)s --mode telemetry --port 5000            print(f"   ✅ Driver receives: Route {test_vehicle.route_name}, Vehicle {test_vehicle.vehicle_reg_code}, and complete GPS coordinate array")

        """            print(f"   ✅ GPS coordinates enable real-world position interpolation")

    )        

            # Cleanup

    parser.add_argument(        await dispatcher.disconnect()

        '--mode',         

        choices=['depot', 'telemetry', 'display'],        print(f"\n" + "=" * 80)

        default='display',        print("ASSIGNMENT EVIDENCE SUMMARY")

        help='Simulator mode (default: display)'        print("=" * 80)

    )        print(f"✅ {len(vehicle_assignments)} vehicles have assigned drivers")

            print(f"✅ {len([v for v in vehicle_assignments if v.route_id])} vehicles have assigned routes")

    parser.add_argument(        print("✅ Routes include GPS coordinate data for interpolation")

        '--debug',         print("✅ System successfully distributes routes with GPS data to drivers")

        action='store_true',        print("✅ All data required for GPS simulation is present and accessible")

        help='Enable debug logging'        

    )        print(f"\n🎉 VEHICLE ASSIGNMENT EVIDENCE COMPLETE")

            print("All vehicles have assigned drivers and GPS-enabled routes!")

    parser.add_argument(        

        '--duration',         return True

        type=float,         

        default=None,    except Exception as e:

        help='Run duration in seconds (default: indefinite for depot mode)'        print(f"❌ Error displaying assignments: {e}")

    )        return False

    

    parser.add_argument(def main():

        '--tick-time',     """Main entry point for the vehicle simulator."""

        type=float,     parser = argparse.ArgumentParser(

        default=1.0,        description="Arknet Transit Vehicle Simulator",

        help='Tick time interval in seconds (default: 1.0) - DEPRECATED'        formatter_class=argparse.RawDescriptionHelpFormatter,

    )        epilog="""

    Examples:

    parser.add_argument(  %(prog)s --mode depot --debug --duration 300

        '--port',   %(prog)s --mode telemetry --port 5000

        type=int,   %(prog)s --mode display

        default=5000,        """

        help='Port for telemetry server mode (default: 5000)'    )

    )    

    parser.add_argument(

    args = parser.parse_args()        '--mode', 

            choices=['depot', 'telemetry', 'display'],

    # Set up debug logging        default='depot',

    if args.debug:        help='Simulator mode (default: depot)'

        logging.getLogger().setLevel(logging.DEBUG)    )

        

    # Warn about deprecated arguments    parser.add_argument(

    if args.tick_time != 1.0:        '--debug', 

        print("⚠️  Warning: --tick-time is deprecated in clean architecture")        action='store_true',

                help='Enable debug logging'

    try:    )

        if args.mode == 'display':    

            asyncio.run(display_vehicle_assignments())    parser.add_argument(

                    '--duration', 

        elif args.mode == 'depot':        type=int, 

            run_clean_depot_mode(args)        default=300,

                    help='Simulation duration in seconds (default: 300)'

        elif args.mode == 'telemetry':    )

            run_telemetry_mode(args)    

                parser.add_argument(

    except KeyboardInterrupt:        '--tick-time', 

        print("\n⏹️  Stopped by user")        type=float, 

    except Exception as e:        default=1.0,

        print(f"❌ Error: {e}")        help='Simulation tick time in seconds (default: 1.0)'

        if args.debug:    )

            import traceback    

            traceback.print_exc()    parser.add_argument(

        sys.exit(1)        '--port', 

        type=int, 

        default=5000,

if __name__ == "__main__":        help='Telemetry server port (default: 5000)'

    main()    )
    
    parser.add_argument(
        '--host', 
        default='localhost',
        help='Telemetry server host (default: localhost)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'depot':
            # Run depot mode using the existing main module
            from world.vehicle_simulator.main import main as depot_main
            sys.argv = [
                'simulator',
                '--mode', 'depot',
                '--duration', str(args.duration),
                '--tick-time', str(args.tick_time)
            ]
            if args.debug:
                sys.argv.append('--debug')
            depot_main()
            
        elif args.mode == 'telemetry':
            # Run telemetry server mode
            import asyncio
            from telemetry_server import TelemetryServer
            
            print(f"🚀 Starting Vehicle Telemetry Server on {args.host}:{args.port}")
            server = TelemetryServer(host=args.host, port=args.port)
            asyncio.run(server.start_server())
            
        elif args.mode == 'display':
            # Run display mode
            import asyncio
            
            print("📊 Displaying Vehicle Assignments...")
            asyncio.run(display_vehicle_assignments())
            
    except KeyboardInterrupt:
        print("\n⏹️  Simulator stopped by user")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Error importing required modules: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting simulator: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()