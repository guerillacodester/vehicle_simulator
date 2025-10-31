"""
Spawn Analysis API
Provides comprehensive endpoints for passenger spawn rate calculations.
Single source of truth for depot-route relationships and building density analysis.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import httpx
import sys
import os
import configparser
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.postgis_client import postgis_client

router = APIRouter(prefix="/spawn", tags=["Spawn Analysis"])

# Load Strapi URL from config.ini
config = configparser.ConfigParser()
config_path = Path(__file__).parent.parent.parent / "config.ini"
config.read(config_path, encoding='utf-8')
STRAPI_URL = config.get('infrastructure', 'strapi_url', fallback='http://localhost:1337')


@router.get("/depot-analysis/{depot_id}", summary="Complete depot spawn analysis")
async def get_depot_analysis(
    depot_id: int,
    depot_radius: int = Query(800, description="Radius around depot in meters"),
    route_buffer: int = Query(100, description="Buffer around route geometry in meters"),
    passengers_per_building: float = Query(0.05, description="Passengers per building per hour"),
) -> Dict[str, Any]:
    """
    Get comprehensive spawn analysis for a depot.
    
    Returns:
    - Buildings near depot (terminal population)
    - All routes servicing this depot
    - Buildings along each route (route attractiveness)
    - Calculated spawn rates per route
    - Total spawn rate for depot
    """
    
    # Get depot info from Strapi
    async with httpx.AsyncClient() as client:
        depot_response = await client.get(f"{STRAPI_URL}/api/depots/{depot_id}")
        if depot_response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Depot {depot_id} not found")
        
        depot_data = depot_response.json()
        depot_attrs = depot_data['data']['attributes']
        depot_location = depot_attrs.get('location')
        
        if not depot_location:
            raise HTTPException(status_code=400, detail="Depot has no location")
        
        depot_lat = depot_location['coordinates'][1]
        depot_lon = depot_location['coordinates'][0]
        depot_name = depot_attrs.get('name', 'Unknown')
    
    # Query buildings near depot
    depot_buildings_list = await postgis_client.get_buildings_near_depot(
        latitude=depot_lat,
        longitude=depot_lon,
        radius_meters=depot_radius,
        limit=5000
    )
    depot_building_count = len(depot_buildings_list)
    terminal_population = depot_building_count * passengers_per_building
    
    # Get routes for this depot
    async with httpx.AsyncClient() as client:
        # Try different relation names (depot, depots, start_depot, end_depot)
        routes_response = await client.get(
            f"{STRAPI_URL}/api/routes",
            params={
                "filters[depot][id][$eq]": depot_id,
                "populate": "*",
                "pagination[pageSize]": 100
            }
        )
        
        routes_data = routes_response.json()
        routes = routes_data.get('data', []) or []
        
        # If no routes found with 'depot', try 'depots'
        if len(routes) == 0:
            routes_response = await client.get(
                f"{STRAPI_URL}/api/routes",
                params={
                    "filters[depots][id][$eq]": depot_id,
                    "populate": "*",
                    "pagination[pageSize]": 100
                }
            )
            routes_data = routes_response.json()
            routes = routes_data.get('data', []) or []
    
    # Analyze each route
    route_analyses = []
    total_route_buildings = 0
    
    for route in routes:
        route_attrs = route['attributes']
        route_id = route['id']
        route_name = route_attrs.get('route_long_name', 'Unknown')
        route_short = route_attrs.get('route_short_name', f'Route {route_id}')
        
        # Get route geometry
        route_geom = route_attrs.get('route_geometry')
        
        if not route_geom or not route_geom.get('coordinates'):
            route_analyses.append({
                'route_id': route_id,
                'route_name': route_name,
                'route_short_name': route_short,
                'building_count': 0,
                'error': 'No geometry data'
            })
            continue
        
        # Query buildings along route using coordinates
        # We'll use the existing spatial endpoint internally
        route_coords = route_geom['coordinates']
        
        # Build LineString and query buildings
        # For now, use document_id if available, otherwise skip
        route_doc_id = route_attrs.get('documentId') or route_attrs.get('document_id')
        
        if not route_doc_id:
            route_analyses.append({
                'route_id': route_id,
                'route_name': route_name,
                'route_short_name': route_short,
                'building_count': 0,
                'error': 'No document_id for building query'
            })
            continue
        
        # Query buildings using the highway document_id
        try:
            route_buildings_list = await postgis_client.get_buildings_near_route(
                route_id=route_doc_id,
                buffer_meters=route_buffer,
                limit=5000
            )
            route_building_count = len(route_buildings_list)
        except Exception as e:
            route_building_count = 0
            route_analyses.append({
                'route_id': route_id,
                'route_name': route_name,
                'route_short_name': route_short,
                'building_count': 0,
                'error': f'Query failed: {str(e)}'
            })
            continue
        
        total_route_buildings += route_building_count
        
        route_analyses.append({
            'route_id': route_id,
            'route_name': route_name,
            'route_short_name': route_short,
            'building_count': route_building_count,
            'geometry_points': len(route_coords)
        })
    
    # Calculate spawn distribution
    spawn_distribution = []
    total_spawn_rate = 0
    
    if total_route_buildings > 0:
        for route_info in route_analyses:
            if 'error' in route_info:
                spawn_distribution.append({
                    **route_info,
                    'attractiveness': 0,
                    'spawn_rate_per_hour': 0
                })
                continue
            
            attractiveness = route_info['building_count'] / total_route_buildings
            spawn_rate = terminal_population * attractiveness
            total_spawn_rate += spawn_rate
            
            spawn_distribution.append({
                **route_info,
                'attractiveness': attractiveness,
                'spawn_rate_per_hour': spawn_rate,
                'spawn_rate_per_minute': spawn_rate / 60,
                'spawn_rate_per_5min': spawn_rate / 12
            })
    elif len(route_analyses) > 0:
        # Equal distribution if no building data
        equal_rate = terminal_population / len(route_analyses)
        for route_info in route_analyses:
            spawn_distribution.append({
                **route_info,
                'attractiveness': 1 / len(route_analyses),
                'spawn_rate_per_hour': equal_rate,
                'spawn_rate_per_minute': equal_rate / 60,
                'spawn_rate_per_5min': equal_rate / 12
            })
            total_spawn_rate += equal_rate
    
    return {
        'depot': {
            'id': depot_id,
            'name': depot_name,
            'location': {
                'lat': depot_lat,
                'lon': depot_lon
            },
            'building_count': depot_building_count,
            'terminal_population_per_hour': terminal_population
        },
        'routes': {
            'count': len(routes),
            'total_buildings': total_route_buildings,
            'analyses': spawn_distribution
        },
        'spawn_summary': {
            'total_spawn_rate_per_hour': total_spawn_rate,
            'total_spawn_rate_per_minute': total_spawn_rate / 60,
            'total_spawn_rate_per_5min': total_spawn_rate / 12
        },
        'parameters': {
            'depot_radius_meters': depot_radius,
            'route_buffer_meters': route_buffer,
            'passengers_per_building_per_hour': passengers_per_building
        }
    }


@router.get("/all-depots", summary="Spawn analysis for all depots")
async def get_all_depots_analysis(
    depot_radius: int = Query(800, description="Radius around depot in meters"),
    route_buffer: int = Query(100, description="Buffer around route geometry in meters"),
    passengers_per_building: float = Query(0.05, description="Passengers per building per hour"),
) -> Dict[str, Any]:
    """
    Get spawn analysis for ALL depots in the system.
    Returns comprehensive analysis for each depot.
    """
    
    # Get all depots
    async with httpx.AsyncClient() as client:
        depots_response = await client.get(
            f"{STRAPI_URL}/api/depots",
            params={"pagination[pageSize]": 100}
        )
        depots_data = depots_response.json()
        depots = depots_data.get('data', []) or []
    
    # Analyze each depot
    depot_analyses = []
    system_total_spawn = 0
    
    for depot in depots:
        depot_id = depot['id']
        
        try:
            analysis = await get_depot_analysis(
                depot_id=depot_id,
                depot_radius=depot_radius,
                route_buffer=route_buffer,
                passengers_per_building=passengers_per_building
            )
            depot_analyses.append(analysis)
            system_total_spawn += analysis['spawn_summary']['total_spawn_rate_per_hour']
        except Exception as e:
            depot_analyses.append({
                'depot': {
                    'id': depot_id,
                    'name': depot['attributes'].get('name', 'Unknown'),
                    'error': str(e)
                }
            })
    
    return {
        'depots': depot_analyses,
        'system_summary': {
            'total_depots': len(depots),
            'total_spawn_rate_per_hour': system_total_spawn,
            'total_spawn_rate_per_minute': system_total_spawn / 60,
            'average_per_depot': system_total_spawn / len(depots) if len(depots) > 0 else 0
        },
        'parameters': {
            'depot_radius_meters': depot_radius,
            'route_buffer_meters': route_buffer,
            'passengers_per_building_per_hour': passengers_per_building
        }
    }


@router.get("/route-analysis/{route_id}", summary="Complete route spawn analysis")
async def get_route_analysis(
    route_id: int,
    route_buffer: int = Query(100, description="Buffer around route geometry in meters"),
    passengers_per_building: float = Query(0.05, description="Passengers per building per hour"),
) -> Dict[str, Any]:
    """
    Get comprehensive spawn analysis for a specific route.
    
    Returns:
    - Route details
    - Buildings along route
    - Associated depots
    - Calculated spawn rate (route-based only, not depot-based)
    """
    
    # Get route from Strapi
    async with httpx.AsyncClient() as client:
        route_response = await client.get(f"{STRAPI_URL}/api/routes/{route_id}?populate=*")
        if route_response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
        
        route_data = route_response.json()
        route_attrs = route_data['data']['attributes']
        route_name = route_attrs.get('route_long_name', 'Unknown')
        route_short = route_attrs.get('route_short_name', f'Route {route_id}')
    
    # Get route geometry
    route_geom = route_attrs.get('route_geometry')
    
    if not route_geom or not route_geom.get('coordinates'):
        raise HTTPException(status_code=400, detail="Route has no geometry data")
    
    route_coords = route_geom['coordinates']
    
    # Query buildings along route using document_id
    route_doc_id = route_attrs.get('documentId') or route_attrs.get('document_id')
    
    if not route_doc_id:
        raise HTTPException(status_code=400, detail="Route has no document_id for building query")
    
    try:
        route_buildings_list = await postgis_client.get_buildings_near_route(
            route_id=route_doc_id,
            buffer_meters=route_buffer,
            limit=5000
        )
        building_count = len(route_buildings_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Building query failed: {str(e)}")
    
    spawn_rate = building_count * passengers_per_building
    
    # Get associated depots
    depot_info = route_attrs.get('depot') or route_attrs.get('depots')
    
    return {
        'route': {
            'id': route_id,
            'name': route_name,
            'short_name': route_short,
            'building_count': building_count,
            'geometry_points': len(route_coords)
        },
        'spawn_rate': {
            'per_hour': spawn_rate,
            'per_minute': spawn_rate / 60,
            'per_5min': spawn_rate / 12
        },
        'depots': depot_info,
        'parameters': {
            'route_buffer_meters': route_buffer,
            'passengers_per_building_per_hour': passengers_per_building
        }
    }


@router.get("/all-routes", summary="Spawn analysis for all routes")
async def get_all_routes_analysis(
    route_buffer: int = Query(100, description="Buffer around route geometry in meters"),
    passengers_per_building: float = Query(0.05, description="Passengers per building per hour"),
) -> Dict[str, Any]:
    """
    Get spawn analysis for ALL routes in the system.
    Returns comprehensive analysis for each route.
    """
    
    # Get all routes
    async with httpx.AsyncClient() as client:
        routes_response = await client.get(
            f"{STRAPI_URL}/api/routes",
            params={"populate": "*", "pagination[pageSize]": 100}
        )
        routes_data = routes_response.json()
        routes = routes_data.get('data', []) or []
    
    # Analyze each route
    route_analyses = []
    system_total_spawn = 0
    
    for route in routes:
        route_id = route['id']
        
        try:
            analysis = await get_route_analysis(
                route_id=route_id,
                route_buffer=route_buffer,
                passengers_per_building=passengers_per_building
            )
            route_analyses.append(analysis)
            system_total_spawn += analysis['spawn_rate']['per_hour']
        except Exception as e:
            route_analyses.append({
                'route': {
                    'id': route_id,
                    'name': route['attributes'].get('route_long_name', 'Unknown'),
                    'error': str(e)
                }
            })
    
    return {
        'routes': route_analyses,
        'system_summary': {
            'total_routes': len(routes),
            'total_spawn_rate_per_hour': system_total_spawn,
            'total_spawn_rate_per_minute': system_total_spawn / 60,
            'average_per_route': system_total_spawn / len(routes) if len(routes) > 0 else 0
        },
        'parameters': {
            'route_buffer_meters': route_buffer,
            'passengers_per_building_per_hour': passengers_per_building
        }
    }


@router.get("/system-overview", summary="Complete system spawn overview")
async def get_system_overview(
    depot_radius: int = Query(800, description="Radius around depot in meters"),
    route_buffer: int = Query(100, description="Buffer around route geometry in meters"),
    passengers_per_building: float = Query(0.05, description="Passengers per building per hour"),
) -> Dict[str, Any]:
    """
    Get complete overview of entire spawn system.
    
    Returns:
    - All depot analyses
    - All route analyses
    - System-wide totals
    - Recommendations
    """
    
    # Get both analyses
    depots_analysis = await get_all_depots_analysis(
        depot_radius=depot_radius,
        route_buffer=route_buffer,
        passengers_per_building=passengers_per_building
    )
    
    routes_analysis = await get_all_routes_analysis(
        route_buffer=route_buffer,
        passengers_per_building=passengers_per_building
    )
    
    # Calculate combined totals
    depot_spawn_total = depots_analysis['system_summary']['total_spawn_rate_per_hour']
    route_spawn_total = routes_analysis['system_summary']['total_spawn_rate_per_hour']
    system_total = depot_spawn_total + route_spawn_total
    
    return {
        'depot_spawning': depots_analysis,
        'route_spawning': routes_analysis,
        'combined_system': {
            'total_spawn_rate_per_hour': system_total,
            'total_spawn_rate_per_minute': system_total / 60,
            'depot_contribution': depot_spawn_total,
            'route_contribution': route_spawn_total,
            'depot_percentage': (depot_spawn_total / system_total * 100) if system_total > 0 else 0,
            'route_percentage': (route_spawn_total / system_total * 100) if system_total > 0 else 0
        },
        'parameters': {
            'depot_radius_meters': depot_radius,
            'route_buffer_meters': route_buffer,
            'passengers_per_building_per_hour': passengers_per_building
        }
    }


@router.get("/compare-scaling", summary="Compare different scaling factors")
async def compare_scaling_factors(
    depot_radius: int = Query(800, description="Radius around depot in meters"),
    route_buffer: int = Query(100, description="Buffer around route geometry in meters"),
) -> Dict[str, Any]:
    """
    Compare system spawn rates at different scaling factors.
    Helps determine realistic passengers_per_building values.
    """
    
    scaling_factors = [0.01, 0.05, 0.1, 0.2, 0.3]
    comparisons = []
    
    for factor in scaling_factors:
        overview = await get_system_overview(
            depot_radius=depot_radius,
            route_buffer=route_buffer,
            passengers_per_building=factor
        )
        
        comparisons.append({
            'passengers_per_building': factor,
            'total_spawn_per_hour': overview['combined_system']['total_spawn_rate_per_hour'],
            'total_spawn_per_minute': overview['combined_system']['total_spawn_rate_per_minute'],
            'depot_spawn_per_hour': overview['combined_system']['depot_contribution'],
            'route_spawn_per_hour': overview['combined_system']['route_contribution']
        })
    
    return {
        'comparisons': comparisons,
        'recommendation': {
            'for_barbados': 'Use 0.05 for realistic simulation (~750 pass/hr system-wide)',
            'for_busy_system': 'Use 0.1-0.2 for higher activity',
            'for_testing': 'Use 0.01 for minimal spawning'
        }
    }


# Global configuration storage (in-memory, should be replaced with database/config file)
_spawn_config = {
    'passengers_per_building_per_hour': 0.05,
    'depot_radius_meters': 800,
    'route_buffer_meters': 100,
    'spawn_cycle_minutes': 5,
    'time_multipliers': {
        'peak_morning': {'hours': '07:00-09:00', 'multiplier': 1.5},
        'peak_evening': {'hours': '16:00-18:00', 'multiplier': 1.5},
        'normal': {'hours': '09:00-16:00,18:00-20:00', 'multiplier': 1.0},
        'off_peak': {'hours': '06:00-07:00,20:00-22:00', 'multiplier': 0.3},
        'night': {'hours': '22:00-06:00', 'multiplier': 0.1}
    },
    'day_multipliers': {
        'weekday': 1.0,
        'saturday': 0.7,
        'sunday': 0.4
    }
}


@router.get("/config", summary="Get current spawn configuration")
async def get_spawn_config() -> Dict[str, Any]:
    """
    Get the current spawn configuration.
    
    Returns all spawn-related parameters and multipliers.
    """
    return {
        'config': _spawn_config,
        'description': {
            'passengers_per_building_per_hour': 'Base rate of passenger generation per building',
            'depot_radius_meters': 'Radius around depot for catchment area',
            'route_buffer_meters': 'Buffer around route for building queries',
            'spawn_cycle_minutes': 'How often spawn calculations occur',
            'time_multipliers': 'Multipliers based on time of day',
            'day_multipliers': 'Multipliers based on day of week'
        }
    }


@router.post("/config", summary="Update spawn configuration")
async def update_spawn_config(
    passengers_per_building_per_hour: Optional[float] = Query(None, ge=0.001, le=1.0),
    depot_radius_meters: Optional[int] = Query(None, ge=100, le=5000),
    route_buffer_meters: Optional[int] = Query(None, ge=10, le=1000),
    spawn_cycle_minutes: Optional[int] = Query(None, ge=1, le=60)
) -> Dict[str, Any]:
    """
    Update spawn configuration parameters.
    
    Only updates provided parameters, leaves others unchanged.
    """
    global _spawn_config
    
    updated_fields = []
    
    if passengers_per_building_per_hour is not None:
        _spawn_config['passengers_per_building_per_hour'] = passengers_per_building_per_hour
        updated_fields.append('passengers_per_building_per_hour')
    
    if depot_radius_meters is not None:
        _spawn_config['depot_radius_meters'] = depot_radius_meters
        updated_fields.append('depot_radius_meters')
    
    if route_buffer_meters is not None:
        _spawn_config['route_buffer_meters'] = route_buffer_meters
        updated_fields.append('route_buffer_meters')
    
    if spawn_cycle_minutes is not None:
        _spawn_config['spawn_cycle_minutes'] = spawn_cycle_minutes
        updated_fields.append('spawn_cycle_minutes')
    
    return {
        'success': True,
        'updated_fields': updated_fields,
        'current_config': _spawn_config
    }


@router.get("/time-multipliers", summary="Get time-of-day multipliers")
async def get_time_multipliers() -> Dict[str, Any]:
    """
    Get time-of-day spawn rate multipliers.
    
    Shows how spawn rates vary throughout the day.
    """
    return {
        'time_multipliers': _spawn_config['time_multipliers'],
        'day_multipliers': _spawn_config['day_multipliers'],
        'description': 'Multipliers are applied to base spawn rate',
        'example': 'Base rate 100 pass/hr × peak_morning (1.5) = 150 pass/hr'
    }


@router.post("/time-multipliers", summary="Update time-of-day multipliers")
async def update_time_multipliers(
    period: str = Query(..., description="Time period (peak_morning, peak_evening, normal, off_peak, night)"),
    multiplier: float = Query(..., ge=0.0, le=5.0, description="Multiplier value")
) -> Dict[str, Any]:
    """
    Update a specific time-of-day multiplier.
    
    Allows fine-tuning of spawn rates for different times.
    """
    global _spawn_config
    
    if period not in _spawn_config['time_multipliers']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Must be one of: {list(_spawn_config['time_multipliers'].keys())}"
        )
    
    _spawn_config['time_multipliers'][period]['multiplier'] = multiplier
    
    return {
        'success': True,
        'updated_period': period,
        'new_multiplier': multiplier,
        'current_config': _spawn_config['time_multipliers']
    }
