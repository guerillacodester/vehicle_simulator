"""
Manifest Visualization
----------------------

Reusable visualization logic for passenger manifests:
- Bar chart: Hourly passenger distribution
- Table: Detailed passenger info ordered by distance from depot
- Metrics: Route statistics and averages

Designed for reuse by CLI, API, and UI without duplication.
"""
from __future__ import annotations

import math
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import httpx


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two coordinates"""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


async def fetch_passengers_from_strapi(
    strapi_url: str,
    route_id: Optional[str] = None,
    target_date: Optional[datetime] = None,
    start_hour: int = 0,
    end_hour: int = 23
) -> List[Dict[str, Any]]:
    """Fetch all passengers from Strapi with filtering"""
    
    all_passengers = []
    page = 1
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            url = f"{strapi_url}/api/active-passengers?pagination[page]={page}&pagination[pageSize]=100"
            response = await client.get(url)
            
            if response.status_code != 200:
                break
            
            data = response.json()
            passengers = data.get('data', [])
            
            if not passengers:
                break
            
            all_passengers.extend(passengers)
            
            meta = data.get('meta', {})
            pagination = meta.get('pagination', {})
            total_pages = pagination.get('pageCount', 1)
            
            if page >= total_pages:
                break
            
            page += 1
    
    # Filter by date, time range, and route
    filtered = []
    for p in all_passengers:
        spawn_time_str = p.get('spawned_at')
        if spawn_time_str:
            spawn_time = datetime.fromisoformat(spawn_time_str.replace('Z', '+00:00'))
            
            if target_date and spawn_time.date() != target_date.date():
                continue
            
            if spawn_time.hour < start_hour or spawn_time.hour > end_hour:
                continue
            
            if route_id and p.get('route_id') != route_id:
                continue
                
            filtered.append(p)
    
    return filtered


def generate_barchart_data(passengers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate bar chart data structure from passengers"""
    
    hourly_counts = [0] * 24
    
    for p in passengers:
        spawn_time_str = p.get('spawned_at')
        if spawn_time_str:
            spawn_time = datetime.fromisoformat(spawn_time_str.replace('Z', '+00:00'))
            hour = spawn_time.hour
            hourly_counts[hour] += 1
    
    total = sum(hourly_counts)
    max_count = max(hourly_counts) if hourly_counts else 0
    peak_hour = hourly_counts.index(max_count) if max_count > 0 else 0
    
    depot_count = sum(1 for p in passengers if p.get('depot_id'))
    route_count = total - depot_count
    
    return {
        'hourly_counts': hourly_counts,
        'total': total,
        'max_count': max_count,
        'peak_hour': peak_hour,
        'route_passengers': route_count,
        'depot_passengers': depot_count
    }


def format_barchart_ascii(
    barchart_data: Dict[str, Any],
    target_date: datetime,
    route_name: str = "All Routes"
) -> str:
    """Format bar chart data as ASCII art string"""
    
    lines = []
    hourly_counts = barchart_data['hourly_counts']
    total = barchart_data['total']
    max_count = barchart_data['max_count']
    peak_hour = barchart_data['peak_hour']
    route_count = barchart_data['route_passengers']
    depot_count = barchart_data['depot_passengers']
    
    # Header
    lines.append("=" * 80)
    lines.append(f"PASSENGER MANIFEST - {target_date.strftime('%A, %Y-%m-%d')} - {route_name}")
    lines.append("=" * 80)
    lines.append(f"Total Passengers: {total}")
    lines.append(f"Peak Hour: {peak_hour:02d}:00 ({max_count} passengers)")
    lines.append("=" * 80)
    lines.append("")
    
    # Bar chart
    scale = 60 / max_count if max_count > 0 else 1
    
    for hour in range(24):
        count = hourly_counts[hour]
        bar_length = int(count * scale)
        bar = "█" * bar_length
        
        hour_label = f"{hour:02d}:00"
        count_label = f"{count:>4}"
        
        if count == max_count and count > 0:
            lines.append(f"{hour_label} │ {bar} {count_label} 🔥")
        elif count >= max_count * 0.7 and count > 0:
            lines.append(f"{hour_label} │ {bar} {count_label} ⚡")
        elif count > 0:
            lines.append(f"{hour_label} │ {bar} {count_label}")
        else:
            lines.append(f"{hour_label} │ ")
    
    lines.append("")
    lines.append("=" * 80)
    
    # Breakdown
    if total > 0:
        lines.append(f"Route Passengers: {route_count} ({route_count/total*100:.1f}%)")
        lines.append(f"Depot Passengers: {depot_count} ({depot_count/total*100:.1f}%)")
    else:
        lines.append("Route Passengers: 0")
        lines.append("Depot Passengers: 0")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


