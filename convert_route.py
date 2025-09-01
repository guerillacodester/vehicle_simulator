#!/usr/bin/env python3
"""
Route Topology
--------------
Standalone module to convert unordered route segments (from QGIS GeoJSON)
into an ordered continuous polyline.

Exposes:
    build_route_topology(raw_segments) -> List[(lon, lat)]
"""

from typing import List, Tuple, Dict, Set
import math


# ---------------- Utilities ----------------

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometers between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(
        dlambda / 2
    ) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


# ---------------- Graph building ----------------

def build_graph(segments: List[List[Tuple[float, float]]]):
    """
    Build adjacency graph from route segments.
    Returns adjacency dict and set of unique nodes.
    """
    graph: Dict[Tuple[float, float], Set[Tuple[float, float]]] = {}
    nodes: Set[Tuple[float, float]] = set()

    for seg in segments:
        for i in range(len(seg) - 1):
            a = tuple(seg[i])
            b = tuple(seg[i + 1])
            nodes.update([a, b])
            graph.setdefault(a, set()).add(b)
            graph.setdefault(b, set()).add(a)

    return graph, nodes


def largest_component(nodes: Set[Tuple[float, float]], graph: Dict):
    """Return largest connected component from graph."""
    seen, components = set(), []

    for node in nodes:
        if node in seen:
            continue
        stack, comp = [node], []
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.append(cur)
            for neigh in graph.get(cur, []):
                if neigh not in seen:
                    stack.append(neigh)
        components.append(comp)

    components.sort(key=len, reverse=True)
    return set(components[0]) if components else set()


# ---------------- Longest path ----------------

def bfs_longest_path(graph: Dict, start) -> Tuple[Tuple[float, float], float, List]:
    """BFS to find farthest node from start."""
    from collections import deque

    visited = {start: (0.0, [start])}
    q = deque([start])
    farthest, maxdist, maxpath = start, 0.0, [start]

    while q:
        cur = q.popleft()
        dist, path = visited[cur]
        for neigh in graph.get(cur, []):
            if neigh not in visited:
                seglen = haversine(cur[1], cur[0], neigh[1], neigh[0])
                ndist = dist + seglen
                visited[neigh] = (ndist, path + [neigh])
                if ndist > maxdist:
                    farthest, maxdist, maxpath = neigh, ndist, path + [neigh]
                q.append(neigh)

    return farthest, maxdist, maxpath


def longest_path(graph: Dict, comp_nodes: Set[Tuple[float, float]]):
    """Find longest simple path (route diameter)."""
    if not comp_nodes:
        return []

    # 1st BFS
    start = next(iter(comp_nodes))
    farthest, _, _ = bfs_longest_path(graph, start)
    # 2nd BFS
    other, _, path = bfs_longest_path(graph, farthest)
    return path


# ---------------- Public API ----------------

def build_route_topology(raw_segments: List[List[Tuple[float, float]]]) -> List[Tuple[float, float]]:
    """
    Entry point: take raw route segments from GeoJSON,
    return an ordered polyline (list of (lon, lat) tuples).
    """
    graph, nodes = build_graph(raw_segments)
    comp_nodes = largest_component(nodes, graph)
    path = longest_path(graph, comp_nodes)
    return path


# ---------------- CLI ----------------

if __name__ == "__main__":
    import argparse, json, sys, os

    parser = argparse.ArgumentParser(
        description="Convert unordered QGIS/GeoJSON route into ordered polyline"
    )
    parser.add_argument("geojson", help="Input route GeoJSON file")
    args = parser.parse_args()

    if not os.path.exists(args.geojson):
        print(f"[ERROR] File not found: {args.geojson}")
        sys.exit(1)

    with open(args.geojson, "r", encoding="utf-8") as f:
        data = json.load(f)

    coords = []
    if data["type"] == "FeatureCollection":
        for feat in data["features"]:
            geom = feat.get("geometry", {})
            if geom.get("type") == "LineString":
                coords.append(geom["coordinates"])
            elif geom.get("type") == "MultiLineString":
                coords.extend(geom["coordinates"])

    route = build_route_topology(coords)
    print(f"[INFO] Processed {len(route)} points")
    for lon, lat in route[:10]:
        print(f"  Lon={lon:.6f}, Lat={lat:.6f}")
    if len(route) > 10:
        print("  ...")
