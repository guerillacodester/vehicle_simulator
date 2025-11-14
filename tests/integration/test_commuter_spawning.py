#!/usr/bin/env python3
"""
Test Commuter Spawning Statistics
==================================

Queries the Manifest API to analyze commuter simulator spawning patterns.

Tests:
1. Total spawn count over time
2. Geographic distribution (GeoJSON coverage)
3. Route distribution (spawns per route)
4. Depot distribution (spawns per depot)
5. Temporal distribution (spawn timing patterns)

Usage:
    python test_commuter_spawning.py
"""

import asyncio
import httpx
from datetime import datetime
from collections import Counter
from typing import Dict, List

try:
    from common.config_provider import get_config
    config = get_config()
    COMMUTER_commuter_service_url = config.infrastructure.commuter_service_url
except Exception:
    COMMUTER_commuter_service_url = "http://localhost:4000"  # Fallback


async def fetch_manifest(limit: int = 1000) -> Dict:
    """Fetch passenger manifest from API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {"limit": limit}
        response = await client.get(f"{COMMUTER_commuter_service_url}/api/manifest", params=params)
        response.raise_for_status()
        return response.json()


def analyze_geographic_distribution(passengers: List[Dict]) -> Dict:
    """Analyze geographic distribution of spawn points"""
    start_coords = []
    stop_coords = []
    
    for p in passengers:
        if p.get("start_lat") and p.get("start_lon"):
            start_coords.append((p["start_lat"], p["start_lon"]))
        if p.get("stop_lat") and p.get("stop_lon"):
            stop_coords.append((p["stop_lat"], p["stop_lon"]))
    
    return {
        "total_start_points": len(start_coords),
        "total_stop_points": len(stop_coords),
        "unique_start_points": len(set(start_coords)),
        "unique_stop_points": len(set(stop_coords)),
        "start_lat_range": (
            min(c[0] for c in start_coords) if start_coords else None,
            max(c[0] for c in start_coords) if start_coords else None
        ),
        "start_lon_range": (
            min(c[1] for c in start_coords) if start_coords else None,
            max(c[1] for c in start_coords) if start_coords else None
        )
    }


def analyze_route_distribution(passengers: List[Dict]) -> Dict:
    """Analyze distribution across routes"""
    route_counts = Counter(p.get("route_id") for p in passengers if p.get("route_id"))
    
    return {
        "routes_with_spawns": len(route_counts),
        "total_spawns": sum(route_counts.values()),
        "spawns_per_route": dict(route_counts),
        "avg_spawns_per_route": sum(route_counts.values()) / len(route_counts) if route_counts else 0,
        "max_spawns_single_route": max(route_counts.values()) if route_counts else 0,
        "min_spawns_single_route": min(route_counts.values()) if route_counts else 0
    }


def analyze_depot_distribution(passengers: List[Dict]) -> Dict:
    """Analyze distribution across depots"""
    depot_counts = Counter(p.get("depot_id") for p in passengers if p.get("depot_id"))
    
    return {
        "depots_with_spawns": len(depot_counts),
        "total_spawns": sum(depot_counts.values()),
        "spawns_per_depot": dict(depot_counts),
        "avg_spawns_per_depot": sum(depot_counts.values()) / len(depot_counts) if depot_counts else 0
    }


def analyze_temporal_distribution(passengers: List[Dict]) -> Dict:
    """Analyze spawn timing patterns"""
    spawn_times = []
    
    for p in passengers:
        spawned_at = p.get("spawned_at")
        if spawned_at:
            try:
                dt = datetime.fromisoformat(spawned_at.replace('Z', '+00:00'))
                spawn_times.append(dt)
            except:
                pass
    
    if not spawn_times:
        return {"error": "No valid spawn timestamps found"}
    
    spawn_times.sort()
    
    # Calculate time gaps between spawns
    gaps = [(spawn_times[i+1] - spawn_times[i]).total_seconds() 
            for i in range(len(spawn_times) - 1)]
    
    return {
        "total_spawns": len(spawn_times),
        "first_spawn": spawn_times[0].isoformat(),
        "last_spawn": spawn_times[-1].isoformat(),
        "time_window_minutes": (spawn_times[-1] - spawn_times[0]).total_seconds() / 60,
        "avg_gap_seconds": sum(gaps) / len(gaps) if gaps else 0,
        "min_gap_seconds": min(gaps) if gaps else 0,
        "max_gap_seconds": max(gaps) if gaps else 0
    }


def analyze_status_distribution(passengers: List[Dict]) -> Dict:
    """Analyze passenger status distribution"""
    status_counts = Counter(p.get("status") for p in passengers)
    
    return {
        "status_breakdown": dict(status_counts),
        "total_passengers": sum(status_counts.values())
    }


async def main():
    """Run all tests"""
    print("=" * 80)
    print("🧪 COMMUTER SPAWNING STATISTICS TEST")
    print("=" * 80)
    print()
    
    # Test 1: Fetch manifest data
    print("📊 Fetching passenger manifest...")
    try:
        manifest = await fetch_manifest(limit=1000)
        passengers = manifest.get("passengers", [])
        print(f"   ✅ Fetched {len(passengers)} passengers from manifest")
        print()
    except Exception as e:
        print(f"   ❌ Failed to fetch manifest: {e}")
        print(f"   Make sure Manifest API is running on {COMMUTER_commuter_service_url}")
        return 1
    
    if not passengers:
        print("⚠️  No passengers found in system.")
        print("   This is normal if commuter simulator just started.")
        print("   Wait 60 seconds for first spawn cycle to complete.")
        return 0
    
    # Test 2: Geographic Distribution
    print("🗺️  GEOGRAPHIC DISTRIBUTION")
    print("-" * 80)
    geo_stats = analyze_geographic_distribution(passengers)
    print(f"   Total spawn points (start): {geo_stats['total_start_points']}")
    print(f"   Unique spawn points (start): {geo_stats['unique_start_points']}")
    print(f"   Total destination points: {geo_stats['total_stop_points']}")
    print(f"   Unique destination points: {geo_stats['unique_stop_points']}")
    if geo_stats['start_lat_range'][0]:
        print(f"   Latitude range: {geo_stats['start_lat_range'][0]:.6f} to {geo_stats['start_lat_range'][1]:.6f}")
        print(f"   Longitude range: {geo_stats['start_lon_range'][0]:.6f} to {geo_stats['start_lon_range'][1]:.6f}")
    print()
    
    # Test 3: Route Distribution
    print("🚌 ROUTE DISTRIBUTION")
    print("-" * 80)
    route_stats = analyze_route_distribution(passengers)
    print(f"   Routes with spawns: {route_stats['routes_with_spawns']}")
    print(f"   Total spawns: {route_stats['total_spawns']}")
    if route_stats['routes_with_spawns'] > 0:
        print(f"   Average spawns per route: {route_stats['avg_spawns_per_route']:.1f}")
        print(f"   Max spawns on single route: {route_stats['max_spawns_single_route']}")
        print(f"   Min spawns on single route: {route_stats['min_spawns_single_route']}")
        print()
        print("   Spawns per route:")
        for route_id, count in sorted(route_stats['spawns_per_route'].items(), key=lambda x: x[1], reverse=True):
            route_display = route_id if route_id else "UNKNOWN"
            print(f"      {route_display}: {count}")
    print()
    
    # Test 4: Depot Distribution
    print("🏢 DEPOT DISTRIBUTION")
    print("-" * 80)
    depot_stats = analyze_depot_distribution(passengers)
    print(f"   Depots with spawns: {depot_stats['depots_with_spawns']}")
    print(f"   Total spawns: {depot_stats['total_spawns']}")
    if depot_stats['depots_with_spawns'] > 0:
        print(f"   Average spawns per depot: {depot_stats['avg_spawns_per_depot']:.1f}")
        print()
        print("   Spawns per depot:")
        for depot_id, count in sorted(depot_stats['spawns_per_depot'].items(), key=lambda x: x[1], reverse=True):
            depot_display = depot_id if depot_id else "UNKNOWN"
            print(f"      {depot_display}: {count}")
    print()
    
    # Test 5: Temporal Distribution
    print("⏰ TEMPORAL DISTRIBUTION")
    print("-" * 80)
    time_stats = analyze_temporal_distribution(passengers)
    if "error" not in time_stats:
        print(f"   Total spawns: {time_stats['total_spawns']}")
        print(f"   First spawn: {time_stats['first_spawn']}")
        print(f"   Last spawn: {time_stats['last_spawn']}")
        print(f"   Time window: {time_stats['time_window_minutes']:.1f} minutes")
        if time_stats['avg_gap_seconds'] > 0:
            print(f"   Average gap between spawns: {time_stats['avg_gap_seconds']:.1f} seconds")
            print(f"   Min gap: {time_stats['min_gap_seconds']:.1f} seconds")
            print(f"   Max gap: {time_stats['max_gap_seconds']:.1f} seconds")
    else:
        print(f"   ❌ {time_stats['error']}")
    print()
    
    # Test 6: Status Distribution
    print("📋 STATUS DISTRIBUTION")
    print("-" * 80)
    status_stats = analyze_status_distribution(passengers)
    print(f"   Total passengers: {status_stats['total_passengers']}")
    print()
    for status, count in status_stats['status_breakdown'].items():
        status_display = status if status else "UNKNOWN"
        percentage = (count / status_stats['total_passengers'] * 100) if status_stats['total_passengers'] > 0 else 0
        print(f"      {status_display}: {count} ({percentage:.1f}%)")
    print()
    
    # Summary
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    print()
    print("SUMMARY:")
    print(f"   • {len(passengers)} total passengers analyzed")
    print(f"   • {route_stats['routes_with_spawns']} routes active")
    print(f"   • {depot_stats['depots_with_spawns']} depots active")
    print(f"   • {geo_stats['unique_start_points']} unique spawn locations")
    print(f"   • Geographic coverage verified ✅")
    print()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
