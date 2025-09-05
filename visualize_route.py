#!/usr/bin/env python3
"""
visualize_route.py
"""
import folium
from folium import plugins
from shapely import wkb
from world.fleet_manager.manager import FleetManager
from world.fleet_manager.models.route import Route


def main():
    route_name = input("Enter route short_name (e.g. 1, 1A): ").strip()

    fm = FleetManager()
    route = fm.db.query(Route).filter_by(short_name=route_name).first()
    if not route:
        print(f"Route '{route_name}' not found"); return

    coords_list = [list(wkb.loads(bytes(rs.shape.geom.data)).coords) for rs in route.shapes]
    fm.close()
    if not coords_list:
        print(f"No coordinates for route '{route_name}'"); return

    center = [coords_list[0][0][1], coords_list[0][0][0]]
    m = folium.Map(location=center, zoom_start=13, tiles=None)

    # Base layers (mutually exclusive): OSM default + "No basemap" option
    folium.TileLayer(
        "OpenStreetMap", name="Basemap", overlay=False, control=True, show=True
    ).add_to(m)
    folium.TileLayer(
        tiles=None, name="No basemap", attr="No background", overlay=False, control=True, show=False
    ).add_to(m)

    # Overlays: lines
    fg_lines = folium.FeatureGroup(name="Route lines", show=True)
    for coords in coords_list:
        latlon = [(lat, lon) for lon, lat in coords]  # flip for folium
        folium.PolyLine(latlon, weight=3, opacity=0.8).add_to(fg_lines)
    fg_lines.add_to(m)

    # Overlays: points
    fg_points = folium.FeatureGroup(name="Route points", show=False)
    for idx, coords in enumerate(coords_list):
        for j, (lon, lat) in enumerate(coords):
            folium.CircleMarker(
                location=(lat, lon), radius=3, color="red",
                fill=True, fill_color="red", fill_opacity=0.9,
                popup=f"Point {idx}-{j}<br>Lat={lat:.6f}<br>Lon={lon:.6f}"
            ).add_to(fg_points)
    fg_points.add_to(m)

    # Controls
    folium.LayerControl(collapsed=False).add_to(m)
    plugins.MousePosition().add_to(m)

    out = f"route_{route_name}_map.html"
    m.save(out)
    print(f"Map written to {out}")


if __name__ == "__main__":
    main()
