#!/usr/bin/env python3
"""
Test the people simulator with strict API and geojson integration.
This test verifies that the people simulator fails gracefully when API/data is unavailable
and works correctly when real data is available.
"""

import asyncio
import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'world'))

from vehicle_simulator.models.people import PeopleSimulator, PoissonDistributionModel, PeopleSimulatorConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_strict_people_simulator():
    """Test the people simulator with strict no-fallback requirements."""
    
    logger.info("Testing people simulator with strict API integration...")
    
    # Initialize with custom config for testing  
    config = PeopleSimulatorConfig(
        api_base_url="http://localhost:8000",
        api_version="v1",
        request_timeout=10
    )
    distribution_model = PoissonDistributionModel(config=config)
    people_simulator = PeopleSimulator(distribution_model)
    
    # Test with Route 1 (should work if geojson file exists)
    available_routes = ["route1"]
    
    try:
        logger.info("Attempting to generate passengers with strict mode...")
        
        # Generate passengers
        passengers = await people_simulator.generate_passengers(
            available_routes=available_routes,
            total_population=20,  # Small test population
            current_time="08:30"  # Peak morning time
        )
        
        logger.info(f"Successfully generated {len(passengers)} passengers!")
        
        # Display some passenger details
        for i, passenger in enumerate(passengers[:5]):  # Show first 5
            logger.info(f"Passenger {i+1}: {passenger.origin} -> {passenger.destination} "
                       f"(Route: {passenger.preferred_route})")
        
        return True
        
    except RuntimeError as e:
        logger.error(f"People simulator failed as expected in strict mode: {e}")
        logger.info("This is expected behavior when API or geojson data is unavailable")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

async def test_api_integration():
    """Test API integration for route coordinates (public endpoints only)."""
    
    logger.info("Testing public API integration...")
    
    # Initialize with custom config for testing
    config = PeopleSimulatorConfig(
        api_base_url="http://localhost:8000",
        api_version="v1", 
        request_timeout=10
    )
    distribution_model = PoissonDistributionModel(config=config)
    
    # Test route coordinate retrieval from public API
    try:
        route_coords = distribution_model._load_route_coordinates_from_api("route1")
        if route_coords and len(route_coords) > 0:
            logger.info(f"Successfully retrieved route coordinates: {len(route_coords)} points")
            return True
        else:
            logger.warning("Public API returned no route coordinates")
            return False
            
    except Exception as e:
        logger.error(f"Public API integration failed: {e}")
        logger.info("Make sure the fleet manager API is running on localhost:8000")
        return False

def test_api_route_loading():
    """Test API-based route coordinate loading."""
    
    logger.info("Testing API route coordinate loading...")
    
    # Initialize with custom config for testing
    config = PeopleSimulatorConfig(
        api_base_url="http://localhost:8000",
        api_version="v1",
        request_timeout=10
    )
    distribution_model = PoissonDistributionModel(config=config)
    
    # Test route coordinate loading from API
    try:
        route_coords = distribution_model._load_route_coordinates_from_api("route1")
        if route_coords and len(route_coords) > 0:
            logger.info(f"Successfully loaded {len(route_coords)} route coordinates from API")
            logger.info(f"First coordinate: {route_coords[0]}")
            logger.info(f"Last coordinate: {route_coords[-1]}")
            return True
        else:
            logger.warning("No route coordinates found from API")
            return False
            
    except Exception as e:
        logger.error(f"API route loading failed: {e}")
        return False

async def main():
    """Run all tests."""
    
    logger.info("=== People Simulator Strict Mode Test ===")
    
    # Test 1: API route loading
    logger.info("\n--- Test 1: API Route Loading ---")
    route_ok = test_api_route_loading()
    
    # Test 2: Public API integration
    logger.info("\n--- Test 2: Public API Integration ---")
    api_ok = await test_api_integration()
    
    # Test 3: Full passenger generation
    logger.info("\n--- Test 3: Full Passenger Generation ---")
    if route_ok and api_ok:
        passenger_ok = await test_strict_people_simulator()
    else:
        logger.info("Skipping passenger generation test (public API data unavailable)")
        passenger_ok = False
    
    # Summary
    logger.info("\n=== Test Results ===")
    logger.info(f"Route API Loading: {'✓ PASS' if route_ok else '✗ FAIL'}")
    logger.info(f"Public API Integration: {'✓ PASS' if api_ok else '✗ FAIL'}")
    logger.info(f"Passenger Generation: {'✓ PASS' if passenger_ok else '✗ FAIL'}")
    
    if route_ok and api_ok and passenger_ok:
        logger.info("\n🎉 People simulator is working with public API data!")
    elif route_ok or api_ok:
        logger.info("\n⚠️  People simulator has partial public API integration")
    else:
        logger.info("\n❌ People simulator requires public API data to function")
    
    logger.info("\nNote: In strict mode, all failures are expected when API is unavailable.")
    logger.info("The simulator will not use fallback coordinates - it requires live API data.")

if __name__ == "__main__":
    asyncio.run(main())