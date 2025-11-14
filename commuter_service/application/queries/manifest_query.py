"""
Manifest Builder
----------------

Reusable helpers to produce a passenger manifest with:
- Ordering by distance from route start
- Reverse geocoded start/stop addresses
- Travel distance (km)

Designed for reuse by CLI tools and future UI/API without reinventing logic.
"""
from __future__ import annotations

import os
import math
import asyncio
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import httpx


@dataclass
class ManifestRow:
    index: int
    spawned_at: Optional[str]
    passenger_id: Optional[str]
    route_id: Optional[str]
    depot_id: Optional[str]

    latitude: Optional[float]
    longitude: Optional[float]
    destination_lat: Optional[float]
    destination_lon: Optional[float]

    status: Optional[str]

    # Computed fields
    route_position_m: float
    travel_distance_km: float
    start_address: str
    stop_address: str

    def to_json(self) -> Dict[str, Any]:
        d = asdict(self)
        # Also provide a human readable trip summary for convenience
        d["trip_summary"] = f"{self.start_address} → {self.stop_address} | {self.travel_distance_km:.2f}"
        return d


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def compute_route_positions(route_coords_latlon: List[List[float]], points: List[Tuple[Optional[float], Optional[float]]]) -> List[float]:
    """Compute cumulative distance from start to nearest route vertex for each point.
    route_coords_latlon is [[lat, lon], ...]
    points is list of (lat, lon)
    """
    if not route_coords_latlon:
        return [0.0 for _ in points]

    cum = [0.0]
    for i in range(1, len(route_coords_latlon)):
        lat1, lon1 = route_coords_latlon[i-1]
        lat2, lon2 = route_coords_latlon[i]
        cum.append(cum[-1] + haversine_m(lat1, lon1, lat2, lon2))

    res: List[float] = []
    for plat, plon in points:
        if plat is None or plon is None:
            res.append(0.0)
            continue
        min_d = float("inf")
        nearest_idx = 0
        for i, (lat, lon) in enumerate(route_coords_latlon):
            d = haversine_m(plat, plon, lat, lon)
            if d < min_d:
                min_d = d
                nearest_idx = i
        res.append(cum[nearest_idx])
    return res


async def fetch_route_coords(geo_url: str, route_id: Optional[str], client: httpx.AsyncClient) -> List[List[float]]:
    if not route_id:
        return []
    try:
        r = await client.get(f"{geo_url}/spatial/route-geometry/{route_id}")
        if r.status_code == 200:
            data = r.json()
            coords_lnglat = data.get("coordinates", [])
            # convert to lat,lon
            return [[c[1], c[0]] for c in coords_lnglat if isinstance(c, list) and len(c) >= 2]
    except Exception:
        pass
    return []


async def reverse_geocode(client: httpx.AsyncClient, geo_url: str, lat: Optional[float], lon: Optional[float], cache: Dict[Tuple[float, float], str]) -> str:
    if lat is None or lon is None:
        return "-"
    key = (round(float(lat), 5), round(float(lon), 5))
    if key in cache:
        return cache[key]
    try:
        resp = await client.get(f"{geo_url}/geocode/reverse", params={"lat": key[0], "lon": key[1]})
        if resp.status_code == 200:
            addr = resp.json().get("address") or f"Lat {key[0]:.5f}, Lon {key[1]:.5f}"
            cache[key] = addr
            return addr
    except Exception:
        pass
    return "-"


