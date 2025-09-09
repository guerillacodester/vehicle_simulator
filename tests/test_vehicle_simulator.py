#!/usr/bin/env python3
"""
Test Vehicle Simulator Structure
"""

import sys
import os

# Add paths
sys.path.append('.')

def test_basic_structure():
    """Test basic file structure"""
    try:
        # Test interface import
        from world.vehicle_simulator.interfaces.route_provider import IRouteProvider
        print("✅ Interface import works")
        
        # Test file provider import  
        from world.vehicle_simulator.providers.file_route_provider import FileRouteProvider
        print("✅ File provider import works")
        
        # Test config provider
        from world.vehicle_simulator.providers.config_provider import SelfContainedConfigProvider
        print("✅ Config provider import works")
        
        # Test standalone manager
        from world.vehicle_simulator.core.standalone_manager import StandaloneFleetManager
        print("✅ Standalone manager import works")
        
        # Test functionality
        provider = FileRouteProvider()
        routes = provider.list_available_routes()
        print(f"✅ Available routes: {routes}")
        
        fleet_manager = StandaloneFleetManager()
        print("✅ Fleet manager created successfully")
        
        print("\n🎉 Vehicle Simulator structure is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_structure()
    sys.exit(0 if success else 1)
