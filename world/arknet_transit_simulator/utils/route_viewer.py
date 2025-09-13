#!/usr/bin/env python3
"""
Route Visualizer CLI
--------------------
Interactive tool to visualize routes from database via API.
- Plots route polyline(s) + points in separate overlays
- Hover + cursor to inspect points
- Checkbox to hide/show basemap
- Cleans up generated HTML (lang, title, charset, viewport)

Usage:
    python route_viewer.py
"""

import sys
import os
import json
import re
import folium
from folium.plugins import MousePosition
import requests
from shapely.wkb import loads as wkb_loads


def fetch_data(api_base, endpoint):
    """Fetch data from API endpoint"""
    url = f"{api_base}/{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch {endpoint}: {e}")
        return []


def wkb_to_coords(wkb_geom):
    """Convert geometry (WKB, hex, or GeoJSON) to coordinate list"""
    from shapely.geometry import shape as shapely_shape
    import json
    try:
        # If it's a dict, treat as GeoJSON
        if isinstance(wkb_geom, dict):
            geom = shapely_shape(wkb_geom)
        # If it's already bytes, use directly
        elif isinstance(wkb_geom, bytes):
            geom = wkb_loads(wkb_geom)
        # If it's a string, try JSON (GeoJSON) first, then hex/WKB
        elif isinstance(wkb_geom, str):
            try:
                geom = shapely_shape(json.loads(wkb_geom))
            except Exception:
                try:
                    geom = wkb_loads(bytes.fromhex(wkb_geom))
                except Exception:
                    return []
        else:
            return []
        if geom.geom_type == 'LineString':
            return list(geom.coords)  # [(lon, lat), ...]
        elif geom.geom_type == 'MultiLineString':
            coords = []
            for line in geom.geoms:
                coords.extend(list(line.coords))
            return coords
    except Exception as e:
        print(f"[WARNING] Error converting geometry: {e}")
    return []


def visualize_route(api_base, route_number):
    """Visualize a specific route from the API"""

    # Fetch route data
    print(f"[INFO] Fetching route {route_number} from API...")
    routes = fetch_data(api_base, "routes")
    route_shapes = fetch_data(api_base, "route_shapes")
    shapes = fetch_data(api_base, "shapes")

    # Find the specific route
    target_route = None
    for route in routes:
        if route.get('short_name', '').upper() == route_number.upper():
            target_route = route
            break

    if not target_route:
        print(f"[ERROR] Route '{route_number}' not found.")
        print("[INFO] Available routes:")
        for route in routes:
            print(f"  - {route.get('short_name', 'Unknown')}")
        return

    print(f"[INFO] Found route: {target_route.get('short_name')} - {target_route.get('long_name', '')}")

    # Get associated shapes
    route_id = target_route['route_id']
    print(f"[DEBUG] Route ID: {route_id}")
    print(f"[DEBUG] Available route_shapes: {len(route_shapes)} entries")
    shape_ids = [rs['shape_id'] for rs in route_shapes if rs['route_id'] == route_id]
    print(f"[DEBUG] Found shape_ids for route: {shape_ids}")

    # Collect route segments from shapes
    segments = []
    for shape_id in shape_ids:
        # Fetch individual shape details
        print(f"[DEBUG] Fetching shape {shape_id}...")
        shape_detail = fetch_data(api_base, f"shapes/{shape_id}")
        print(f"[DEBUG] Shape detail response: {shape_detail}")
        if shape_detail and 'geom' in shape_detail:
            geom_field = shape_detail['geom']
            print(f"[DEBUG] shape_id={shape_id} geom_field type={type(geom_field)} value={repr(geom_field)[:200]}")
            # Try to decode if base64 or hex
            coords = wkb_to_coords(geom_field)
            print(f"[DEBUG] Extracted {len(coords)} coordinates from shape {shape_id}")
            if coords:
                segments.append(coords)
        else:
            print(f"[DEBUG] No geom field found in shape {shape_id}")

    if not segments:
        print("[ERROR] No coordinates found for this route. (Check if the shape geometry is present and in a supported format: GeoJSON, WKB, or hex string.)")
        return

    # Flatten all coords to compute map center
    all_coords = [pt for seg in segments for pt in seg]
    avg_lat = sum(lat for lon, lat in all_coords) / len(all_coords)
    avg_lon = sum(lon for lon, lat in all_coords) / len(all_coords)

    print(f"[INFO] Map center: {avg_lat:.6f}, {avg_lon:.6f}")

    # Map with no default tiles
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=14, tiles=None)

    # Base layers
    folium.TileLayer("OpenStreetMap", name="Basemap", control=True).add_to(m)
    folium.TileLayer(tiles="", name="No basemap", attr="No basemap", control=True).add_to(m)

    # Overlay groups
    fg_line = folium.FeatureGroup(name="Route", show=True)
    fg_pts = folium.FeatureGroup(name="All stops", show=True)

    # Draw each segment separately
    for seg in segments:
        # Polyline (swap order → Folium wants (lat, lon))
        folium.PolyLine(
            [(lat, lon) for (lon, lat) in seg],
            color="blue", weight=3, opacity=0.7
        ).add_to(fg_line)

        # Points
        for i, (lon, lat) in enumerate(seg):
            folium.CircleMarker(
                location=[lat, lon],
                radius=3, color="red",
                fill=True, fill_opacity=0.8,
                popup=f"Lat={lat:.6f}<br>Lon={lon:.6f}"
            ).add_to(fg_pts)

    fg_line.add_to(m)
    fg_pts.add_to(m)

    # Mouse tracker
    MousePosition(
        position="bottomright",
        separator=" | ",
        prefix="Coordinates:",
        lat_formatter="function(num) {return L.Util.formatNum(num, 6);}",
        lng_formatter="function(num) {return L.Util.formatNum(num, 6);}",
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # Save map
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"route_{route_number}.html")
    m.save(out_path)

    # Clean HTML
    clean_html(out_path, title=f"Route {route_number}")

    print(f"[INFO] Map saved to: {out_path}")
    print("[INFO] Open it in your browser to interact.")


