"""
Console - Historic Passenger Viewer
-----------------------------------

Query Strapi active-passengers with optional filters and print a concise table.

Env:
- STRAPI_URL (default: http://localhost:1337)
- STRAPI_TOKEN (optional)

Usage examples:
    python -m commuter_simulator.interfaces.cli.list_passengers --route gg3pv3z19hhm117v9xth5ezq --start 2025-10-29T09:00:00Z --end 2025-10-29T10:00:00Z
    python -m commuter_simulator.interfaces.cli.list_passengers --depot abcd1234 --limit 50
    python -m commuter_simulator.interfaces.cli.list_passengers --limit 10 --sort createdAt:desc
    python -m commuter_simulator.interfaces.cli.list_passengers --route gg3pv3z19hhm117v9xth5ezq --json
"""

from __future__ import annotations

import os
import sys
import asyncio
from typing import Optional, Dict, Any, List, Tuple
import json
from datetime import datetime
import argparse
import math

import httpx

# Reusable manifest enrichment
from commuter_simulator.application.queries import enrich_manifest_rows


def build_params(route: Optional[str], depot: Optional[str], start: Optional[str], end: Optional[str], limit: int, sort: str, status: Optional[str]) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "pagination[pageSize]": limit,
        "sort": sort,
    }
    if route:
        params["filters[route_id][$eq]"] = route
    if depot:
        params["filters[depot_id][$eq]"] = depot
    if start:
        params["filters[spawned_at][$gte]"] = start
    if end:
        params["filters[spawned_at][$lte]"] = end
    if status:
        params["filters[status][$eq]"] = status
    return params


def parse_attrs(item: Dict[str, Any]) -> Dict[str, Any]:
    attrs = item.get("attributes", {})
    if attrs:
        return {
            "id": item.get("id"),
            **attrs,
        }
    # Fallback flat
    return item


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def calculate_route_position(passenger_lat: float, passenger_lon: float, route_coords: List[List[float]]) -> tuple[float, int]:
    """
    Calculate distance along route from start to nearest point to passenger.
    Returns (distance_from_start_m, nearest_segment_index)
    """
    cumulative_distances = [0.0]
    for i in range(1, len(route_coords)):
        lat1, lon1 = route_coords[i-1]
        lat2, lon2 = route_coords[i]
        segment_dist = haversine_distance(lat1, lon1, lat2, lon2)
        cumulative_distances.append(cumulative_distances[-1] + segment_dist)
    
    # Find nearest point on route
    min_dist = float('inf')
    nearest_idx = 0
    for i, (lat, lon) in enumerate(route_coords):
        dist = haversine_distance(passenger_lat, passenger_lon, lat, lon)
        if dist < min_dist:
            min_dist = dist
            nearest_idx = i
    
    return cumulative_distances[nearest_idx], nearest_idx


async def reverse_geocode_address(client: httpx.AsyncClient, geo_url: str, lat: Optional[float], lon: Optional[float], cache: Dict[Tuple[float, float], str]) -> str:
    """Reverse geocode lat/lon to a readable address using GeospatialService with simple caching."""
    if lat is None or lon is None:
        return "-"
    key = (round(float(lat), 5), round(float(lon), 5))
    if key in cache:
        return cache[key]
    try:
        resp = await client.get(f"{geo_url}/geocode/reverse", params={"lat": key[0], "lon": key[1]})
        if resp.status_code == 200:
            data = resp.json()
            addr = data.get("address") or f"Lat {key[0]:.5f}, Lon {key[1]:.5f}"
            cache[key] = addr
            return addr
        else:
            return "-"
    except Exception:
        return "-"


async def main_async():
    parser = argparse.ArgumentParser(description="List passengers from Strapi active-passengers")
    parser.add_argument("--route", help="Filter by route_id", default=None)
    parser.add_argument("--depot", help="Filter by depot_id", default=None)
    parser.add_argument("--start", help="Filter spawned_at >= ISO8601", default=None)
    parser.add_argument("--end", help="Filter spawned_at <= ISO8601", default=None)
    parser.add_argument("--limit", type=int, default=100, help="Max rows (default 100)")
    parser.add_argument("--sort", default="spawned_at:asc", help="Sort (default spawned_at:asc)")
    parser.add_argument("--status", default=None, help="Filter status (e.g., WAITING, BOARDED)")
    parser.add_argument("--json", action="store_true", help="Output NDJSON for piping")
    args = parser.parse_args()

    base_url = os.getenv("STRAPI_URL", "http://localhost:1337").rstrip("/")
    token = os.getenv("STRAPI_TOKEN")

    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = build_params(args.route, args.depot, args.start, args.end, args.limit, args.sort, args.status)

    async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
        r = await client.get(f"{base_url}/api/active-passengers", params=params)
        r.raise_for_status()
        data = r.json()
        items = data.get("data", [])

    rows = [parse_attrs(it) for it in items]
    enriched = await enrich_manifest_rows(rows, args.route)

    if args.json:
        for row in enriched:
            print(
                json.dumps({
                    "index": row.index,
                    "spawned_at": row.spawned_at,
                    "passenger_id": row.passenger_id,
                    "route_id": row.route_id,
                    "depot_id": row.depot_id,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "destination_lat": row.destination_lat,
                    "destination_lon": row.destination_lon,
                    "status": row.status,
                    "route_position_m": row.route_position_m,
                    "travel_distance_km": row.travel_distance_km,
                    "start_address": row.start_address,
                    "stop_address": row.stop_address,
                    "trip_summary": f"{row.start_address} → {row.stop_address} | {row.travel_distance_km:.2f}",
                })
            )
        return

    # Table output - Passenger Manifest
    print(f"\n{'='*160}")
    print(f"PASSENGER MANIFEST - {len(enriched)} passengers")
    if args.route:
        print(f"Route: {args.route} (ordered by distance from route start)")
    else:
        print(f"Hint: pass --route to compute and order by distance from route start")
    print(f"{'='*160}")
    print(f"{'#':<4} {'Spawned':<10} {'Status':<8} {'Pos(m)':>8} {'Passenger ID':<22} {'Route':<8} {'Depot':<10} {'Trip (Start → Stop | km)':<75}")
    print("-" * 160)

    def fmt_time(s: Optional[str]) -> str:
        if not s:
            return "-"
        try:
            dt = datetime.fromisoformat(s.replace('Z','+00:00'))
            return dt.strftime('%H:%M:%S')
        except Exception:
            return s[:19]

    for row in enriched:
        pos_m = int(round(row.route_position_m or 0.0))
        km = row.travel_distance_km or 0.0
        trip = f"{row.start_address} → {row.stop_address} | {km:.2f}"
        print(
            f"{row.index:<4} "
            f"{fmt_time(row.spawned_at):<10} "
            f"{(row.status or '-'):<8} "
            f"{pos_m:>8} "
            f"{(row.passenger_id or '-'):<22} "
            f"{(row.route_id or '-'):<8} "
            f"{(row.depot_id or '-'):<10} "
            f"{trip:<75}"
        )


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        sys.exit(0)