async def enrich_passengers_with_geocoding(
    passengers: List[Dict[str, Any]],
    geospatial_url: str
) -> List[Dict[str, Any]]:
    """Enrich passengers with geocoded addresses and calculated distances"""
    
    # Fetch depot coordinates
    depot_cache = {}
    
    async def get_depot_coords(route_id: str) -> Tuple[Optional[float], Optional[float]]:
        if route_id in depot_cache:
            return depot_cache[route_id]
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{geospatial_url}/routes/by-document-id/{route_id}/depot")
                if response.status_code == 200:
                    depot_info = response.json().get('depot', {})
                    coords = (depot_info.get('latitude'), depot_info.get('longitude'))
                    depot_cache[route_id] = coords
                    return coords
        except:
            pass
        return (None, None)
    
    # Fetch all depot coords in parallel
    route_ids = list(set(p.get('route_id') for p in passengers if p.get('route_id')))
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [get_depot_coords(rid) for rid in route_ids]
        await asyncio.gather(*tasks)
    
    # Collect unique coordinates for batch geocoding
    unique_coords = set()
    for p in passengers:
        start_lat = p.get('latitude')
        start_lon = p.get('longitude')
        dest_lat = p.get('destination_lat')
        dest_lon = p.get('destination_lon')
        
        if start_lat and start_lon:
            unique_coords.add((start_lat, start_lon))
        if dest_lat and dest_lon:
            unique_coords.add((dest_lat, dest_lon))
    
    # Reverse geocode all unique coordinates in parallel
    address_cache = {}
    
    async with httpx.AsyncClient(timeout=10.0) as shared_client:
        async def geocode_coord(lat: float, lon: float, semaphore: asyncio.Semaphore) -> Tuple[Tuple[float, float], str]:
            async with semaphore:
                try:
                    response = await shared_client.get(f"{geospatial_url}/geocode/reverse?lat={lat}&lon={lon}")
                    if response.status_code == 200:
                        data = response.json()
                        return ((lat, lon), data.get('address', 'N/A'))
                except:
                    pass
                return ((lat, lon), 'N/A')
        
        semaphore = asyncio.Semaphore(100)
        coords_list = list(unique_coords)
        
        tasks = [geocode_coord(lat, lon, semaphore) for lat, lon in coords_list]
        results = await asyncio.gather(*tasks)
        
        for coords, address in results:
            address_cache[coords] = address
    
    # Enrich passenger data
    enriched = []
    
    for idx, p in enumerate(passengers, 1):
        start_lat = p.get('latitude')
        start_lon = p.get('longitude')
        dest_lat = p.get('destination_lat')
        dest_lon = p.get('destination_lon')
        
        route_id = p.get('route_id')
        depot_lat, depot_lon = depot_cache.get(route_id, (None, None)) if route_id else (None, None)
        
        start_addr = address_cache.get((start_lat, start_lon), 'N/A') if start_lat and start_lon else 'N/A'
        dest_addr = address_cache.get((dest_lat, dest_lon), 'N/A') if dest_lat and dest_lon else 'N/A'
        
        commute_distance = 0.0
        if all([start_lat, start_lon, dest_lat, dest_lon]):
            commute_distance = haversine_distance(start_lat, start_lon, dest_lat, dest_lon)
        
        depot_distance = 0.0
        if all([depot_lat, depot_lon, start_lat, start_lon]):
            depot_distance = haversine_distance(depot_lat, depot_lon, start_lat, start_lon)
        
        enriched.append({
            'index': idx,
            'passenger': p,
            'start_address': start_addr,
            'dest_address': dest_addr,
            'commute_distance': commute_distance,
            'depot_distance': depot_distance
        })
    
    return enriched


