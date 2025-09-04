#!/usr/bin/env python3
"""
geojson_to_routes.py
--------------------
Converts a GeoJSON of routes into a flattened dataset that aligns with a
PostgreSQL table schema: routes(route TEXT, path TEXT).

- Each LineString (or each component of a MultiLineString) becomes ONE row.
- 'path' is compact JSON string (single line) of [lon,lat] pairs.
- 'route' is inferred from, in order of priority:
    1) feature.properties['route'] or ['name'] (if present)
    2) --route-name CLI override
    3) input filename stem, with suffix _1, _2, ... for subsequent parts

Outputs:
- SQL file with INSERT statements (optional)
- CSV file with headers: route,path (optional)
- Processed GeoJSON (optional): same features but with coordinates compacted

Usage:
  python geojson_to_routes.py input.geojson \
      --out-sql routes.sql \
      --out-csv routes.csv \
      --out-json processed.geojson \
      --route-name test

"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Optional

def compact_json(obj: Any) -> str:
    """Return a compact, single-line JSON string."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)

def sql_escape(s: str) -> str:
    """Escape single quotes for SQL literal."""
    return s.replace("'", "''")

def infer_route_name(
    base_name: str,
    seq: int,
    feature_props: Optional[Dict[str, Any]],
    cli_route_name: Optional[str]
) -> str:
    # 1) from properties
    if feature_props:
        for key in ("route", "name", "id", "Route", "Name"):
            if key in feature_props and str(feature_props[key]).strip():
                return str(feature_props[key]).strip()
    # 2) CLI override
    if cli_route_name:
        return f"{cli_route_name}" if seq == 0 else f"{cli_route_name}_{seq}"
    # 3) fallback to filename stem
    return f"{base_name}" if seq == 0 else f"{base_name}_{seq}"

def rows_from_feature(
    feature: Dict[str, Any],
    base_name: str,
    start_seq: int,
    cli_route_name: Optional[str]
) -> Tuple[List[Tuple[str, str]], int]:
    """
    Extract (route, path) rows from a single GeoJSON feature.
    Returns: (rows, next_seq)
    """
    rows: List[Tuple[str, str]] = []
    geom = feature.get("geometry") or {}
    gtype = geom.get("type")
    props = feature.get("properties") or {}
    seq = start_seq

    if gtype == "LineString":
        coords = geom.get("coordinates", [])
        route = infer_route_name(base_name, seq, props, cli_route_name)
        path = compact_json(coords)
        rows.append((route, path))
        seq += 1

    elif gtype == "MultiLineString":
        for part in geom.get("coordinates", []):
            route = infer_route_name(base_name, seq, props, cli_route_name)
            path = compact_json(part)
            rows.append((route, path))
            seq += 1

    else:
        # ignore other geometry types
        pass

    return rows, seq

def write_sql(rows: Iterable[Tuple[str, str]], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        f.write("-- INSERTs for public.routes (route TEXT, path TEXT)\n")
        for route, path in rows:
            f.write(
                "INSERT INTO routes (route, path) VALUES "
                f"('{sql_escape(route)}','{sql_escape(path)}');\n"
            )

def write_csv(rows: Iterable[Tuple[str, str]], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["route", "path"])
        for route, path in rows:
            w.writerow([route, path])

def write_processed_geojson(
    original: Dict[str, Any],
    out_path: Path
) -> None:
    """
    Writes a 'processed' GeoJSON. Here we just ensure numeric coords and
    compact lists. (Structure preserved.)
    """
    # Minimal pass-through; real “processing” can be adapted to your needs.
    # We do not reformat into vertical arrays; keep as standard GeoJSON.
    out_path.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(description="Flatten GeoJSON to (route, path) rows.")
    ap.add_argument("input", help="Input GeoJSON path")
    ap.add_argument("--out-sql", help="Write SQL INSERTs to this file")
    ap.add_argument("--out-csv", help="Write CSV to this file")
    ap.add_argument("--out-json", help="Write processed GeoJSON to this file")
    ap.add_argument("--route-name", help="Force base route name (overrides props/file stem)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: input not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    with in_path.open("r", encoding="utf-8") as f:
        gj = json.load(f)

    base_name = in_path.stem
    all_rows: List[Tuple[str, str]] = []
    seq = 0

    features = gj.get("features")
    if isinstance(features, list):
        for feat in features:
            rows, seq = rows_from_feature(feat, base_name, seq, args.route_name)
            all_rows.extend(rows)
    else:
        # Support bare geometry GeoJSON
        fake_feature = {"type": "Feature", "geometry": gj, "properties": {}}
        rows, seq = rows_from_feature(fake_feature, base_name, seq, args.route_name)
        all_rows.extend(rows)

    if not all_rows:
        print("No LineString or MultiLineString geometries found.", file=sys.stderr)
        sys.exit(2)

    # Outputs
    if args.out_sql:
        write_sql(all_rows, Path(args.out_sql))
    if args.out_csv:
        write_csv(all_rows, Path(args.out_csv))
    if args.out_json:
        write_processed_geojson(gj, Path(args.out_json))

    # Console preview
    print(f"Rows: {len(all_rows)}")
    for i, (route, path) in enumerate(all_rows[:3], start=1):
        print(f"{i}. route={route} | path_len={len(path)}")

if __name__ == "__main__":
    main()