def clean_html(path: str, title: str = "Route Map") -> None:
    """Post-process the HTML to fix common validator warnings."""
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # Ensure <html lang="en">
    if not re.search(r'<html[^>]*\blang\s*=', html, flags=re.IGNORECASE):
        html = re.sub(r'<html([^>]*)>', r'<html\1 lang="en">', html, count=1, flags=re.IGNORECASE)

    # Ensure <title>
    if not re.search(r'<title>.*?</title>', html, flags=re.IGNORECASE | re.DOTALL):
        html = re.sub(r'<head[^>]*>', f'<head>\n<title>{title}</title>', html, count=1, flags=re.IGNORECASE)

    # Normalize charset
    html = re.sub(
        r'<meta[^>]*http-equiv\s*=\s*["\']content-type["\'][^>]*>',
        '<meta charset="utf-8">',
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'<meta\s+charset\s*=\s*["\'][^"\']*["\']\s*/?>',
        '<meta charset="utf-8">',
        html,
        flags=re.IGNORECASE,
    )

    # Fix viewport (remove user-scalable & maximum-scale)
    def _fix_viewport(tag_html: str) -> str:
        m = re.search(r'content\s*=\s*["\'](.*?)["\']', tag_html, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return tag_html
        content = m.group(1)
        parts = [p.strip() for p in re.split(r'\s*,\s*', content.replace('\n', ' '))]
        keep = [p for p in parts if not re.match(r'(?i)(user\s*-\s*scalable|max\s*-\s*scale)\s*=', p)]
        new_content = ', '.join(keep)
        start, end = m.span(1)
        return tag_html[:start] + new_content + tag_html[end:]

    html = re.sub(
        r'<meta\s+[^>]*name\s*=\s*["\']viewport["\'][^>]*\/?>',
        lambda m: _fix_viewport(m.group(0)),
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    print("Route Visualizer CLI")
    print("====================")
    print("Interactive tool to visualize routes from database via API.")
    print("Type 'help' or '?' at any prompt for assistance.")
    print("Press Ctrl+C at any time to exit gracefully.\n")

    try:
        # Get API base URL
        while True:
            api_base = input("Enter API base URL (default: http://localhost:8000/api/v1): ").strip()
            if not api_base:
                api_base = "http://localhost:8000/api/v1"
            if api_base.lower() in ('help', '?'):
                print("\nHelp: Enter the base URL of your API server.")
                print("Example: http://localhost:8000/api/v1")
                continue
            break

        # Get route number
        while True:
            route_number = input("Enter route number to visualize (e.g., 1, 1A): ").strip()
            if route_number.lower() in ('help', '?'):
                print("\nHelp: Enter the route number you want to visualize.")
                print("Examples: 1, 1A, 2, 3B, etc.")
                continue
            if route_number:
                break

        # Visualize the route
        visualize_route(api_base, route_number)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user (Ctrl+C). Exiting gracefully.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