def calculate_route_metrics(enriched_passengers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary metrics for the route"""
    
    total = len(enriched_passengers)
    depot_count = sum(1 for item in enriched_passengers if item['passenger'].get('depot_id'))
    route_count = total - depot_count
    
    avg_commute = sum(item['commute_distance'] for item in enriched_passengers) / total if total > 0 else 0
    avg_depot_dist = sum(item['depot_distance'] for item in enriched_passengers) / total if total > 0 else 0
    
    # Calculate total route distance from passenger coordinates
    route_total_distance = None
    if enriched_passengers:
        all_coords = []
        for item in enriched_passengers:
            p = item['passenger']
            lat = p.get('latitude')
            lon = p.get('longitude')
            if lat and lon:
                all_coords.append((lat, lon))
        
        if all_coords and len(all_coords) > 1:
            total_distance = 0.0
            for i in range(len(all_coords) - 1):
                lat1, lon1 = all_coords[i]
                lat2, lon2 = all_coords[i + 1]
                total_distance += haversine_distance(lat1, lon1, lat2, lon2)
            route_total_distance = total_distance
    
    return {
        'total_passengers': total,
        'route_passengers': route_count,
        'depot_passengers': depot_count,
        'avg_commute_distance': avg_commute,
        'avg_depot_distance': avg_depot_dist,
        'total_route_distance': route_total_distance
    }


def format_table_ascii(
    enriched_passengers: List[Dict[str, Any]],
    metrics: Dict[str, Any],
    target_date: datetime,
    route_name: str = "All Routes"
) -> str:
    """Format enriched passengers as ASCII table string"""
    
    # Sort by depot distance
    sorted_passengers = sorted(enriched_passengers, key=lambda x: x['depot_distance'])
    
    lines = []
    
    # Header
    lines.append("=" * 140)
    lines.append(f"PASSENGER MANIFEST TABLE - {target_date.strftime('%A, %Y-%m-%d')} - {route_name}")
    lines.append("=" * 140)
    lines.append(f"Total Passengers: {metrics['total_passengers']}")
    lines.append("=" * 140)
    lines.append("")
    
    # Table header
    lines.append(f"{'#':>4} | {'Spawn Time':^19} | {'Start Location':^30} | {'Dest Location':^30} | {'Commute':>8} | {'From Depot':>11}")
    lines.append("-" * 140)
    
    # Table rows
    for item in sorted_passengers:
        idx = item['index']
        p = item['passenger']
        commute_dist = item['commute_distance']
        depot_dist = item['depot_distance']
        start_addr = item['start_address']
        dest_addr = item['dest_address']
        
        spawn_time_str = p.get('spawned_at', '')
        if spawn_time_str:
            spawn_time = datetime.fromisoformat(spawn_time_str.replace('Z', '+00:00'))
            spawn_display = spawn_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            spawn_display = 'N/A'
        
        start_addr_short = start_addr[:28]
        dest_addr_short = dest_addr[:28]
        
        lines.append(f"{idx:>4} | {spawn_display:^19} | {start_addr_short:<30} | {dest_addr_short:<30} | {commute_dist:>6.2f}km | {depot_dist:>9.2f}km")
    
    lines.append("")
    lines.append("=" * 140)
    
    # Summary
    lines.append(f"Route Passengers: {metrics['route_passengers']} | Depot Passengers: {metrics['depot_passengers']}")
    lines.append(f"Average Commute Distance: {metrics['avg_commute_distance']:.2f}km")
    lines.append(f"Average Distance from Depot: {metrics['avg_depot_distance']:.2f}km")
    
    if metrics['total_route_distance'] is not None:
        lines.append(f"Total Route Distance: {metrics['total_route_distance']:.2f}km")
    
    lines.append("=" * 140)
    
    return "\n".join(lines)