async def enrich_manifest_rows(
    rows: List[Dict[str, Any]], 
    route_id: Optional[str],
    progress_callback = None
) -> List[ManifestRow]:
    """Enrich raw Strapi rows with computed positions, addresses, and distances.
    Returns list of ManifestRow ordered by route_position_m.
    
    Args:
        rows: Raw passenger data from Strapi
        route_id: Route ID for position calculation
        progress_callback: Optional async callback(enriched_row, index, total) for streaming
    """
    geo_url = os.getenv("GEO_URL", "http://localhost:6000").rstrip("/")

    async with httpx.AsyncClient(timeout=20.0) as client:
        route_coords = await fetch_route_coords(geo_url, route_id, client)

        # Compute positions
        points = [(r.get("latitude"), r.get("longitude")) for r in rows]
        positions = compute_route_positions(route_coords, points) if route_coords else [0.0 for _ in rows]

        # Compute travel distances
        travel_km: List[float] = []
        for r in rows:
            lat, lon = r.get("latitude"), r.get("longitude")
            dlat, dlon = r.get("destination_lat"), r.get("destination_lon")
            if None not in (lat, lon, dlat, dlon):
                travel_km.append(haversine_m(lat, lon, dlat, dlon)/1000.0)
            else:
                travel_km.append(0.0)

        # Reverse geocode with bounded concurrency and streaming
        addr_cache: Dict[Tuple[float, float], str] = {}
        sem = asyncio.Semaphore(int(os.getenv("GEOCODE_CONCURRENCY", "20")))
        
        enriched: List[ManifestRow] = []
        total = len(rows)
        completed = 0

        async def process_passenger(i: int, r: Dict[str, Any]):
            """Process single passenger with geocoding"""
            async with sem:
                start_addr = await reverse_geocode(client, geo_url, r.get("latitude"), r.get("longitude"), addr_cache)
            async with sem:
                stop_addr = await reverse_geocode(client, geo_url, r.get("destination_lat"), r.get("destination_lon"), addr_cache)
            
            row = ManifestRow(
                index=i+1,
                spawned_at=r.get("spawned_at"),
                passenger_id=r.get("passenger_id"),
                route_id=r.get("route_id"),
                depot_id=r.get("depot_id"),
                latitude=r.get("latitude"),
                longitude=r.get("longitude"),
                destination_lat=r.get("destination_lat"),
                destination_lon=r.get("destination_lon"),
                status=r.get("status"),
                route_position_m=float(positions[i] or 0.0),
                travel_distance_km=float(travel_km[i] or 0.0),
                start_address=start_addr or "-",
                stop_address=stop_addr or "-",
            )
            
            return row

        # Process all passengers concurrently and emit progress as each completes
        tasks = [process_passenger(i, r) for i, r in enumerate(rows)]
        for coro in asyncio.as_completed(tasks):
            row = await coro
            enriched.append(row)
            completed += 1
            
            # Stream progress callback - fires as each passenger completes
            if progress_callback:
                await progress_callback(row, completed, total)

        enriched.sort(key=lambda x: x.route_position_m)
        # Re-assign indices according to sorted order
        for idx, row in enumerate(enriched, 1):
            row.index = idx
        return enriched


async def fetch_passengers(
    client: httpx.AsyncClient,
    strapi_url: str,
    token: Optional[str],
    params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Fetch ALL passengers from Strapi, paginating through all pages"""
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    all_items = []
    page = 1
    max_pages = 100  # Safety limit to prevent infinite loops
    
    # Parse attributes helper - handle both wrapped and unwrapped formats
    def parse_attrs(item: Dict[str, Any]) -> Dict[str, Any]:
        # Check if data is wrapped in 'attributes' (Strapi page 1 format)
        if "attributes" in item:
            attrs = item.get("attributes", {})
            return {"id": item.get("id"), "documentId": item.get("documentId"), **attrs}
        # Otherwise data is already flat (Strapi page 2+ format)
        return item
    
    while page <= max_pages:
        # Add pagination to params
        page_params = {**params, "pagination[page]": page}
        
        print(f"[DEBUG] Fetching page {page}...")
        r = await client.get(f"{strapi_url}/api/active-passengers", params=page_params, headers=headers)
        r.raise_for_status()
        data = r.json()
        items = data.get("data", [])
        
        print(f"[DEBUG] Page {page}: got {len(items)} items")
        
        if not items:
            print(f"[DEBUG] No items on page {page}, stopping")
            break
        
        all_items.extend([parse_attrs(it) for it in items])
        
        # Check if there are more pages
        meta = data.get("meta", {})
        pagination = meta.get("pagination", {})
        total_pages = pagination.get("pageCount", 1)
        current_page = pagination.get("page", page)
        
        print(f"[DEBUG] Pagination meta: page={current_page}, total_pages={total_pages}, total_items={len(all_items)}")
        
        if page >= total_pages:
            print(f"[DEBUG] Reached last page ({page} >= {total_pages})")
            break
        
        page += 1
    
    print(f"[DEBUG] Returning {len(all_items)} total items")
    return all_items

