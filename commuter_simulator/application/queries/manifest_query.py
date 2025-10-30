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


async def enrich_manifest_rows(rows: List[Dict[str, Any]], route_id: Optional[str]) -> List[ManifestRow]:
    """Enrich raw Strapi rows with computed positions, addresses, and distances.
    Returns list of ManifestRow ordered by route_position_m.
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

        # Reverse geocode with bounded concurrency
        addr_cache: Dict[Tuple[float, float], str] = {}
        sem = asyncio.Semaphore(int(os.getenv("GEOCODE_CONCURRENCY", "5")))

        async def addr_pair(r: Dict[str, Any]) -> Tuple[str, str]:
            async with sem:
                a = await reverse_geocode(client, geo_url, r.get("latitude"), r.get("longitude"), addr_cache)
            async with sem:
                b = await reverse_geocode(client, geo_url, r.get("destination_lat"), r.get("destination_lon"), addr_cache)
            return a, b

        addr_pairs = await asyncio.gather(*(addr_pair(r) for r in rows))

        enriched: List[ManifestRow] = []
        for i, r in enumerate(rows):
            start_addr, stop_addr = addr_pairs[i]
            enriched.append(ManifestRow(
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
            ))

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
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = await client.get(f"{strapi_url}/api/active-passengers", params=params, headers=headers)
    r.raise_for_status()
    data = r.json()
    items = data.get("data", [])
    # normalize attrs
    def parse_attrs(item: Dict[str, Any]) -> Dict[str, Any]:
        attrs = item.get("attributes", {})
        if attrs:
            return {"id": item.get("id"), **attrs}
        return item
    return [parse_attrs(it) for it in items]
