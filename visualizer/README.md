# Passenger Visualizer

A tiny FastAPI app that helps you test RouteSpawner and DepotSpawner visually.

What it does:
- Aggregates route geometry from GeospatialService and passengers from Strapi
- Serves a Leaflet map to display passengers along a selected route and in a time window

## Prereqs
- Strapi running locally at <http://localhost:1337> with `active-passengers` content type
- GeospatialService running locally at <http://localhost:8001> (endpoint `/spatial/route-geometry/{route_id}`)
- Python 3.10+

## Install (Windows PowerShell)
```powershell
# From repo root
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r visualizer/requirements.txt
```

## Run
```powershell
# Optional env vars (defaults shown)
$env:STRAPI_URL = "http://localhost:1337"
$env:GEO_URL = "http://localhost:8001"
# If your Strapi requires auth for reads, set a token (role must have read on active-passengers)
# $env:STRAPI_TOKEN = "<your_strapi_token>"

uvicorn visualizer.app:app --host 0.0.0.0 --port 8010 --reload
```

## Try it
Open in a browser:
```
http://localhost:8010/route-viewer?route_id=<ROUTE_DOCUMENT_ID>&start=2025-10-29T09:00:00Z&end=2025-10-29T10:00:00Z
```
- route_id: Strapi documentId for the route (e.g., `gg3pv3z19hhm117v9xth5ezq`)
- start/end: ISO8601 timestamps filter `spawned_at`

## How passengers are fetched
The API calls Strapi:
```
GET /api/active-passengers?filters[route_id][$eq]={route_id}&filters[status][$eq]=WAITING&filters[spawned_at][$gte]={start}&filters[spawned_at][$lte]={end}&pagination[pageSize]=1000
```
And GeospatialService:
```
GET /spatial/route-geometry/{route_id}
```
Returned JSON:
```json
{
  "route": {"type":"LineString","coordinates":[[lat,lon], ...]},
  "passengers": [{"passenger_id":"...","latitude":13.1,"longitude":-59.6,"spawned_at":"..."}],
  "meta": {"count": 42}
}
```

## Notes
- This app is for diagnostics; it doesn’t modify data.
- If you see CORS or auth issues, prefer using this proxy over direct browser calls to Strapi/GeospatialService.
- You can adapt it to show depot-based passengers at `/api/depot/{depot_id}/data` and future overlays.
