#!/usr/bin/env python3
"""
route_topology.py
-----------------
Robust route reconstruction for MultiLineString GeoJSON.
Finds true termini and builds a continuous ordered path
suitable for Navigator.
"""

from __future__ import annotations
import json, math
from collections import defaultdict, deque
from typing import List, Tuple, Dict

Coord = Tuple[float, float]

# --- Helpers ------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Return distance in meters between two lat/lon points."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlmb/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))


def _round_pt(pt: Coord, ndigits=6) -> Coord:
    lon, lat = pt
    return (round(float(lon), ndigits), round(float(lat), ndigits))


def _load_segments(path: str, ndigits=6) -> List[List[Coord]]:
    """Extract all LineString/MultiLineString coords from a GeoJSON file."""
    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    segments: List[List[Coord]] = []
    for feat in gj.get("features", []):
        geom = feat.get("geometry", {})
        if geom.get("type") == "LineString":
            coords = [_round_pt(tuple(c), ndigits) for c in geom["coordinates"]]
            if len(coords) >= 2:
                segments.append(coords)
        elif geom.get("type") == "MultiLineString":
            for seg in geom["coordinates"]:
                coords = [_round_pt(tuple(c), ndigits) for c in seg]
                if len(coords) >= 2:
                    segments.append(coords)
    return segments


# --- Graph construction -------------------------------------------------

def _build_graph(segments: List[List[Coord]]) -> Dict[Coord, set]:
    """Build adjacency graph of points."""
    adj = defaultdict(set)
    for seg in segments:
        for i in range(len(seg) - 1):
            p1, p2 = seg[i], seg[i+1]
            adj[p1].add(p2)
            adj[p2].add(p1)
    return adj


def _bfs_longest_path(adj: Dict[Coord, set]) -> List[Coord]:
    """Return longest path in the graph (graph diameter) via 2 BFS runs."""
    # First BFS: arbitrary start
    start = next(iter(adj))
    def bfs(src):
        dist, parent = {src:0}, {src:None}
        q = deque([src])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in dist:
                    dist[v] = dist[u] + 1
                    parent[v] = u
                    q.append(v)
        farthest = max(dist, key=dist.get)
        return farthest, dist, parent

    far1, _, _ = bfs(start)
    far2, dist, parent = bfs(far1)

    # Reconstruct path
    path = []
    u = far2
    while u is not None:
        path.append(u)
        u = parent[u]
    path.reverse()
    return path


# --- Public API ---------------------------------------------------------

def find_termini(route_file: str) -> Tuple[Coord, Coord]:
    """Return the two termini (endpoints) of the route."""
    segments = _load_segments(route_file)
    adj = _build_graph(segments)
    path = _bfs_longest_path(adj)
    return path[0], path[-1]


def build_ordered_path(route_file: str, direction: str = "outbound") -> List[Coord]:
    """
    Build a continuous ordered route polyline from GeoJSON.
    Direction can be 'outbound' (default) or 'inbound' (reversed).
    """
    segments = _load_segments(route_file)
    adj = _build_graph(segments)
    path = _bfs_longest_path(adj)   # longest chain of connected nodes
    if direction.lower() == "inbound":
        path.reverse()
    return [(lon, lat) for lon, lat in path]

def build_ordered_path_from_featurecollection(fc: dict, direction: str = "outbound") -> List[Coord]:
    """
    Build an ordered path from an in-memory GeoJSON FeatureCollection.
    Mirrors build_ordered_path, but operates on data instead of a file.
    """
    segments: List[List[Coord]] = []
    for feat in fc.get("features", []):
        geom = feat.get("geometry", {})
        t = geom.get("type")
        if t == "LineString":
            coords = [_round_pt(tuple(c)) for c in geom.get("coordinates", [])]
            if len(coords) >= 2:
                segments.append(coords)
        elif t == "MultiLineString":
            for seg in geom.get("coordinates", []):
                coords = [_round_pt(tuple(c)) for c in seg]
                if len(coords) >= 2:
                    segments.append(coords)

    adj = _build_graph(segments)
    path = _bfs_longest_path(adj)
    if direction.lower() == "inbound":
        path.reverse()
    return [(lon, lat) for lon, lat in path]
