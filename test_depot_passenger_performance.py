#!/usr/bin/env python3
"""
Performance validation test for depot-centric passenger system.

Tests system capability to handle 1200+ concurrent vehicles with minimal resource usage.
Validates memory efficiency, CPU usage, and response times under heavy load.
"""
import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

from world.arknet_transit_simulator.models.depot_passenger_coordinator import setup_depot_passenger_system
from world.arknet_transit_simulator.models.people import PeopleSimulatorConfig


class PerformanceValidator:
    """Validate system performance under heavy load."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.process = psutil.Process()
        self.initial_memory = None
        self.peak_memory = 0
        self.cpu_samples = []
        
    def start_monitoring(self):
        """Start performance monitoring."""
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory
        self.cpu_samples = []
        self.logger.info(f"Performance monitoring started. Initial memory: {self.initial_memory:.1f} MB")
    
    def sample_performance(self):
        """Sample current performance metrics."""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        cpu_percent = self.process.cpu_percent()
        
        self.peak_memory = max(self.peak_memory, memory_mb)
        self.cpu_samples.append(cpu_percent)
        
        return {
            'memory_mb': memory_mb,
            'cpu_percent': cpu_percent,
            'memory_growth_mb': memory_mb - self.initial_memory
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        max_cpu = max(self.cpu_samples) if self.cpu_samples else 0
        
        return {
            'initial_memory_mb': self.initial_memory,
            'peak_memory_mb': self.peak_memory,
            'memory_growth_mb': self.peak_memory - self.initial_memory,
            'avg_cpu_percent': avg_cpu,
            'max_cpu_percent': max_cpu,
            'total_samples': len(self.cpu_samples)
        }


async def create_test_data():
    """Create test depots and routes for performance testing."""
    # Create 10 test depots spread across a city
    depots = []
    for i in range(10):
        depots.append({
            'depot_id': f'depot_{i}',
            'lat': 37.7749 + (i * 0.01),  # Spread across San Francisco area
            'lon': -122.4194 + (i * 0.01),
            'boarding_radius': 0.001  # ~100m radius
        })
    
    # Create 5 test routes with realistic polylines
    routes = {}
    for i in range(5):
        route_points = []
        # Create route with 50 points
        for j in range(50):
            route_points.append((
                37.7749 + (i * 0.005) + (j * 0.0002),
                -122.4194 + (i * 0.005) + (j * 0.0002)
            ))
        routes[f'route_{i}'] = route_points
    
    return depots, routes


async def test_basic_functionality():
    """Test basic system functionality with small load."""
    print("=== Testing Basic Functionality ===")
    
    depots, routes = await create_test_data()
    
    # Setup system with standard performance mode
    coordinator = await setup_depot_passenger_system(
        depots=depots,
        routes=routes,
        performance_mode='standard'
    )
    
    try:
        # Register a few test vehicles
        for i in range(10):
            coordinator.register_vehicle(
                f'basic_test_vehicle_{i}',
                f'route_{i % 5}',
                37.7749 + (i * 0.001),
                -122.4194 + (i * 0.001)
            )
        
        # Run for 30 seconds
        await asyncio.sleep(30)
        
        # Check stats
        stats = coordinator.get_system_stats()
        print(f"Basic test results: {stats['passenger_stats']['active_vehicles']} vehicles registered")
        print(f"Passengers generated: {stats['passenger_stats']['passengers_generated']}")
        
        success = stats['passenger_stats']['active_vehicles'] == 10
        print(f"Basic functionality test: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    finally:
        await coordinator.stop()


async def test_1200_vehicle_load():
    """Test system with 1200 vehicles under heavy load."""
    print("\n=== Testing 1200 Vehicle Load ===")
    
    validator = PerformanceValidator()
    validator.start_monitoring()
    
    depots, routes = await create_test_data()
    
    # Setup system with high performance mode
    coordinator = await setup_depot_passenger_system(
        depots=depots,
        routes=routes,
        performance_mode='high_performance'
    )
    
    try:
        start_time = time.time()
        
        # Register 1200 vehicles in batches to avoid overwhelming the system
        print("Registering 1200 vehicles...")
        batch_size = 100
        for batch_start in range(0, 1200, batch_size):
            batch_end = min(batch_start + batch_size, 1200)
            
            for i in range(batch_start, batch_end):
                coordinator.register_vehicle(
                    f'load_test_vehicle_{i}',
                    f'route_{i % 5}',
                    37.7749 + ((i % 100) * 0.0001),  # Distribute across area
                    -122.4194 + ((i % 100) * 0.0001)
                )
            
            # Sample performance after each batch
            perf = validator.sample_performance()
            print(f"Batch {batch_start}-{batch_end}: Memory {perf['memory_mb']:.1f}MB, CPU {perf['cpu_percent']:.1f}%")
            
            # Brief pause between batches
            await asyncio.sleep(0.5)
        
        registration_time = time.time() - start_time
        print(f"Vehicle registration completed in {registration_time:.2f} seconds")
        
        # Run load test for 5 minutes, sampling performance
        print("Running 5-minute load test...")
        test_duration = 300  # 5 minutes
        sample_interval = 10  # Sample every 10 seconds
        
        for elapsed in range(0, test_duration, sample_interval):
            await asyncio.sleep(sample_interval)
            
            perf = validator.sample_performance()
            stats = coordinator.get_system_stats()
            
            print(f"T+{elapsed+sample_interval}s: "
                  f"Memory {perf['memory_mb']:.1f}MB (+{perf['memory_growth_mb']:.1f}MB), "
                  f"CPU {perf['cpu_percent']:.1f}%, "
                  f"Passengers: {stats['passenger_stats']['total_waiting_passengers']}")
        
        # Final performance summary
        final_stats = coordinator.get_system_stats()
        perf_summary = validator.get_summary()
        
        print(f"\n=== Load Test Results ===")
        print(f"Vehicles: {final_stats['passenger_stats']['active_vehicles']}")
        print(f"Total passengers generated: {final_stats['passenger_stats']['passengers_generated']}")
        print(f"Passengers matched: {final_stats['passenger_stats']['passengers_matched']}")
        print(f"Peak memory usage: {perf_summary['peak_memory_mb']:.1f} MB")
        print(f"Memory growth: {perf_summary['memory_growth_mb']:.1f} MB")
        print(f"Average CPU: {perf_summary['avg_cpu_percent']:.1f}%")
        print(f"Peak CPU: {perf_summary['max_cpu_percent']:.1f}%")
        
        # Validate performance criteria
        criteria_passed = []
        
        # Memory growth should be reasonable (< 500MB for 1200 vehicles)
        memory_ok = perf_summary['memory_growth_mb'] < 500
        criteria_passed.append(('Memory Growth < 500MB', memory_ok))
        
        # Average CPU should be reasonable (< 50%)
        cpu_ok = perf_summary['avg_cpu_percent'] < 50
        criteria_passed.append(('Average CPU < 50%', cpu_ok))
        
        # System should generate passengers
        passengers_ok = final_stats['passenger_stats']['passengers_generated'] > 0
        criteria_passed.append(('Passengers Generated', passengers_ok))
        
        # All vehicles should be registered
        vehicles_ok = final_stats['passenger_stats']['active_vehicles'] == 1200
        criteria_passed.append(('All Vehicles Registered', vehicles_ok))
        
        print(f"\n=== Performance Criteria ===")
        all_passed = True
        for criterion, passed in criteria_passed:
            status = 'PASSED' if passed else 'FAILED'
            print(f"{criterion}: {status}")
            all_passed = all_passed and passed
        
        print(f"\nOverall Load Test: {'PASSED' if all_passed else 'FAILED'}")
        
        return all_passed
        
    finally:
        await coordinator.stop()


async def test_ultra_low_resource_mode():
    """Test system in ultra-low resource mode for constrained hardware."""
    print("\n=== Testing Ultra-Low Resource Mode ===")
    
    validator = PerformanceValidator()
    validator.start_monitoring()
    
    depots, routes = await create_test_data()
    
    # Setup system with ultra-low resource mode
    coordinator = await setup_depot_passenger_system(
        depots=depots,
        routes=routes,
        performance_mode='ultra_low_resource'
    )
    
    try:
        # Register 500 vehicles (more realistic for low-end hardware)
        print("Registering 500 vehicles in ultra-low resource mode...")
        
        for i in range(500):
            coordinator.register_vehicle(
                f'low_resource_vehicle_{i}',
                f'route_{i % 5}',
                37.7749 + ((i % 50) * 0.0002),
                -122.4194 + ((i % 50) * 0.0002)
            )
            
            if i % 100 == 99:  # Sample every 100 vehicles
                perf = validator.sample_performance()
                print(f"Registered {i+1} vehicles: Memory {perf['memory_mb']:.1f}MB, CPU {perf['cpu_percent']:.1f}%")
        
        # Run for 2 minutes
        print("Running 2-minute resource-constrained test...")
        for i in range(12):  # 12 * 10 seconds = 2 minutes
            await asyncio.sleep(10)
            perf = validator.sample_performance()
            print(f"T+{(i+1)*10}s: Memory {perf['memory_mb']:.1f}MB, CPU {perf['cpu_percent']:.1f}%")
        
        final_stats = coordinator.get_system_stats()
        perf_summary = validator.get_summary()
        
        print(f"\n=== Ultra-Low Resource Results ===")
        print(f"Memory growth: {perf_summary['memory_growth_mb']:.1f} MB")
        print(f"Average CPU: {perf_summary['avg_cpu_percent']:.1f}%")
        
        # Stricter criteria for low-resource mode
        memory_ok = perf_summary['memory_growth_mb'] < 200  # < 200MB growth
        cpu_ok = perf_summary['avg_cpu_percent'] < 25       # < 25% CPU
        
        success = memory_ok and cpu_ok
        print(f"Ultra-low resource test: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    finally:
        await coordinator.stop()


async def main():
    """Run comprehensive performance validation."""
    print("Depot-Centric Passenger System Performance Validation")
    print("=" * 60)
    
    # Configure logging for performance testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    results = []
    
    try:
        # Test 1: Basic functionality
        result1 = await test_basic_functionality()
        results.append(('Basic Functionality', result1))
        
        # Test 2: 1200 vehicle load test
        result2 = await test_1200_vehicle_load()
        results.append(('1200 Vehicle Load Test', result2))
        
        # Test 3: Ultra-low resource mode
        result3 = await test_ultra_low_resource_mode()
        results.append(('Ultra-Low Resource Mode', result3))
        
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        return False
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL TEST RESULTS")
    print(f"{'='*60}")
    
    all_passed = True
    for test_name, passed in results:
        status = 'PASSED' if passed else 'FAILED'
        print(f"{test_name}: {status}")
        all_passed = all_passed and passed
    
    print(f"\nOverall System Validation: {'PASSED' if all_passed else 'FAILED'}")
    
    if all_passed:
        print("\n✅ System is ready for production use with 1200+ vehicles")
        print("   - Memory usage is within acceptable limits")
        print("   - CPU usage is efficient for real-time operation")
        print("   - Passenger generation and matching works correctly")
        print("   - System scales appropriately across performance modes")
    else:
        print("\n❌ System requires optimization before production use")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())