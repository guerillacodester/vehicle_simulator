#!/usr/bin/env python3
"""
Definitive Passenger Spawning Test - Temporal and Spatial Analysis
================================================================

This script provides comprehensive validation of passenger spawning across:
- All depot locations with GPS coordinates
- Route stops with geometry data  
- POI categories with attraction-based spawning
- Temporal patterns across full 24-hour cycle
- Statistical validation of Poisson mathematics

Output: Detailed spawn count analysis + CSV data for visualization
"""

import asyncio
import csv
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))
from production_api_data_source import ProductionApiDataSource

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PassengerSpawningAnalyzer:
    """Comprehensive passenger spawning analysis and validation system."""
    
    def __init__(self):
        self.data_source = ProductionApiDataSource()
        self.spawn_data = []
        self.temporal_stats = {}
        self.location_stats = {}
        
    async def initialize(self):
        """Initialize the production data source."""
        logger.info("🔄 Initializing ProductionApiDataSource...")
        success = await self.data_source.initialize()
        if not success:
            raise RuntimeError("Failed to initialize data source")
        logger.info("✅ Data source initialized successfully")
        
    async def run_comprehensive_analysis(self) -> Dict:
        """Run complete 24-hour spawning analysis."""
        logger.info("🚀 Starting comprehensive passenger spawning analysis...")
        
        results = {
            'temporal_analysis': {},
            'spatial_analysis': {},
            'statistics': {},
            'validation': {},
            'export_data': []
        }
        
        # Analyze spawning patterns across 24 hours
        logger.info("📊 Analyzing temporal patterns (24-hour cycle)...")
        for hour in range(24):
            hour_data = await self.analyze_hour_spawning(hour)
            results['temporal_analysis'][hour] = hour_data
            
            # Add to export data for visualization
            for spawn in hour_data['spawns']:
                spawn['hour'] = hour
                results['export_data'].append(spawn)
                
        # Calculate comprehensive statistics
        results['statistics'] = self.calculate_statistics(results['temporal_analysis'])
        
        # Validate against expected patterns
        results['validation'] = self.validate_spawning_patterns(results['temporal_analysis'])
        
        # Analyze spatial distribution
        results['spatial_analysis'] = self.analyze_spatial_distribution(results['export_data'])
        
        logger.info("✅ Comprehensive analysis complete!")
        return results
    
    async def analyze_hour_spawning(self, hour: int) -> Dict:
        """Analyze passenger spawning for a specific hour."""
        logger.info(f"⏰ Analyzing hour {hour}:00...")
        
        # Create datetime for the specific hour
        base_date = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # Use geographic bounds from the data source
        bounds = self.data_source._geographic_bounds or self.data_source._fallback_bounds
        location_bounds = {
            'min_lat': bounds.min_lat,
            'max_lat': bounds.max_lat,
            'min_lon': bounds.min_lon,
            'max_lon': bounds.max_lon
        }
        
        # Generate passengers for 1-hour timeframe (60 minutes)
        passengers = self.data_source.get_passengers_for_timeframe(
            start_time=base_date,
            duration_minutes=60,     # 1 hour duration
            location_bounds=location_bounds
        )
        
        # Categorize spawns by location type
        spawns_by_type = {'depot': [], 'route': [], 'poi': []}
        
        for passenger in passengers:
            spawn_info = {
                'passenger_id': passenger['id'],
                'location': {
                    'lat': passenger['latitude'],
                    'lon': passenger['longitude']
                },
                'destination_type': passenger['destination_type'],
                'spawn_time': passenger['pickup_time'].isoformat() if isinstance(passenger['pickup_time'], datetime) else str(passenger['pickup_time']),
                'location_name': passenger.get('poi_category', 'Unknown')
            }
            
            # Determine spawn location type based on destination or location analysis
            location_type = self.determine_location_type(passenger, spawn_info)
            spawns_by_type[location_type].append(spawn_info)
        
        return {
            'hour': hour,
            'total_spawns': len(passengers),
            'spawns_by_type': {
                'depot': len(spawns_by_type['depot']),
                'route': len(spawns_by_type['route']), 
                'poi': len(spawns_by_type['poi'])
            },
            'spawns': spawns_by_type['depot'] + spawns_by_type['route'] + spawns_by_type['poi'],
            'geographic_bounds': {
                'min_lat': min(p['latitude'] for p in passengers) if passengers else 0,
                'max_lat': max(p['latitude'] for p in passengers) if passengers else 0,
                'min_lon': min(p['longitude'] for p in passengers) if passengers else 0,
                'max_lon': max(p['longitude'] for p in passengers) if passengers else 0
            }
        }
    
    def determine_location_type(self, passenger, spawn_info: Dict) -> str:
        """Determine if spawn is at depot, route, or POI based on destination."""
        if passenger['destination_type'] == 'depot':
            return 'depot'
        elif passenger['destination_type'] == 'route':
            return 'route'
        else:
            return 'poi'
    
    def calculate_statistics(self, temporal_data: Dict) -> Dict:
        """Calculate comprehensive statistics from temporal analysis."""
        logger.info("📈 Calculating spawning statistics...")
        
        hourly_totals = [data['total_spawns'] for data in temporal_data.values()]
        depot_counts = [data['spawns_by_type']['depot'] for data in temporal_data.values()]
        route_counts = [data['spawns_by_type']['route'] for data in temporal_data.values()]
        poi_counts = [data['spawns_by_type']['poi'] for data in temporal_data.values()]
        
        return {
            'total_daily_spawns': sum(hourly_totals),
            'hourly_statistics': {
                'mean': statistics.mean(hourly_totals),
                'median': statistics.median(hourly_totals),
                'std_dev': statistics.stdev(hourly_totals) if len(hourly_totals) > 1 else 0,
                'min': min(hourly_totals),
                'max': max(hourly_totals)
            },
            'peak_hours': {
                'highest_spawn_hour': hourly_totals.index(max(hourly_totals)),
                'lowest_spawn_hour': hourly_totals.index(min(hourly_totals)),
                'rush_hour_morning': self.calculate_rush_hour(hourly_totals, 6, 10),
                'rush_hour_evening': self.calculate_rush_hour(hourly_totals, 16, 20)
            },
            'distribution_by_type': {
                'depot_total': sum(depot_counts),
                'route_total': sum(route_counts), 
                'poi_total': sum(poi_counts),
                'depot_percentage': sum(depot_counts) / sum(hourly_totals) * 100 if sum(hourly_totals) > 0 else 0,
                'route_percentage': sum(route_counts) / sum(hourly_totals) * 100 if sum(hourly_totals) > 0 else 0,
                'poi_percentage': sum(poi_counts) / sum(hourly_totals) * 100 if sum(hourly_totals) > 0 else 0
            }
        }
    
    def calculate_rush_hour(self, hourly_totals: List[int], start_hour: int, end_hour: int) -> Dict:
        """Calculate rush hour statistics."""
        rush_hours = hourly_totals[start_hour:end_hour]
        if not rush_hours:
            return {'average': 0, 'peak_hour': start_hour}
            
        peak_index = rush_hours.index(max(rush_hours))
        return {
            'average': sum(rush_hours) / len(rush_hours),
            'peak_hour': start_hour + peak_index,
            'peak_count': max(rush_hours)
        }
    
    def validate_spawning_patterns(self, temporal_data: Dict) -> Dict:
        """Validate spawning patterns against expected behavior."""
        logger.info("✅ Validating spawning patterns...")
        
        validation_results = {
            'rush_hour_validation': self.validate_rush_hours(temporal_data),
            'geographic_validation': self.validate_geographic_bounds(temporal_data),
            'mathematical_validation': self.validate_poisson_distribution(temporal_data),
            'temporal_consistency': self.validate_temporal_consistency(temporal_data)
        }
        
        # Calculate overall validation score
        passed_tests = sum(1 for result in validation_results.values() if result.get('passed', False))
        total_tests = len(validation_results)
        
        validation_results['overall_score'] = {
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            'status': 'PASSED' if passed_tests == total_tests else 'PARTIAL' if passed_tests > 0 else 'FAILED'
        }
        
        return validation_results
    
    def validate_rush_hours(self, temporal_data: Dict) -> Dict:
        """Validate that rush hours show higher spawning."""
        morning_rush = [temporal_data[h]['total_spawns'] for h in [7, 8, 9]]
        evening_rush = [temporal_data[h]['total_spawns'] for h in [17, 18, 19]]
        off_peak = [temporal_data[h]['total_spawns'] for h in [2, 3, 23]]
        
        morning_avg = sum(morning_rush) / len(morning_rush)
        evening_avg = sum(evening_rush) / len(evening_rush)
        off_peak_avg = sum(off_peak) / len(off_peak)
        
        return {
            'passed': morning_avg > off_peak_avg and evening_avg > off_peak_avg,
            'morning_rush_avg': morning_avg,
            'evening_rush_avg': evening_avg,
            'off_peak_avg': off_peak_avg,
            'rush_multiplier': max(morning_avg, evening_avg) / off_peak_avg if off_peak_avg > 0 else 0
        }
    
    def validate_geographic_bounds(self, temporal_data: Dict) -> Dict:
        """Validate all spawns are within Barbados bounds."""
        barbados_bounds = {
            'min_lat': 13.0396, 'max_lat': 13.3356,
            'min_lon': -59.6489, 'max_lon': -59.4206
        }
        
        all_in_bounds = True
        total_spawns = 0
        
        for hour_data in temporal_data.values():
            bounds = hour_data['geographic_bounds']
            total_spawns += hour_data['total_spawns']
            
            if (bounds['min_lat'] < barbados_bounds['min_lat'] or 
                bounds['max_lat'] > barbados_bounds['max_lat'] or
                bounds['min_lon'] < barbados_bounds['min_lon'] or
                bounds['max_lon'] > barbados_bounds['max_lon']):
                all_in_bounds = False
                break
        
        return {
            'passed': all_in_bounds,
            'total_spawns_checked': total_spawns,
            'barbados_bounds': barbados_bounds
        }
    
    def validate_poisson_distribution(self, temporal_data: Dict) -> Dict:
        """Validate that spawning follows Poisson-like statistical properties."""
        hourly_counts = [data['total_spawns'] for data in temporal_data.values()]
        
        if len(hourly_counts) < 2:
            return {'passed': False, 'reason': 'Insufficient data'}
        
        mean_spawns = statistics.mean(hourly_counts)
        variance_spawns = statistics.variance(hourly_counts)
        
        # For Poisson distribution, variance should approximately equal mean
        poisson_ratio = variance_spawns / mean_spawns if mean_spawns > 0 else 0
        
        # Allow 50% variance from perfect Poisson (real-world factor)
        is_poisson_like = 0.5 <= poisson_ratio <= 2.0
        
        return {
            'passed': is_poisson_like,
            'mean_spawns': mean_spawns,
            'variance_spawns': variance_spawns,
            'poisson_ratio': poisson_ratio,
            'expected_range': [0.5, 2.0]
        }
    
    def validate_temporal_consistency(self, temporal_data: Dict) -> Dict:
        """Validate temporal patterns are consistent and realistic."""
        # Check that we have spawns throughout the day
        hours_with_spawns = sum(1 for data in temporal_data.values() if data['total_spawns'] > 0)
        
        # Check for reasonable distribution across location types
        total_depot = sum(data['spawns_by_type']['depot'] for data in temporal_data.values())
        total_route = sum(data['spawns_by_type']['route'] for data in temporal_data.values())
        total_poi = sum(data['spawns_by_type']['poi'] for data in temporal_data.values())
        total_all = total_depot + total_route + total_poi
        
        balanced_distribution = (
            total_all > 0 and
            total_depot / total_all > 0.1 and  # At least 10% depot spawns
            total_route / total_all > 0.1 and  # At least 10% route spawns  
            total_poi / total_all > 0.1        # At least 10% POI spawns
        )
        
        return {
            'passed': hours_with_spawns >= 20 and balanced_distribution,  # At least 20/24 hours active
            'hours_with_spawns': hours_with_spawns,
            'total_hours': 24,
            'balanced_distribution': balanced_distribution,
            'distribution': {
                'depot_pct': total_depot / total_all * 100 if total_all > 0 else 0,
                'route_pct': total_route / total_all * 100 if total_all > 0 else 0,
                'poi_pct': total_poi / total_all * 100 if total_all > 0 else 0
            }
        }
    
    def analyze_spatial_distribution(self, export_data: List[Dict]) -> Dict:
        """Analyze spatial distribution patterns."""
        logger.info("🗺️ Analyzing spatial distribution...")
        
        if not export_data:
            return {'error': 'No spawn data available'}
        
        # Group by location type
        by_type = {'depot': [], 'route': [], 'poi': []}
        for spawn in export_data:
            location_type = self.determine_spawn_type(spawn)
            by_type[location_type].append(spawn)
        
        # Calculate geographic spread
        all_lats = [spawn['location']['lat'] for spawn in export_data]
        all_lons = [spawn['location']['lon'] for spawn in export_data]
        
        return {
            'total_locations': len(export_data),
            'geographic_spread': {
                'lat_range': max(all_lats) - min(all_lats),
                'lon_range': max(all_lons) - min(all_lons),
                'center': {
                    'lat': sum(all_lats) / len(all_lats),
                    'lon': sum(all_lons) / len(all_lons)
                }
            },
            'distribution_by_type': {
                type_name: len(spawns) for type_name, spawns in by_type.items()
            }
        }
    
    def determine_spawn_type(self, spawn: Dict) -> str:
        """Determine spawn type from spawn data."""
        return spawn.get('destination_type', 'poi')
    
    def export_results(self, results: Dict, filename_base: str = 'passenger_spawning_analysis'):
        """Export results in multiple formats for visualization."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export detailed JSON results
        json_filename = f"{filename_base}_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"📄 Exported detailed results to {json_filename}")
        
        # Export CSV for visualization
        csv_filename = f"{filename_base}_{timestamp}.csv"
        with open(csv_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hour', 'passenger_id', 'lat', 'lon', 'destination_type', 'location_name', 'spawn_time'])
            
            for spawn in results['export_data']:
                writer.writerow([
                    spawn['hour'],
                    spawn['passenger_id'],
                    spawn['location']['lat'],
                    spawn['location']['lon'],
                    spawn['destination_type'],
                    spawn['location_name'],
                    spawn['spawn_time']
                ])
        logger.info(f"📊 Exported visualization data to {csv_filename}")
        
        return json_filename, csv_filename
    
    def print_summary_report(self, results: Dict):
        """Print comprehensive summary report."""
        print("\n" + "="*80)
        print("🎯 DEFINITIVE PASSENGER SPAWNING ANALYSIS REPORT")
        print("="*80)
        
        stats = results['statistics']
        validation = results['validation']
        
        print(f"\n📊 SPAWNING STATISTICS:")
        print(f"   • Total Daily Spawns: {stats['total_daily_spawns']:,}")
        print(f"   • Hourly Average: {stats['hourly_statistics']['mean']:.1f}")
        print(f"   • Peak Hour: {stats['peak_hours']['highest_spawn_hour']}:00 "
              f"({max([results['temporal_analysis'][h]['total_spawns'] for h in range(24)])} spawns)")
        print(f"   • Rush Hour Morning: {stats['peak_hours']['rush_hour_morning']['peak_hour']}:00 "
              f"({stats['peak_hours']['rush_hour_morning']['peak_count']} spawns)")
        print(f"   • Rush Hour Evening: {stats['peak_hours']['rush_hour_evening']['peak_hour']}:00 "
              f"({stats['peak_hours']['rush_hour_evening']['peak_count']} spawns)")
        
        print(f"\n🎯 DISTRIBUTION BY LOCATION TYPE:")
        dist = stats['distribution_by_type']
        print(f"   • Depot Spawns: {dist['depot_total']:,} ({dist['depot_percentage']:.1f}%)")
        print(f"   • Route Spawns: {dist['route_total']:,} ({dist['route_percentage']:.1f}%)")
        print(f"   • POI Spawns: {dist['poi_total']:,} ({dist['poi_percentage']:.1f}%)")
        
        print(f"\n✅ VALIDATION RESULTS:")
        overall = validation['overall_score']
        print(f"   • Overall Status: {overall['status']} ({overall['passed_tests']}/{overall['total_tests']} tests)")
        print(f"   • Success Rate: {overall['success_rate']:.1f}%")
        print(f"   • Rush Hour Validation: {'✅ PASSED' if validation['rush_hour_validation']['passed'] else '❌ FAILED'}")
        print(f"   • Geographic Bounds: {'✅ PASSED' if validation['geographic_validation']['passed'] else '❌ FAILED'}")
        print(f"   • Poisson Distribution: {'✅ PASSED' if validation['mathematical_validation']['passed'] else '❌ FAILED'}")
        print(f"   • Temporal Consistency: {'✅ PASSED' if validation['temporal_consistency']['passed'] else '❌ FAILED'}")
        
        print(f"\n🗺️ SPATIAL ANALYSIS:")
        spatial = results['spatial_analysis']
        if 'geographic_spread' in spatial:
            spread = spatial['geographic_spread']
            print(f"   • Total Spawn Locations: {spatial['total_locations']:,}")
            print(f"   • Geographic Center: {spread['center']['lat']:.4f}, {spread['center']['lon']:.4f}")
            print(f"   • Latitude Range: {spread['lat_range']:.4f}°")
            print(f"   • Longitude Range: {spread['lon_range']:.4f}°")
        
        print("\n" + "="*80)
        print("🎉 Analysis Complete! Check visualization at:")
        print("   http://localhost:1337/passenger-spawning-visualization.html")
        print("="*80 + "\n")


async def main():
    """Run the definitive passenger spawning analysis."""
    try:
        analyzer = PassengerSpawningAnalyzer()
        
        # Initialize system
        await analyzer.initialize()
        
        # Run comprehensive analysis
        results = await analyzer.run_comprehensive_analysis()
        
        # Export results
        json_file, csv_file = analyzer.export_results(results)
        
        # Print summary report
        analyzer.print_summary_report(results)
        
        print(f"📁 Files generated:")
        print(f"   • Detailed results: {json_file}")
        print(f"   • Visualization data: {csv_file}")
        print(f"   • Web visualization: passenger-spawning-visualization.html")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())